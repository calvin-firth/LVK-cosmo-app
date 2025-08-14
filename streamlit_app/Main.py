import streamlit as st
import time
import redis
from streamlit_autorefresh import st_autorefresh

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
st.session_state["events"]=st.session_state["redis"].smembers("events:all")

st.session_state["status"]["Connected"] = ((time.time() - int(st.session_state["status"]["Last Check"])) < 60)

pg = st.navigation([st.Page("Home.py", title="Home"),st.Page("Notices test.py")])
pg.run()

if(st.session_state["status"]["Connected"]):
    st_autorefresh(interval=10000, key="autorefresh")