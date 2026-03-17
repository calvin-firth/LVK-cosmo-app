import streamlit as st
import time
import redis
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timezone,timedelta
from streamlit_javascript import st_javascript
import pandas as pd
import numpy as np
from io import StringIO
import io

def is_utf8(data):
    try:
        data.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False

if"queued" not in st.session_state:
    st.session_state["queued"] = None
if "status" not in st.session_state:
    st.session_state["status"] = None
if "redis" not in st.session_state:
    st.session_state["redis"] = redis.Redis.from_url("rediss://default_ro:AuEiAAIgcDIuQ6LLfLtc9kt4C1IgcAba7p2sLT-NK6bZjTFpNoICyQ@merry-grackle-57634.upstash.io:6379",decode_responses=True,retry_on_timeout=True)
if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default_ro:AuEiAAIgcDIuQ6LLfLtc9kt4C1IgcAba7p2sLT-NK6bZjTFpNoICyQ@merry-grackle-57634.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)
if "events" not in st.session_state:
    st.session_state["events"] = None

st.session_state["status"] = st.session_state["redis"].hgetall("Status")
st.session_state["status"] = dict(sorted(st.session_state["status"].items()))
try:
    st.session_state["queued"] = st.session_state["redis"].lrange("queue:waiting", 0, -1)
except:
    st.session_state["queued"] = "queue too large to read"
st.session_state["events"]=sorted(st.session_state["redis"].smembers("events:all"),reverse=True)

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
                mapper = {'50% area': '{0:,.2f}',
                          '90% area': '{0:,.2f}',
                          'dl': '{0:,.2f}'
                          }
                df = pd.DataFrame.from_dict(decoded_data)
                for col in ['50% area', '90% area', 'dl']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                st.session_state["Event table"] = pd.DataFrame(np.concatenate([st.session_state["Event table"].values,df[['50% area', '90% area', 'dl']].values]),columns=st.session_state["Event table"].columns)
    st.session_state["Event table"].reset_index().rename(columns={'index': "Event"})
    st.session_state["Event table"]["is_checked"] = np.zeros(len(st.session_state["Event table"]["50% Sky-localization area"]), dtype=bool)

    posteriors = []
    retracted = 0
    num_post = 0

st.session_state["status"]["Connected"] = ((time.time() - float(st.session_state["status"]["Last Check"])) < 60)

tz_offset = st_javascript("new Date().getTimezoneOffset();")

if tz_offset is not None:
    utc_str = st.session_state["status"]["Last Check"]
    utc_dt=datetime.fromtimestamp(int(float((utc_str))))
    # Convert using offset
    local_dt = utc_dt.astimezone(
        timezone.utc
    ) - timedelta(minutes=tz_offset)  # JS offset is minutes behind UTC

    st.session_state["status"]["Last Check"]=local_dt.strftime("%Y-%m-%d %H:%M:%S")


pg = st.navigation([st.Page("Home.py", title="Home"),st.Page("Notices test.py",title="Recent events"),st.Page("All events.py",title="All events"),st.Page("Combined posterior.py",title="Combined posterior")])
pg.run()

if(st.session_state["status"]["Connected"]):
    st_autorefresh(interval=10000, key="autorefresh")