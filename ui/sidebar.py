"""
sidebar.py
All input widgets. Returns one immutable SimInputs object so the rest of the
app never touches widgets directly.
"""
from dataclasses import dataclass

import streamlit as st

from aero.constants import MS_TO_KMH
from aero.forces import FlowCondition
from aero.wing import WingConfig


@dataclass(frozen=True)
class SimInputs:
    wing: WingConfig
    flow: FlowCondition
    camber: float        # fraction of chord (airflow tab section)
    camber_pos: float    # x/c of maximum camber
    thickness: float     # fraction of chord


def render_sidebar() -> SimInputs:
    with st.sidebar:
        st.header("Wing geometry")
        chord_m = st.slider("Chord (m)", 0.10, 0.60, 0.35, 0.01)
        span_m = st.slider("Span (m)", 0.40, 1.50, 0.95, 0.01)
        aoa_deg = st.slider("Angle of attack (deg)", -5.0, 25.0, 8.0, 0.5)

        st.header("Flow conditions")
        speed_kmh = st.slider("Airspeed (km/h)", 50, 350, 288, 1)
        air_density = st.slider("Air density (kg/m^3)", 0.90, 1.30, 1.225, 0.005)

        with st.expander("Model parameters (advanced)"):
            cl0 = st.slider("CL at 0 deg (camber)", 0.0, 2.0, 1.0, 0.05)
            alpha_stall_deg = st.slider("Stall angle (deg)", 8.0, 25.0, 14.0, 0.5)
            cd0 = st.slider("Profile drag CD0", 0.005, 0.100, 0.020, 0.005)
            oswald_e = st.slider("Span efficiency e", 0.50, 1.00, 0.90, 0.01)
            endplate_factor = st.slider("Endplate factor", 1.00, 1.50, 1.15, 0.01)

        with st.expander("Airfoil section (airflow tab)"):
            camber_pct = st.slider("Camber (% chord)", 0.0, 8.0, 4.0, 0.5)
            camber_pos = st.slider("Camber position (x/c)", 0.2, 0.7, 0.4, 0.05)
            thickness_pct = st.slider("Thickness (% chord)", 6.0, 20.0, 12.0, 1.0)

    wing = WingConfig(
        name="Custom wing",
        chord_m=chord_m,
        span_m=span_m,
        aoa_deg=aoa_deg,
        cl0=cl0,
        alpha_stall_deg=alpha_stall_deg,
        cd0=cd0,
        oswald_e=oswald_e,
        endplate_factor=endplate_factor,
    )
    flow = FlowCondition(velocity_ms=speed_kmh / MS_TO_KMH, air_density=air_density)
    return SimInputs(wing, flow, camber_pct / 100.0, camber_pos, thickness_pct / 100.0)
