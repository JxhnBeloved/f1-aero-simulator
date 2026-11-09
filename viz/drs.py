"""
drs.py (figures)
Closed-versus-open DRS plots.
"""
from __future__ import annotations

from matplotlib.figure import Figure

from .theme import PALETTE

CLOSED = PALETTE["blue"]
OPEN = PALETTE["orange"]


def plot_drs_aoa(closed: dict, opened: dict, set_angle_deg: float,
                 stall_closed_deg: float, stall_open_deg: float) -> Figure:
    """Downforce, drag and L/D versus the driver-set wing angle, DRS closed and open."""
    panels = [("downforce_n", "Downforce (N)"), ("drag_n", "Drag (N)"),
              ("l_over_d", "Efficiency L/D")]
    fig = Figure(figsize=(11, 3.8), dpi=110, constrained_layout=True)
    axes = fig.subplots(1, 3)

    x = closed["aoa_deg"]
    idx = int(abs(x - set_angle_deg).argmin())
    for ax, (key, label) in zip(axes, panels):
        ax.plot(x, closed[key], color=CLOSED, linewidth=2, label="DRS closed")
        ax.plot(x, opened[key], color=OPEN, linewidth=2, label="DRS open")
        for series, color in ((closed, CLOSED), (opened, OPEN)):
            ax.plot(x[idx], series[key][idx], "o", color="white",
                    markeredgecolor=color, markeredgewidth=2, markersize=8, zorder=5)
        ax.axvline(stall_closed_deg, color=CLOSED, linestyle=":", linewidth=1)
        ax.axvline(stall_open_deg, color=OPEN, linestyle=":", linewidth=1)
        ax.set_xlabel("Wing angle set by driver / team (deg)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.5)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, fontsize=8)
    fig.suptitle("Angle sweep (dot = current setting, dotted line = stall angle)",
                 fontsize=9)
    return fig


def plot_drs_speed(closed: dict, opened: dict, current_kmh: float) -> Figure:
    """Downforce and drag versus airspeed, DRS closed and open."""
    panels = [("downforce_n", "Downforce (N)"), ("drag_n", "Drag (N)")]
    fig = Figure(figsize=(10, 3.8), dpi=110, constrained_layout=True)
    axes = fig.subplots(1, 2)

    for ax, (key, label) in zip(axes, panels):
        ax.plot(closed["velocity_kmh"], closed[key], color=CLOSED, linewidth=2,
                label="DRS closed")
        ax.plot(opened["velocity_kmh"], opened[key], color=OPEN, linewidth=2,
                label="DRS open")
        ax.fill_between(closed["velocity_kmh"], opened[key], closed[key],
                        color=OPEN, alpha=0.12)
        ax.axvline(current_kmh, color=PALETTE["muted"], linestyle="--", linewidth=1)
        ax.set_xlabel("Airspeed (km/h)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.5)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=2, fontsize=8)
    fig.suptitle("Speed sweep (dashed line = current airspeed, shaded = what DRS changes)",
                 fontsize=9)
    return fig
