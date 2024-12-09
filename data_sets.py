import pandas as pd
import streamlit as st


@st.cache_data
def orbit_active_data():
    df = pd.read_csv("orb_active.csv", encoding="latin-1", low_memory=False)
    return df


@st.cache_data
def orbit_inactive_data():
    df = pd.read_csv("orb_inactive.csv", encoding="latin-1", low_memory=False)
    return df


@st.cache_data
def get_in_plan(df):
    in_plan = df.loc[df["Plan"] == "In Plan"].copy()
    in_plan = in_plan["Plan"].count()
    return in_plan


@st.cache_data
def get_out_of_plan(df):
    out_plan = df.loc[df["Plan"] == "Out Of Plan"].copy()
    out_plan = out_plan["Plan"].count()
    return out_plan
