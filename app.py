"""
app.py
Streamlit front end for the F1 Aerodynamics Simulator (Stage 6).
Run with:  streamlit run app.py

All physics lives in the aero/ package; this file only collects inputs and
displays results.
"""
import numpy as np
import streamlit as st

from aero.airfoil import airfoil_nodes
from aero.constants import MS_TO_KMH
from aero.forces import FlowCondition, compute_performance
from aero.panel_method import solve_panels
from aero.sweeps import sweep_aoa
from aero.wing import WingConfig
from viz.flow_field import plot_cp_distribution, plot_flow_field
from viz.plots import plot_aoa_sweep

st.set_page_config(page_title="F1 Aero Simulator", layout="wide")

st.title("F1 Aerodynamics Simulator")
st.caption(
    "Simplified analytical model (lifting-line theory + empirical stall) plus a "
    "2D potential-flow panel method. Engineering estimates, not CFD results."
)

# ---------------------------------------------------------------- controls
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
result = compute_performance(wing, flow)

tab_dashboard, tab_airflow = st.tabs(["Performance dashboard", "Airflow (computed)"])

# --------------------------------------------------------------- dashboard
with tab_dashboard:
    if result.is_stalled:
        st.warning(
            f"Angle of attack ({aoa_deg:.1f} deg) is beyond the stall angle "
            f"({alpha_stall_deg:.1f} deg): the flow has separated, so downforce "
            "drops and drag rises."
        )

    row1 = st.columns(4)
    row1[0].metric("Downforce", f"{result.downforce_n:,.0f} N")
    row1[1].metric("Drag", f"{result.drag_n:,.0f} N")
    row1[2].metric("Efficiency (L/D)", f"{result.l_over_d:.2f}")
    row1[3].metric("Dynamic pressure", f"{result.dynamic_pressure_pa:,.0f} Pa")

    row2 = st.columns(4)
    row2[0].metric("CL (downforce coeff.)", f"{result.cl:.3f}")
    row2[1].metric("CD (drag coeff.)", f"{result.cd:.3f}")
    row2[2].metric("of which induced CDi", f"{result.cd_induced:.3f}")
    row2[3].metric("Downforce (mass equiv.)", f"{result.downforce_kgf:,.0f} kgf")

    st.caption(
        f"Planform area {wing.area_m2:.3f} m^2, aspect ratio {wing.aspect_ratio:.2f}, "
        f"airspeed {flow.velocity_ms:.1f} m/s."
    )

    st.subheader("Performance across angle of attack")
    sweep = sweep_aoa(wing, flow, np.linspace(-5.0, 25.0, 121))
    st.pyplot(plot_aoa_sweep(sweep, aoa_deg, alpha_stall_deg))

    with st.expander("Model assumptions and limitations"):
        st.markdown(
            """
- Incompressible, steady, attached flow below stall.
- Finite-wing lift slope from Prandtl lifting-line theory.
- Induced drag CDi = CL^2 / (pi e AR).
- Stall is an **empirical shape**, not computed from boundary-layer physics.
- No Reynolds-number effects, ground effect or multi-element interaction yet.
- Treat results as trends for comparing configurations, not as absolute predictions.
"""
        )

# ----------------------------------------------------------------- airflow
with tab_airflow:
    st.info(
        "**What you are looking at:** a real numerical solution of 2D, inviscid, "
        "incompressible potential flow around the airfoil section (a Hess-Smith panel "
        "method). Streamlines and pressures are computed, not hand-drawn. It is **not "
        "CFD**: there is no boundary layer, so no stall, no friction drag and no "
        "tip vortices."
    )

    panel = solve_panels(
        airfoil_nodes(camber_pct / 100.0, camber_pos, thickness_pct / 100.0),
        aoa_deg,
    )

    if aoa_deg > alpha_stall_deg:
        st.warning(
            "Beyond the stall angle the real flow separates from the suction surface. "
            "This inviscid solution cannot show that, so the picture below is no "
            "longer physically realistic."
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("2D section CL (panel method)", f"{panel.cl:.3f}")
    m2.metric("2D section CD (panel method)",
              "~ 0" if abs(panel.cd) < 0.005 else f"{panel.cd:.3f}")
    m3.metric("Peak suction Cp", f"{panel.cp.min():.2f}")
    m4.metric("Whole-wing CL (analytical model)", f"{result.cl:.3f}")
    st.caption(
        "The panel CL is for an infinite 2D section; the analytical CL is for your finite "
        "wing, so they are not expected to match. Panel CD is ~0 because inviscid flow "
        "has no drag (d'Alembert's paradox)."
    )

    show_streamlines = st.checkbox("Show streamlines", value=True)
    st.pyplot(plot_flow_field(panel, show_streamlines=show_streamlines))
    st.pyplot(plot_cp_distribution(panel))
