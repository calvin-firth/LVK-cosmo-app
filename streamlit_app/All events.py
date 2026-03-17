import streamlit as st
import redis
import pandas as pd
from io import StringIO
import io
import numpy as np
import matplotlib.pyplot as plt

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
    st.session_state["Event table"].columns = ["50% Sky-localization area", "90% Sky-localization area", "Luminosity distance (Mpc)"]
    for event in st.session_state["events"]:
        if event not in st.session_state["Event table"].index:
            decoded_data = {}
            binary_data = {}
            json_data = {}

            raw_data = st.session_state["redis2"].hgetall(event)
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
                st.session_state["Event table"].loc[event] = decoded_data.values()

    st.session_state["Event table"]["is_checked"] = np.zeros(len(st.session_state["Event table"]["50% Sky-localization area"]), dtype=bool)
    st.session_state["Event table"].reset_index().rename(columns={'index':"Event"})
    posteriors = []
    retracted = 0
    num_post = 0

st.write("Use the dropdown menu to view the analysis results for any previously analyzed event (currently only includes LVK's O4 operating run)")
selected_event = st.selectbox("", ["Choose an event..."] + st.session_state["events"],label_visibility="collapsed")

#list_df = pd.DataFrame(st.session_state["events"], columns=["Event"])
#list_df["is_checked"] = np.ones(len(st.session_state["events"]),dtype=bool)

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
    st.session_state["Event table"],
    column_config=column_config,
    disabled=["command", "rating"],  # Optional: disable other columns
)

if any(edited_df["is_checked"]):
    events_to_choose = np.array(st.session_state["events"])[np.where(edited_df["is_checked"])[0]]

    posteriors = []
    retracted = 0
    num_post = 0

    for event in events_to_choose:
        if event == 'S250221eb'  or event =='S230830b' or event == 'S230715bw'or event == 'S241126dm' or event=='S250221gb'or event=='S250108ha' or event == 'S241104a' or event =='S240624cd'or event=='S240423br'or event=='S240420aw' or event=='S231112ag'  or event=='S230808i'or event=='S230712a' or event=='S230708bi'or event=='S230622ba':#or event=='S241110br':
            retracted+=1
            continue #or event == 'S241126dm'
        if (st.session_state["redis2"].exists(event)):
            decoded_data = {}
            binary_data = {}
            json_data = {}

            raw_data = st.session_state["redis2"].hgetall(event)
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

            if json_data:
                # st.subheader("Structured Data")
                posteriors.append(json_data['posterior'].to_numpy())
                num_post += 1

    posteriors = np.stack(posteriors)
    posteriors = np.transpose(posteriors, (2, 0, 1))

    comb_log = np.sum(np.log(posteriors[1]),axis=0)
    comb_log -= np.max(comb_log)
    combined_post = np.exp(comb_log)
    area = np.trapezoid(combined_post, posteriors[0,0])
    combined_post = combined_post / area

    log_likelihood = np.sum(np.log(posteriors[2]),axis=0)
    like_max = np.max(log_likelihood)
    log_likelihood -= np.max(log_likelihood)
    empty_post = np.exp(log_likelihood)
    area_empty = np.trapezoid(empty_post, posteriors[0,0])
    empty_post = empty_post/area_empty

    fig,ax = plt.subplots()
    ax.scatter(posteriors[0,0],combined_post,s=5)
    ax.plot(posteriors[0,0],empty_post,color='orange')
    ax.set_xlabel("$H_0 (km/s/Mpc)$",fontsize=16)
    ax.set_ylabel("$p(H_0)$",fontsize=16)
    ax.set_title("Combined posterior (" + str(num_post) + " events)",fontsize=20)
    ax.tick_params(labelsize=14)
    ax.legend(["Glade+ K-band, eps1","Empty catalog"],fontsize=14)

    st.pyplot(fig)