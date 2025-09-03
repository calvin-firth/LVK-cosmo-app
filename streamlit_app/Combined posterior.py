import numpy as np
import streamlit as st
import redis
import pandas as pd

if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)

if "Event table" not in st.session_state:
    tbl_df = pd.dataframe(columns=["50% area", "90% area", "dl", ])
    for event in st.session_state["events"]:
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

            # Show plain UTF-8 decoded fields
            if decoded_data:
                # st.subheader("Event Info")

                for col in ['50% area', '90% area', 'dl']:
                    tbl_df.loc[event][col] = decoded_data

st.write(tbl_df)