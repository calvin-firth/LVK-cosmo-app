

import streamlit as st
import pandas as pd
from unicodedata import category

if "catalog" not in st.session_state:
  st.session_state["catalog"] = None
if "cat_loaded" not in st.session_state:
  st.session_state["cat_loaded"] = False

import matplotlib.pyplot as plt
import streamlit.components.v1 as components
import mpld3
import icarogw
import healpy as hp
import numpy as np
from galaxycat import analyze_event
import copy

posterior_dict = {}

catalog_choice = st.selectbox("Select catalog",["Glade+","Upglade"])
eps = st.selectbox("Eps setting", ["eps-1","eps-0"])
load = st.button("Load catalog")
if load:
  if catalog_choice=="Glade+":
    cat = icarogw.catalog.icarogw_catalog(r'/mnt/c/Users/Calvi/2025 IREU Sapienza/icaro_gladep.hdf5', 'K-band', eps)
  elif catalog_choice=="Upglade":
    cat = icarogw.catalog.icarogw_catalog(r'/mnt/c/Users/Calvi/2025 IREU Sapienza/icaro_upglade.hdf5', 'g-band-gr', eps)
  st.write("Loading catalog...")
  cat.load_from_hdf5_file()
  outcat = copy.deepcopy(cat)
  outcat.make_me_empty()
  empty_cat = outcat
  st.write("Catalog loaded.")
  st.session_state["catalog"] = cat
  st.session_state["empty cat"] = empty_cat
  st.session_state["cat_loaded"] = True

if st.session_state["cat_loaded"]:
  st.session_state["catalog"].moc_mthr_map.plot()

  skymap_file = st.file_uploader("Upload your skymap here")

  test = analyze_event(skymap_file.name,skymap_file,st.session_state["catalog"], st.session_state["empty cat"])