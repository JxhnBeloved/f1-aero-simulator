"""
comparison.py
Figures that overlay several wing configurations on the same axes.
"""
from __future__ import annotations

from matplotlib.figure import Figure

COLORS = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]


def plot_comparison_aoa(wings, sweeps) -> Figure:
    """Downforce, drag and L/D versus angle of attack for several wings.
    A dot marks each wing's current operating angle."""
    panels = [
        ("downforce_n", "Downforce (N)"),
        ("drag_n", "Drag (N)"),
        ("l_over_d", "Efficiency L/D"),
    ]
    fig = Figure(figsize=(11, 3.8), dpi=110, constrained_layout=True)
    axes = fig.subplots(1, 3)

    for ax, (key, label) in zip(axes, panels):
        for wing, sweep, color in zip(wings, sweeps, COLORS):
            x, y = sweep["aoa_deg"], sweep[key]
            ax.plot(x, y, color=color, linewidth=2, label=wing.name)
            idx = int(abs(x - wing.aoa_deg).argmin())
            ax.plot(x[idx], y[idx], "o", color=color, markeredgecolor="black",
                    markersize=8, zorder=5)
            ax.axvline(wing.alpha_stall_deg, color=color, linestyle=":", linewidth=1)
        ax.set_xlabel("Angle of attack (deg)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3, fontsize=8)
    fig.suptitle("Angle sweep (dot = current setting, dotted line = stall angle)",
                 fontsize=9)
    return fig


def plot_comparison_velocity(wings, sweeps, current_kmh: float) -> Figure:
    """Downforce and drag versus airspeed, each wing at its own set angle."""
    panels = [("downforce_n", "Downforce (N)"), ("drag_n", "Drag (N)")]
    fig = Figure(figsize=(10, 3.8), dpi=110, constrained_layout=True)
    axes = fig.subplots(1, 2)

    for ax, (key, label) in zip(axes, panels):
        for wing, sweep, color in zip(wings, sweeps, COLORS):
            ax.plot(sweep["velocity_kmh"], sweep[key], color=color, linewidth=2,
                    label=f"{wing.name} ({wing.aoa_deg:.1f} deg)")
        ax.axvline(current_kmh, color="gray", linestyle="--", linewidth=1)
        ax.set_xlabel("Airspeed (km/h)")
        ax.set_ylabel(label)
        ax.grid(True, alpha=0.3)

    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncol=3, fontsize=8)
    fig.suptitle("Speed sweep (dashed line = current airspeed)", fontsize=9)
    return fig
