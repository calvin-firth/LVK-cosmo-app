import streamlit as st
import time

st.title("Live galaxy catalog $H_0$ inference (still under development)")
st.write("Code status: ")
st.write(st.session_state["status"])
st.write("This website displays low-latency cosmology results from gravitational wave events. Separate from this streamlit user-interface, there is a script that runs continuously, and searches for alerts from the Ligo-Virgo-Kagra (LVK) collaboration. When an alert is received, the script uses publicly available skymap data (which can be found at [gracedb.ligo.org](https://gracedb.ligo.org/)) to perform an analysis that results in a posterior probability distribution for the Hubble constant, $H_0$. This home page shows the current status of the separate background analysis. The live analysis results can be seen on the page titled \"Recent events\", and all previously done analysis can be seen on \"All events\".")
st.write("Developed by Calvin Firth (University of Minnesota/Sapienza Universita di Roma)")
