"""
flow_field.py
Figures for the 2D panel-method solution: pressure-coefficient map with
streamlines, and the Cp distribution along the chord.

Display convention: the solver works on an UPRIGHT airfoil. An F1 wing is
inverted, and flow physics is mirror-symmetric, so we simply flip the y axis
when drawing. Downforce then points down, toward the track.
"""
from __future__ import annotations

import numpy as np
from matplotlib.figure import Figure

from aero.panel_method import PanelSolution, inside_mask, velocity_field

CP_MIN_SHOWN = -3.0   # colour scale floor; stronger suction is clipped to this colour


def plot_flow_field(sol: PanelSolution, show_streamlines: bool = True,
                    nx: int = 150, ny: int = 90) -> Figure:
    """Pressure coefficient map (like a CFD contour plot) with streamlines."""
    xs = np.linspace(-0.7, 1.7, nx)
    ys = np.linspace(-0.6, 0.6, ny)
    X, Y = np.meshgrid(xs, ys)

    u, v = velocity_field(sol, X, Y)
    body = inside_mask(sol, X, Y, margin=-0.004)
    # Values inside the body are meaningless; the filled airfoil is drawn on top
    # of them, and the streamlines are masked so they stop at the surface.
    cp_field = np.nan_to_num(1.0 - (u**2 + v**2), nan=1.0, posinf=1.0, neginf=CP_MIN_SHOWN)
    u = np.ma.masked_where(body, u)
    v = np.ma.masked_where(body, v)

    fig = Figure(figsize=(10, 4.6), dpi=110, constrained_layout=True)
    ax = fig.subplots()

    levels = np.linspace(CP_MIN_SHOWN, 1.0, 41)
    filled = ax.contourf(X, Y, np.clip(cp_field, CP_MIN_SHOWN, 1.0),
                         levels=levels, cmap="RdYlBu_r", extend="min")
    if show_streamlines:
        ax.streamplot(xs, ys, u, v, density=1.6, color="black",
                      linewidth=0.5, arrowsize=0.7)

    ax.fill(sol.nodes[:, 0], sol.nodes[:, 1], color="#222222", zorder=5)
    ax.set_aspect("equal")
    ax.set_xlim(xs[0], xs[-1])
    ax.set_ylim(ys[-1], ys[0])          # flipped: inverted (downforce) wing
    ax.set_xlabel("x / chord")
    ax.set_ylabel("y / chord (flipped: wing inverted)")
    ax.set_title(f"Computed 2D potential flow, alpha = {sol.alpha_deg:.1f} deg "
                 "(inviscid panel method, not CFD)", fontsize=10)

    cbar = fig.colorbar(filled, ax=ax, shrink=0.85, pad=0.01)
    cbar.set_label("Pressure coefficient Cp")
    ax.annotate("flow", xy=(0.95, 0.5), xytext=(0.80, 0.5),
                xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="->"), fontsize=8, va="center")
    return fig


def plot_cp_distribution(sol: PanelSolution) -> Figure:
    """Cp versus chordwise position (Cp axis inverted, as is conventional)."""
    n = len(sol.cp)
    half = n // 2
    lower = slice(0, half)        # nodes run TE -> lower surface -> LE
    upper = slice(half, n)        # then LE -> upper surface -> TE
    x = sol.centers[:, 0]

    fig = Figure(figsize=(6, 3.6), dpi=110, constrained_layout=True)
    ax = fig.subplots()
    ax.plot(x[upper], sol.cp[upper], color="tab:blue", linewidth=2,
            label="Suction side (faces the track)")
    ax.plot(x[lower], sol.cp[lower], color="tab:red", linewidth=2,
            label="Pressure side (faces the sky)")
    ax.invert_yaxis()
    ax.set_xlabel("x / chord")
    ax.set_ylabel("Cp")
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8)
    ax.set_title("Surface pressure distribution (area between curves = force)",
                 fontsize=9)
    return fig
