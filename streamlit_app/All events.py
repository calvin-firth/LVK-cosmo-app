import streamlit as st
import redis
import pandas as pd
from io import StringIO
import io
import numpy as np

if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default_ro:AuEiAAIgcDIuQ6LLfLtc9kt4C1IgcAba7p2sLT-NK6bZjTFpNoICyQ@merry-grackle-57634.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)

if "Event table" not in st.session_state:
    tbl_json = st.session_state["redis2"].json().get("event_list_metadata",'$')[0]
    tbl_df = pd.read_json(StringIO(tbl_json),dtype=float)
    tbl_df = tbl_df.applymap(
        lambda x: x[0] if isinstance(x, list) else x
    ).apply(pd.to_numeric, errors="ignore")
    st.session_state["Event table"]=tbl_df

tbl=st.session_state["Event table"]
tbl.columns = ["50% Sky-localization area","90% Sky-localization area","Luminosity distance (Mpc)"]
tbl["is_checked"] = np.zeros(len(tbl["50% Sky-localization area"]), dtype=bool)
events_to_choose = []
posteriors = []
retracted=0
num_post=0

st.dataframe(tbl)
st.header("Interactive Data Editor with Checkboxes")

# Configure the 'is_checked' column as a CheckboxColumn
column_config = {
    "is_checked": st.column_config.CheckboxColumn(
        "Select",  # Column header label
        help="Select this row to include in the results",
        default=False,
    )
}

# Display the data editor
edited_df = st.data_editor(
    df,
    column_config=column_config,
    disabled=["command", "rating"],  # Optional: disable other columns
    hide_index=True
)

st.write("Use the dropdown menu to view the analysis results for all previously analyzed events (currently only includes LVK's O4 operating run)")
selected_event = st.selectbox("", ["Choose an event..."] + st.session_state["events"],label_visibility="collapsed")



if selected_event is not "Choose an event...":
    st.header(selected_event)
    decoded_data = {}
    binary_data = {}
    json_data = {}

    raw_data = st.session_state["redis2"].hgetall(selected_event)
    raw_data = dict(sorted(raw_data.items()))

    for k, v in raw_data.items():
        key = k.decode() if isinstance(k, bytes) else k
        try:
            value = v.decode("utf-8")

            # Check if value is valid JSON
            try:
                parsed_json = pd.read_json(StringIO(value))
                json_data[key] = parsed_json
            except:
                decoded_data[key] = [value]

        except UnicodeDecodeError:
            binary_data[key] = v  # Leave binary

    # Show plain UTF-8 decoded fields
    if decoded_data:
        # st.subheader("Event Info")

        mapper = {'50% area': '{0:,.2f}',
                  '90% area': '{0:,.2f}',
                  'dl': '{0:,.2f}'
                  }
        df = pd.DataFrame.from_dict(decoded_data)
        for col in ['50% area', '90% area', 'dl']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        styler = (df).style.hide().format(mapper)
        st.write(styler.to_html(), unsafe_allow_html=True)

    # Show PNGs or warn
    if binary_data:
        keys = ["skymap", "numdensity", "posterior plot"]
        text = ["Skymap", "Number density", "Posterior plot"]
        # st.subheader("Figures")
        for n, key in enumerate(keys):
            try:
                binary = binary_data[key]
                if binary.startswith(b'\x89PNG'):
                    st.write(f"**{text[n]}**")
                    st.image(io.BytesIO(binary))
                else:
                    st.warning(f"Cannot display binary data for key '{key}': unsupported format.")
            except:
                continue

    if json_data:
        # st.subheader("Structured Data")
        st.write("Posterior data")
        st.dataframe(json_data['posterior'], hide_index=True, height=200)