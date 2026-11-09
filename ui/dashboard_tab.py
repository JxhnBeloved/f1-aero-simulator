"""
dashboard_tab.py
Performance dashboard: KPI cards, angle sweep, drag polar and a plain-language reading.
"""
import numpy as np
import streamlit as st

from aero.constants import MS_TO_KMH
from aero.derived import drag_power_kw, induced_drag_share, kw_to_hp
from aero.sweeps import sweep_aoa
from ui.styles import note_box, show_kpi, status_badge
from viz.plots import plot_aoa_sweep, plot_drag_polar


def render_dashboard_tab(inputs, result) -> None:
    wing, flow = inputs.wing, inputs.flow
    kmh = flow.velocity_ms * MS_TO_KMH
    power_kw = drag_power_kw(result.drag_n, flow.velocity_ms)
    share = induced_drag_share(result.cd_induced, result.cd)

    if result.is_stalled:
        st.markdown(
            status_badge(f"STALLED: {wing.aoa_deg:.1f} deg is beyond the "
                         f"{wing.alpha_stall_deg:.1f} deg stall angle", ok=False),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(status_badge("ATTACHED FLOW (below stall angle)", ok=True),
                    unsafe_allow_html=True)

    row1 = st.columns(4)
    show_kpi(row1[0], "Downforce", f"{result.downforce_n:,.0f}", "N",
             f"&asymp; {result.downforce_kgf:,.0f} kgf pressing the car down", "blue")
    show_kpi(row1[1], "Drag", f"{result.drag_n:,.0f}", "N",
             f"absorbs {power_kw:,.0f} kW ({kw_to_hp(power_kw):,.0f} hp) at {kmh:.0f} km/h",
             "red")
    show_kpi(row1[2], "Efficiency (L/D)", f"{result.l_over_d:.2f}", "",
             "newtons of downforce per newton of drag", "green")
    show_kpi(row1[3], "Dynamic pressure", f"{result.dynamic_pressure_pa:,.0f}", "Pa",
             f"{kmh:.0f} km/h, air density {flow.air_density:.3f} kg/m3", "orange")

    row2 = st.columns(4)
    show_kpi(row2[0], "CL (downforce coeff.)", f"{result.cl:.3f}", "", "", "blue")
    show_kpi(row2[1], "CD (total drag coeff.)", f"{result.cd:.3f}", "", "", "red")
    show_kpi(row2[2], "Induced share of drag", f"{share * 100:.0f}", "%",
             "drag paid for making downforce", "gray")
    show_kpi(row2[3], "Wing area", f"{wing.area_m2:.3f}", "m&sup2;",
             f"aspect ratio {wing.aspect_ratio:.2f}", "gray")

    st.subheader("Performance across angle of attack")
    sweep = sweep_aoa(wing, flow, np.linspace(-5.0, 25.0, 121))
    st.pyplot(plot_aoa_sweep(sweep, wing.aoa_deg, wing.alpha_stall_deg))

    left, right = st.columns([2, 3])
    with left:
        st.pyplot(plot_drag_polar(sweep, wing.aoa_deg, wing.alpha_stall_deg))
    with right:
        st.subheader("Reading the result")
        st.markdown(
            note_box(
                f"At <b>{kmh:.0f} km/h</b> this wing pushes the car down with about "
                f"<b>{result.downforce_n:,.0f} N</b> (the weight of {result.downforce_kgf:,.0f} kg) "
                f"and costs <b>{result.drag_n:,.0f} N</b> of drag.<br><br>"
                f"<b>{share * 100:.0f}%</b> of that drag is induced drag, the price of "
                f"making downforce with a finite wing. Raising the angle adds downforce, "
                f"but induced drag grows with CL squared, so each extra degree costs more "
                f"drag than the last.<br><br>"
                "Past the stall angle the flow separates: downforce falls while drag keeps "
                "rising. The stall behaviour here is an empirical approximation, not a "
                "boundary-layer calculation."
            ),
            unsafe_allow_html=True,
        )
