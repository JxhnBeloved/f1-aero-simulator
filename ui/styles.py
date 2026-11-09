"""
styles.py
Visual styling for the Streamlit app: CSS, header, KPI cards and badges.
All colours come from viz/theme.py so Matplotlib figures and HTML match.
"""
import streamlit as st

from viz.theme import PALETTE

_CSS = """<style>
.block-container {padding-top: 2.4rem; max-width: 1450px;}
.app-title {font-size: 2.1rem; font-weight: 800; letter-spacing: 0.5px; line-height: 1.1;}
.app-title span {color: #E10600;}
.app-sub {color: #8B949E; margin: 4px 0 10px 0;}
.chip {display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 0.72rem; font-weight: 600; border: 1px solid #30363D; color: #C9D1D9; margin: 0 6px 6px 0;}
.chip.model {border-color: #58A6FF; color: #58A6FF;}
.chip.computed {border-color: #3FB950; color: #3FB950;}
.chip.warn {border-color: #F0883E; color: #F0883E;}
.kpi {background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 14px 16px; margin-bottom: 12px;}
.kpi-label {font-size: 0.72rem; letter-spacing: 0.08em; color: #8B949E; font-weight: 600; text-transform: uppercase;}
.kpi-value {font-size: 1.9rem; font-weight: 700; line-height: 1.2; color: #E6EDF3;}
.kpi-unit {font-size: 0.95rem; font-weight: 500; color: #8B949E; margin-left: 6px;}
.kpi-sub {font-size: 0.78rem; color: #8B949E; margin-top: 2px;}
.status {display: inline-block; padding: 4px 12px; border-radius: 6px; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 10px;}
.status.ok {background: rgba(63,185,80,0.15); color: #3FB950; border: 1px solid #3FB950;}
.status.bad {background: rgba(225,6,0,0.15); color: #FF6B63; border: 1px solid #E10600;}
.note {background: #161B22; border: 1px solid #30363D; border-radius: 10px; padding: 14px 18px; color: #C9D1D9; font-size: 0.92rem; line-height: 1.55;}
</style>"""

ACCENTS = {
    "blue": PALETTE["blue"],
    "red": PALETTE["red"],
    "green": PALETTE["green"],
    "orange": PALETTE["orange"],
    "gray": PALETTE["muted"],
}


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def render_header() -> None:
    st.markdown(
        '<div class="app-title">F1 <span>AERO</span> SIMULATOR</div>'
        '<div class="app-sub">Wing aerodynamics: forces, airflow and configuration trade-offs</div>'
        '<span class="chip model">ANALYTICAL MODEL: lifting-line + empirical stall</span>'
        '<span class="chip computed">AIRFLOW: computed 2D panel method</span>'
        '<span class="chip warn">NOT CFD</span>',
        unsafe_allow_html=True,
    )


def kpi_card(label: str, value: str, unit: str = "", sub: str = "",
             accent: str = "blue") -> str:
    """HTML for one KPI card (single line: Markdown treats indented HTML as code)."""
    color = ACCENTS.get(accent, ACCENTS["blue"])
    unit_html = f'<span class="kpi-unit">{unit}</span>' if unit else ""
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return (
        f'<div class="kpi" style="border-left: 4px solid {color};">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}{unit_html}</div>'
        f'{sub_html}</div>'
    )


def show_kpi(column, label: str, value: str, unit: str = "", sub: str = "",
             accent: str = "blue") -> None:
    column.markdown(kpi_card(label, value, unit, sub, accent), unsafe_allow_html=True)


def status_badge(text: str, ok: bool) -> str:
    kind = "ok" if ok else "bad"
    return f'<div class="status {kind}">{text}</div>'


def note_box(html: str) -> str:
    return f'<div class="note">{html}</div>'
