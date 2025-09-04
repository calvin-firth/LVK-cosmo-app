import numpy as np
import streamlit as st
import redis
import pandas as pd
from io import StringIO
import os
import matplotlib.pyplot as plt

if "redis2" not in st.session_state:
    st.session_state["redis2"] = redis.Redis.from_url(
        "rediss://default:AWTjAAIjcDE0ODhlMDIxZTEwNDg0Y2NmOTM5YTliZWI4ZTE0OGI5ZHAxMA@internal-sawfly-25827.upstash.io:6379",
        decode_responses=False,retry_on_timeout=True)

if "Event table" not in st.session_state:
    tbl_json = st.session_state["redis2"].json().get("event_list_metadata",'$')[0]
    tbl_df = pd.read_json(StringIO(tbl_json),dtype=float)
    tbl_df = tbl_df.applymap(
        lambda x: x[0] if isinstance(x, list) else x
    ).apply(pd.to_numeric, errors="ignore")
    st.session_state["Event table"]=tbl_df

tbl=st.session_state["Event table"]
events_to_choose = []
posteriors = []
retracted=0
num_post=0

loc_min,loc_max=st.slider("Luminosity Distance (Mpc)", 0, np.int64(np.ceil(np.max(tbl["dl"]))),(0,100))

dl_max = np.inf
dl_min = 0

for event in tbl.loc[(tbl['90% area']<loc_max)*(tbl['90% area']>loc_min)*(tbl['dl']<dl_max)*(tbl['dl']>dl_min)].index:
    events_to_choose.append(event)

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
area = np.trapz(combined_post, posteriors[0,0])
combined_post = combined_post / area

log_likelihood = np.sum(np.log(posteriors[2]),axis=0)
like_max = np.max(log_likelihood)
log_likelihood -= np.max(log_likelihood)
empty_post = np.exp(log_likelihood)
area_empty = np.trapz(empty_post, posteriors[0,0])
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