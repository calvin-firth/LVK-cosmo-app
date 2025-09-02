import streamlit as st
import time
import redis
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timezone,timedelta
from streamlit_javascript import st_javascript

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
    st.session_state["redis"] = redis.Redis.from_url("rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",decode_responses=True,retry_on_timeout=True)
if "events" not in st.session_state:
    st.session_state["events"] = None

st.session_state["status"] = st.session_state["redis"].hgetall("Status")
st.session_state["status"] = dict(sorted(st.session_state["status"].items()))
st.session_state["queued"] = st.session_state["redis"].lrange("queue:waiting", 0, -1)
st.session_state["events"]=sorted(st.session_state["redis"].smembers("events:all"),reverse=True)

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