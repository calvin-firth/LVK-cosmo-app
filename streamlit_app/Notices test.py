import streamlit as st
import json
from Main import is_utf8
import redis
import io
import pandas as pd
from io import StringIO

if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)

st.write("Queued alerts: ")
st.write(st.session_state["queued"])

st.title("Recent events")

for event in st.session_state["redis"].smembers("events:all"):
    if(st.session_state["redis"].exists(event)):
        st.header(event)
        decoded_data = {}
        binary_data = {}
        json_data = {}

        raw_data = st.session_state["redis2"].hgetall(event)
        raw_data = dict(sorted(raw_data.items()))

        # Classify each item
        for k, v in raw_data.items():
            key = k.decode() if isinstance(k, bytes) else k
            try:
                value = v.decode("utf-8")

                # Check if value is valid JSON
                try:
                    parsed_json = pd.read_json(StringIO(value)).style.hide().format('{0:,.2f}')
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
            #st.subheader("Figures")
            for key, binary in binary_data.items():
                if binary.startswith(b'\x89PNG'):
                    st.write(f"**{key}**")
                    st.image(io.BytesIO(binary))
                else:
                    st.warning(f"Cannot display binary data for key '{key}': unsupported format.")

        if json_data:
            #st.subheader("Structured Data")
            st.dataframe(json_data['posterior'])