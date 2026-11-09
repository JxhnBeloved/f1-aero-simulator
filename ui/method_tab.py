"""
method_tab.py
Static explanation of the models, their validation and their limits.
"""
import streamlit as st

from ui.styles import note_box


def render_method_tab() -> None:
    st.subheader("Two models, clearly separated")
    st.markdown(
        """
| | Analytical wing model | 2D panel method |
|---|---|---|
| **Used for** | Forces in newtons, CL, CD, L/D, comparisons | Streamlines and surface pressure |
| **Method** | Lifting-line theory, induced drag, empirical stall | Hess-Smith panels with Kutta condition |
| **Dimension** | Finite 3D wing | 2D airfoil section |
| **Flow physics** | Attached flow, then an empirical stall shape | Inviscid, incompressible potential flow |
| **Status** | Engineering estimate | Computed numerical solution |
"""
    )

    st.subheader("Validation")
    st.markdown(
        """
- Dynamic pressure and force scaling (V squared, linear in density) checked analytically.
- Finite-wing lift slope approaches the thin-airfoil value 2 pi as aspect ratio grows.
- Panel method reproduces the exact pressure distribution on a circular cylinder (max error 0.004).
- NACA 0012 at 5 deg gives CL = 0.60 (thin-airfoil theory: 0.55; thick-section panel results are a little higher).
- Zero drag for a closed body (d'Alembert), Kutta condition satisfied, lift from pressure
  integration agrees with Kutta-Joukowski within 3 percent.
"""
    )

    st.subheader("Limitations")
    st.markdown(
        note_box(
            "<b>Not modelled:</b> boundary layer and separation (so stall is empirical), "
            "Reynolds-number effects, tip vortices and wake, ground effect, multi-element "
            "wings, interaction with wheels and bodywork, compressibility, turbulence.<br><br>"
            "<b>Presets and defaults</b> are illustrative parameter sets, not data from any "
            "real car. Use results to compare trends between configurations, not as absolute "
            "predictions."
        ),
        unsafe_allow_html=True,
    )
