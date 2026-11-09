"""
comparison_tab.py
Streamlit UI for comparison mode. Only presentation code lives here; all
numbers come from the aero/ package.
"""
import numpy as np
import streamlit as st

from aero.configs import PRESETS
from aero.constants import MS_TO_KMH
from aero.forces import compute_performance
from aero.sweeps import sweep_aoa, sweep_velocity
from viz.comparison import plot_comparison_aoa, plot_comparison_velocity


def _wing_controls(column, index, preset):
    """Sliders for one configuration; returns the edited WingConfig."""
    with column:
        st.markdown(f"**Configuration {index + 1}: {preset.name}**")
        chord = st.slider("Chord (m)", 0.10, 0.60, preset.chord_m, 0.01,
                          key=f"cmp{index}_chord")
        span = st.slider("Span (m)", 0.40, 1.50, preset.span_m, 0.01,
                         key=f"cmp{index}_span")
        aoa = st.slider("Angle of attack (deg)", -5.0, 25.0, preset.aoa_deg, 0.5,
                        key=f"cmp{index}_aoa")
        cl0 = st.slider("CL at 0 deg (camber)", 0.0, 2.0, preset.cl0, 0.05,
                        key=f"cmp{index}_cl0")
        stall = st.slider("Stall angle (deg)", 8.0, 25.0, preset.alpha_stall_deg, 0.5,
                          key=f"cmp{index}_stall")
    return preset.with_changes(chord_m=chord, span_m=span, aoa_deg=aoa,
                               cl0=cl0, alpha_stall_deg=stall)


def _markdown_table(names, rows):
    header = "| Metric | " + " | ".join(names) + " |"
    divider = "|---|" + "---|" * len(names)
    body = ["| " + label + " | " + " | ".join(values) + " |" for label, values in rows]
    return "\n".join([header, divider] + body)


def render_comparison_tab(flow):
    st.caption(
        "Compare three wing configurations at the same airspeed and air density "
        "(set in the sidebar). Each configuration has its own angle and geometry. "
        "The presets are illustrative parameter sets, not data from any real car."
    )

    columns = st.columns(3)
    wings = [_wing_controls(col, i, preset)
             for i, (col, preset) in enumerate(zip(columns, PRESETS))]
    results = [compute_performance(w, flow) for w in wings]

    st.subheader(f"Results at {flow.velocity_ms * MS_TO_KMH:.0f} km/h")
    rows = [
        ("Angle of attack (deg)", [f"{r.aoa_deg:.1f}" for r in results]),
        ("Downforce (N)", [f"{r.downforce_n:,.0f}" for r in results]),
        ("Drag (N)", [f"{r.drag_n:,.0f}" for r in results]),
        ("Efficiency L/D", [f"{r.l_over_d:.2f}" for r in results]),
        ("CL", [f"{r.cl:.3f}" for r in results]),
        ("CD", [f"{r.cd:.3f}" for r in results]),
        ("Stalled?", ["YES" if r.is_stalled else "no" for r in results]),
    ]
    st.markdown(_markdown_table([r.name for r in results], rows))

    best_downforce = max(results, key=lambda r: r.downforce_n)
    best_efficiency = max(results, key=lambda r: r.l_over_d)
    lowest_drag = min(results, key=lambda r: r.drag_n)
    st.markdown(
        f"- Most downforce: **{best_downforce.name}** ({best_downforce.downforce_n:,.0f} N)\n"
        f"- Lowest drag: **{lowest_drag.name}** ({lowest_drag.drag_n:,.0f} N)\n"
        f"- Best efficiency (L/D): **{best_efficiency.name}** ({best_efficiency.l_over_d:.2f})"
    )

    st.subheader("Angle of attack sweep")
    angles = np.linspace(-5.0, 25.0, 121)
    aoa_sweeps = [sweep_aoa(w, flow, angles) for w in wings]
    st.pyplot(plot_comparison_aoa(wings, aoa_sweeps))

    st.subheader("Airspeed sweep")
    speeds_ms = np.linspace(50.0, 350.0, 61) / MS_TO_KMH
    speed_sweeps = [sweep_velocity(w, flow.air_density, speeds_ms) for w in wings]
    st.pyplot(plot_comparison_velocity(wings, speed_sweeps,
                                       flow.velocity_ms * MS_TO_KMH))

    with st.expander("How to read this"):
        st.markdown(
            """
- **Downforce and drag both grow with V^2.** Doubling speed quadruples each, so the
  *difference* between wing settings matters more at high speed.
- **More downforce costs drag.** Induced drag grows with CL^2, so a high-downforce setup
  loses top speed on the straights but gains grip in corners.
- **Efficiency (L/D) is not the goal by itself.** A team picks the setting that gives the
  lowest lap time for that circuit, which needs a lap-time model (not included here).
- All numbers come from the simplified analytical model, not CFD.
"""
        )
