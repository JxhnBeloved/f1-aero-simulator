"""
app.py
F1 Aerodynamics Simulator: Streamlit entry point.
Run with:  streamlit run app.py

This file only wires things together. Physics lives in aero/, figures in viz/,
and the interface in ui/.
"""
import streamlit as st

from aero.forces import compute_performance
from ui.airflow_tab import render_airflow_tab
from ui.comparison_tab import render_comparison_tab
from ui.dashboard_tab import render_dashboard_tab
from ui.drs_tab import render_drs_tab
from ui.method_tab import render_method_tab
from ui.sidebar import render_sidebar
from ui.styles import inject_css, render_header
from viz.theme import apply_matplotlib_theme

st.set_page_config(page_title="F1 Aero Simulator", layout="wide")
apply_matplotlib_theme()
inject_css()
render_header()

inputs = render_sidebar()
result = compute_performance(inputs.wing, inputs.flow)

tab_dash, tab_flow, tab_compare, tab_drs, tab_method = st.tabs(
    ["Performance dashboard", "Airflow (computed)", "Configuration comparison",
     "DRS open vs closed", "Method and limits"]
)

with tab_dash:
    render_dashboard_tab(inputs, result)
with tab_flow:
    render_airflow_tab(inputs, result)
with tab_compare:
    render_comparison_tab(inputs.flow)
with tab_drs:
    render_drs_tab(inputs)
with tab_method:
    render_method_tab()
