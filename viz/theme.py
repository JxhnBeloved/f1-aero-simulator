"""
theme.py
One colour palette shared by the Streamlit styling and all Matplotlib figures,
so the whole app looks consistent. Call apply_matplotlib_theme() once at start-up.
"""
from __future__ import annotations

import matplotlib

PALETTE = {
    "bg": "#0E1117",
    "panel": "#161B22",
    "text": "#E6EDF3",
    "muted": "#8B949E",
    "grid": "#30363D",
    "red": "#E10600",
    "blue": "#58A6FF",
    "green": "#3FB950",
    "orange": "#F0883E",
}


def apply_matplotlib_theme() -> None:
    """Dark Matplotlib defaults matching the app theme."""
    p = PALETTE
    matplotlib.rcParams.update({
        "figure.facecolor": p["bg"],
        "figure.edgecolor": p["bg"],
        "savefig.facecolor": p["bg"],
        "axes.facecolor": p["panel"],
        "axes.edgecolor": p["grid"],
        "axes.labelcolor": p["text"],
        "axes.titlecolor": p["text"],
        "text.color": p["text"],
        "xtick.color": p["muted"],
        "ytick.color": p["muted"],
        "grid.color": p["grid"],
        "legend.facecolor": p["panel"],
        "legend.edgecolor": p["grid"],
        "legend.labelcolor": p["text"],
        "font.size": 9,
    })
