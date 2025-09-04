import numpy as np
import streamlit as st
import redis
import pandas as pd
from io import StringIO

if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)

if "Event table" not in st.session_state:
    tbl_json = st.session_state["redis2"].json().get("event_list_metadata",'$')[0]
    tbl_df = pd.read_json(StringIO(tbl_json))

st.write(tbl_df)