"""
airflow_tab.py
Airflow tab: 2D potential-flow panel method around the chosen airfoil section.
"""
import streamlit as st

from aero.airfoil import airfoil_nodes
from aero.panel_method import solve_panels
from ui.styles import note_box, show_kpi
from viz.flow_field import plot_cp_distribution, plot_flow_field


def render_airflow_tab(inputs, result) -> None:
    wing = inputs.wing

    st.markdown(
        note_box(
            "<b>What you are looking at:</b> a real numerical solution of 2D, inviscid, "
            "incompressible potential flow around the airfoil section (a Hess-Smith panel "
            "method). Streamlines and pressures are <b>computed</b>, not hand-drawn. It is "
            "<b>not CFD</b>: there is no boundary layer, so no stall, no friction drag and "
            "no tip vortices."
        ),
        unsafe_allow_html=True,
    )
    st.write("")

    panel = solve_panels(
        airfoil_nodes(inputs.camber, inputs.camber_pos, inputs.thickness),
        wing.aoa_deg,
    )

    if wing.aoa_deg > wing.alpha_stall_deg:
        st.warning(
            "Beyond the stall angle the real flow separates from the suction surface. "
            "This inviscid solution cannot show that, so the picture below is no "
            "longer physically realistic."
        )

    cols = st.columns(4)
    show_kpi(cols[0], "2D section CL (panel)", f"{panel.cl:.3f}", "",
             "infinite-span section", "blue")
    show_kpi(cols[1], "2D section CD (panel)",
             "~ 0" if abs(panel.cd) < 0.005 else f"{panel.cd:.3f}", "",
             "inviscid flow has no drag", "gray")
    show_kpi(cols[2], "Peak suction Cp", f"{panel.cp.min():.2f}", "",
             "lowest pressure on the surface", "red")
    show_kpi(cols[3], "Whole-wing CL (analytical)", f"{result.cl:.3f}", "",
             "finite wing, not expected to match", "green")

    show_streamlines = st.checkbox("Show streamlines", value=True)
    st.pyplot(plot_flow_field(panel, show_streamlines=show_streamlines))
    st.pyplot(plot_cp_distribution(panel))
