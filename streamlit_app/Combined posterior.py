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
    tbl_df = pd.read_json(StringIO(tbl_json),dtype={'50% area':float,'90% area':float,'dl':float})

st.write(tbl_df)

events_to_choose = []
posteriors = []
retracted=0
num_post=0

loc_max = 65
loc_min = 0
dl_max = np.inf
dl_min = 0
min_overdensity = 0

st.write(tbl_df['90% area'].dtype)

for event in tbl_df.loc[(tbl_df['90% area']<loc_max)*(tbl_df['90% area']>loc_min)*(tbl_df['Luminosity Distance']<dl_max)*(tbl_df['Luminosity Distance']>dl_min) * (tbl_df['Max Overdensity']>min_overdensity)].index:
    events_to_choose.append(event)

for event in events_to_choose:
    if event == 'S250221eb'  or event =='S230830b' or event == 'S230715bw'or event == 'S241126dm' or event=='S250221gb'or event=='S250108ha' or event == 'S241104a' or event =='S240624cd'or event=='S240423br'or event=='S240420aw' or event=='S231112ag'  or event=='S230808i'or event=='S230712a' or event=='S230708bi'or event=='S230622ba':#or event=='S241110br':
        retracted+=1
        continue #or event == 'S241126dm'
    if 'H0_posterior.csv' in os.listdir('Analysis plots/Gladep_neffPE10_npar25k_eps1_rs0/'+event) and 'H0_posterior.csv' in os.listdir('Analysis plots/Gladep_neffPE10_npar25k_eps1_rs42/'+event):
        if (st.session_state["redis2"].exists(event)):
            are_events = True
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

            if json_data:
                # st.subheader("Structured Data")
                st.dataframe(json_data['posterior'], hide_index=True, height=200)
                num_post += 1
        #post = pd.read_csv('Analysis plots/Gladep_neffPE10_npar25k_eps1_rs0/'+event+'/H0_posterior.csv')
        #posteriors_dict[event] = post.to_numpy()
        #posteriors.append(post.to_numpy())
        #event_list_rs0.append(event)