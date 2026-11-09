"""
drs_tab.py
Streamlit tab: DRS open versus closed for the wing set in the sidebar.
"""
import numpy as np
import streamlit as st

from aero.constants import MS_TO_KMH
from aero.derived import kw_to_hp
from aero.drs import DRSModel, apply_drs, compare_drs, sweep_drs
from aero.sweeps import sweep_velocity
from ui.styles import note_box, show_kpi
from viz.drs import plot_drs_aoa, plot_drs_speed


def render_drs_tab(inputs) -> None:
    wing, flow = inputs.wing, inputs.flow
    kmh = flow.velocity_ms * MS_TO_KMH

    st.markdown(
        note_box(
            "<b>DRS</b> (Drag Reduction System) opens the rear-wing flap to cut drag on "
            "straights. Here it is modelled simply: opening the flap removes part of the "
            "wing's camber and reduces its effective angle. The two parameters below are "
            "<b>illustrative, not calibrated to any real car</b>, and the model has no "
            "flap-gap flow or wake effects."
        ),
        unsafe_allow_html=True,
    )
    st.write("")

    c1, c2 = st.columns(2)
    with c1:
        frac_pct = st.slider("Camber lift kept when open (%)", 0, 100, 55, 5,
                             key="drs_cl0_frac")
    with c2:
        reduction = st.slider("Effective angle reduction when open (deg)", 0.0, 8.0,
                              2.5, 0.5, key="drs_aoa_reduction")
    model = DRSModel(cl0_fraction=frac_pct / 100.0, aoa_reduction_deg=reduction)

    cmp = compare_drs(wing, flow, model)
    opened_wing = apply_drs(wing, model)

    cols = st.columns(4)
    show_kpi(cols[0], "Downforce, DRS open", f"{cmp.opened.downforce_n:,.0f}", "N",
             f"{cmp.downforce_change_n:+,.0f} N ({cmp.downforce_change_pct:+.0f} %) vs closed "
             f"{cmp.closed.downforce_n:,.0f} N", "blue")
    show_kpi(cols[1], "Drag, DRS open", f"{cmp.opened.drag_n:,.0f}", "N",
             f"{cmp.drag_change_n:+,.0f} N ({cmp.drag_change_pct:+.0f} %) vs closed "
             f"{cmp.closed.drag_n:,.0f} N", "red")
    show_kpi(cols[2], "Efficiency L/D, DRS open", f"{cmp.opened.l_over_d:.2f}", "",
             f"closed: {cmp.closed.l_over_d:.2f}", "green")
    show_kpi(cols[3], "Drag power saved", f"{cmp.drag_power_saved_kw:,.0f}", "kW",
             f"&asymp; {kw_to_hp(cmp.drag_power_saved_kw):,.0f} hp at {kmh:.0f} km/h", "orange")

    rows = [
        ("Effective angle (deg)", f"{wing.aoa_deg:.1f}", f"{opened_wing.aoa_deg:.1f}"),
        ("CL at 0 deg", f"{wing.cl0:.2f}", f"{opened_wing.cl0:.2f}"),
        ("CL", f"{cmp.closed.cl:.3f}", f"{cmp.opened.cl:.3f}"),
        ("CD", f"{cmp.closed.cd:.3f}", f"{cmp.opened.cd:.3f}"),
        ("Downforce (N)", f"{cmp.closed.downforce_n:,.0f}", f"{cmp.opened.downforce_n:,.0f}"),
        ("Drag (N)", f"{cmp.closed.drag_n:,.0f}", f"{cmp.opened.drag_n:,.0f}"),
        ("Efficiency L/D", f"{cmp.closed.l_over_d:.2f}", f"{cmp.opened.l_over_d:.2f}"),
    ]
    table = ["| Metric | DRS closed | DRS open |", "|---|---|---|"]
    table += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    st.markdown("\n".join(table))

    if cmp.drag_change_pct < cmp.downforce_change_pct:
        st.markdown(
            note_box(
                f"Opening DRS cuts drag by <b>{-cmp.drag_change_pct:.0f}%</b> but downforce by "
                f"only <b>{-cmp.downforce_change_pct:.0f}%</b>. Induced drag grows with CL "
                "squared, so a modest loss of lift removes a much larger share of the drag. "
                "That asymmetry is why DRS is worth using on a straight."
            ),
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            note_box("With these parameters the drag saving is not larger than the downforce "
                     "loss, so DRS would not pay off here."),
            unsafe_allow_html=True,
        )

    st.subheader("Angle sweep")
    set_angles = np.linspace(-5.0, 25.0, 121)
    closed_sw, open_sw = sweep_drs(wing, flow, set_angles, model)
    st.pyplot(plot_drs_aoa(closed_sw, open_sw, wing.aoa_deg, wing.alpha_stall_deg,
                           wing.alpha_stall_deg + model.aoa_reduction_deg))

    st.subheader("Airspeed sweep")
    speeds_ms = np.linspace(50.0, 350.0, 61) / MS_TO_KMH
    st.pyplot(plot_drs_speed(sweep_velocity(wing, flow.air_density, speeds_ms),
                             sweep_velocity(opened_wing, flow.air_density, speeds_ms), kmh))
