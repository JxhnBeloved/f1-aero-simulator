"""
plots.py
Matplotlib figures. Plot functions return a Figure and never call plt.show(),
so the same code works in Streamlit, notebooks and scripts.
"""
from __future__ import annotations

from matplotlib.figure import Figure


def plot_aoa_sweep(sweep: dict, current_aoa_deg: float, stall_deg: float) -> Figure:
    """Downforce, drag and L/D versus angle of attack, with the current point marked."""
    panels = [
        ("downforce_n", "Downforce (N)", "tab:blue"),
        ("drag_n", "Drag (N)", "tab:red"),
        ("l_over_d", "Efficiency L/D", "tab:green"),
    ]

    fig = Figure(figsize=(11, 3.2), dpi=110, constrained_layout=True)
    axes = fig.subplots(1, 3)

    x = sweep["aoa_deg"]
    for ax, (key, label, color) in zip(axes, panels):
        y = sweep[key]
        ax.plot(x, y, color=color, linewidth=2)
        ax.axvline(stall_deg, color="gray", linestyle=":", linewidth=1)

        # Mark the current operating point (nearest sweep sample).
        idx = int(abs(x - current_aoa_deg).argmin())
        ax.plot(x[idx], y[idx], "o", color="black", markersize=7, zorder=5)

        ax.set_xlabel("Angle of attack (deg)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

    axes[0].annotate("stall", xy=(stall_deg, axes[0].get_ylim()[0]),
                     xytext=(3, 6), textcoords="offset points",
                     color="gray", fontsize=8)
    return fig
