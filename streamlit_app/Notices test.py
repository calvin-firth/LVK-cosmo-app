import streamlit as st
import json
from Main import is_utf8
import redis
import io
import pandas as pd
from io import StringIO
from datetime import date

if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)

st.write("Queued alerts: ")
st.write(st.session_state["queued"])

st.title("Recent events")

today = date.today()
formatted_date = int(today.strftime("%y%m%d"))
are_events=False

for event in st.session_state["events"]:
    t_event = int(event[1:7])
    if (formatted_date-t_event > 200):
        continue

    if(st.session_state["redis"].exists(event)):
        are_events=True
        st.header(event)
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

        #Show plain UTF-8 decoded fields
        if decoded_data:
            #st.subheader("Event Info")

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
            keys = ["skymap","numdensity","posterior plot"]
            #st.subheader("Figures")
            for key in keys:
                try:
                    binary = binary_data[key]
                    if binary.startswith(b'\x89PNG'):
                        st.write(f"**{key}**")
                        st.image(io.BytesIO(binary))
                    else:
                        st.warning(f"Cannot display binary data for key '{key}': unsupported format.")
                except:
                    continue

        if json_data:
            #st.subheader("Structured Data")
            st.write("Posterior data")
            st.dataframe(json_data['posterior'],hide_index=True,height=200)

if not are_events:
    st.write("No recent events")