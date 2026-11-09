"""
plots.py
Matplotlib figures for the performance dashboard. Plot functions return a
Figure and never call plt.show(), so they work in Streamlit, notebooks and scripts.
"""
from __future__ import annotations

from matplotlib.figure import Figure

from .theme import PALETTE


def plot_aoa_sweep(sweep: dict, current_aoa_deg: float, stall_deg: float) -> Figure:
    """Downforce, drag and L/D versus angle of attack, with the current point marked."""
    panels = [
        ("downforce_n", "Downforce (N)", PALETTE["blue"]),
        ("drag_n", "Drag (N)", PALETTE["red"]),
        ("l_over_d", "Efficiency L/D", PALETTE["green"]),
    ]

    fig = Figure(figsize=(11, 3.2), dpi=110, constrained_layout=True)
    axes = fig.subplots(1, 3)

    x = sweep["aoa_deg"]
    for ax, (key, label, color) in zip(axes, panels):
        y = sweep[key]
        ax.plot(x, y, color=color, linewidth=2)
        ax.axvline(stall_deg, color=PALETTE["muted"], linestyle=":", linewidth=1)

        # Mark the current operating point (nearest sweep sample).
        idx = int(abs(x - current_aoa_deg).argmin())
        ax.plot(x[idx], y[idx], "o", color="white", markeredgecolor=color,
                markeredgewidth=2, markersize=8, zorder=5)

        ax.set_xlabel("Angle of attack (deg)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.5)

    axes[0].annotate("stall", xy=(stall_deg, axes[0].get_ylim()[0]),
                     xytext=(3, 6), textcoords="offset points",
                     color=PALETTE["muted"], fontsize=8)
    return fig


def plot_drag_polar(sweep: dict, current_aoa_deg: float, stall_deg: float) -> Figure:
    """Drag polar: downforce coefficient CL against drag coefficient CD
    (the same kind of plot as the top-left panel of an airfoil polar chart)."""
    x, cl, cd = sweep["aoa_deg"], sweep["cl"], sweep["cd"]

    fig = Figure(figsize=(5.2, 3.8), dpi=110, constrained_layout=True)
    ax = fig.subplots()
    ax.plot(cd, cl, color=PALETTE["orange"], linewidth=2)

    i_now = int(abs(x - current_aoa_deg).argmin())
    i_stall = int(abs(x - stall_deg).argmin())
    ax.plot(cd[i_stall], cl[i_stall], "x", color=PALETTE["muted"], markersize=9,
            markeredgewidth=2, label="stall angle")
    ax.plot(cd[i_now], cl[i_now], "o", color="white", markeredgecolor=PALETTE["orange"],
            markeredgewidth=2, markersize=8, zorder=5, label="current setting")

    ax.set_xlabel("Drag coefficient CD")
    ax.set_ylabel("Downforce coefficient CL")
    ax.set_title("Drag polar", fontsize=10)
    ax.grid(True, alpha=0.5)
    ax.legend(fontsize=8, loc="lower right")
    return fig
