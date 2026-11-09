"""
panel_method.py
2D Hess-Smith panel method: constant-strength source panels plus one constant
vortex strength shared by all panels, with the Kutta condition at the trailing edge.

WHAT THIS IS
    A real solution of the 2D, inviscid, incompressible, irrotational
    (potential) flow around the airfoil. Streamlines and the pressure
    distribution it produces are COMPUTED, not drawn by hand.

WHAT THIS IS NOT
    * No boundary layer, so no skin friction, no flow separation, no stall.
    * Zero drag (d'Alembert's paradox). Real drag is added elsewhere.
    * 2D only: no tip vortices and no induced drag.
    * Not CFD (no Navier-Stokes, no turbulence model).

Conventions
    Free stream has unit speed. Nodes are ordered clockwise starting at the trailing
    edge. For panel i, t_i is the unit tangent along the node order and
    n_i = (-t_y, t_x) is the outward normal.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.path import Path


@dataclass(frozen=True)
class PanelSolution:
    nodes: np.ndarray          # (N+1, 2)
    alpha_deg: float
    centers: np.ndarray        # (N, 2) control points (panel midpoints)
    tangents: np.ndarray       # (N, 2)
    normals: np.ndarray        # (N, 2)
    lengths: np.ndarray        # (N,)
    sources: np.ndarray        # (N,) source strengths
    gamma: float               # vortex strength (counter-clockwise positive)
    vt: np.ndarray             # (N,) tangential velocity at control points
    cp: np.ndarray             # (N,) pressure coefficient at control points
    cl: float                  # lift coefficient from pressure integration
    cd: float                  # drag coefficient from pressure integration (~0)


def _geometry(nodes: np.ndarray):
    d = nodes[1:] - nodes[:-1]
    lengths = np.hypot(d[:, 0], d[:, 1])
    tangents = d / lengths[:, None]
    normals = np.column_stack([-tangents[:, 1], tangents[:, 0]])
    centers = 0.5 * (nodes[1:] + nodes[:-1])
    return centers, tangents, normals, lengths


def _unit_panel_velocity(points, nodes, tangents, normals, lengths):
    """Velocity at `points` (M, 2) from every panel with UNIT strength.

    Returns two (M, N, 2) arrays: source velocity and vortex velocity, each as
    global (x, y) components. The vortex velocity is the source velocity rotated
    by +90 degrees (a counter-clockwise vortex).
    """
    start = nodes[:-1]
    rel = points[:, None, :] - start[None, :, :]                  # (M, N, 2)
    xl = np.einsum("mnk,nk->mn", rel, tangents)                    # local x
    yl = np.einsum("mnk,nk->mn", rel, normals)                     # local y
    L = lengths[None, :]

    r1sq = xl**2 + yl**2
    r2sq = (xl - L) ** 2 + yl**2
    with np.errstate(divide="ignore", invalid="ignore"):
        u = np.log(r1sq / r2sq) / (4.0 * np.pi)
    w = (np.arctan2(yl, xl - L) - np.arctan2(yl, xl)) / (2.0 * np.pi)

    src = u[..., None] * tangents[None] + w[..., None] * normals[None]
    # rotate +90 degrees: (a, b) -> (-b, a)
    vor = np.stack([-src[..., 1], src[..., 0]], axis=-1)
    return src, vor


def solve_panels(nodes: np.ndarray, alpha_deg: float, kutta: bool = True) -> PanelSolution:
    """Solve the potential flow around a closed polygon.

    alpha_deg is the angle of attack of an UPRIGHT airfoil (nose-up positive).
    kutta=False removes the vortex (used only to validate the solver on a circle).
    """
    centers, tangents, normals, lengths = _geometry(nodes)
    n = len(lengths)
    a = np.radians(alpha_deg)
    vinf = np.array([np.cos(a), np.sin(a)])           # airfoil fixed, flow arrives from front-below

    src, vor = _unit_panel_velocity(centers, nodes, tangents, normals, lengths)

    # Influence of panel j on control point i, resolved along n_i and t_i.
    a_n = np.einsum("ijk,ik->ij", src, normals)
    a_t = np.einsum("ijk,ik->ij", src, tangents)
    b_n = np.einsum("ijk,ik->ij", vor, normals)
    b_t = np.einsum("ijk,ik->ij", vor, tangents)

    # Self-influence of a constant panel at its own midpoint (exact limits):
    #   source: normal +1/2, tangential 0    vortex: normal 0, tangential -1/2
    idx = np.arange(n)
    a_n[idx, idx], a_t[idx, idx] = 0.5, 0.0
    b_n[idx, idx], b_t[idx, idx] = 0.0, -0.5
    b_n, b_t = b_n.sum(axis=1), b_t.sum(axis=1)

    rhs_n = -(normals @ vinf)
    rhs_t = -(tangents @ vinf)

    if kutta:
        mat = np.zeros((n + 1, n + 1))
        rhs = np.zeros(n + 1)
        mat[:n, :n] = a_n
        mat[:n, n] = b_n
        rhs[:n] = rhs_n
        # Kutta: tangential speeds on the two trailing-edge panels cancel
        mat[n, :n] = a_t[0] + a_t[n - 1]
        mat[n, n] = b_t[0] + b_t[n - 1]
        rhs[n] = rhs_t[0] + rhs_t[n - 1]
        sol = np.linalg.solve(mat, rhs)
        sources, gamma = sol[:n], float(sol[n])
    else:
        sources = np.linalg.solve(a_n, rhs_n)
        gamma = 0.0

    vt = a_t @ sources + gamma * b_t + (tangents @ vinf)
    cp = 1.0 - vt**2

    # Force on each panel = -Cp * n * length (per unit chord, c = 1)
    force = -(cp * lengths)[:, None] * normals
    fx, fy = force.sum(axis=0)
    cl = float(-fx * np.sin(a) + fy * np.cos(a))
    cd = float(fx * np.cos(a) + fy * np.sin(a))

    return PanelSolution(nodes, alpha_deg, centers, tangents, normals, lengths,
                         sources, gamma, vt, cp, cl, cd)


def velocity_field(sol: PanelSolution, x, y, chunk: int = 2000):
    """Velocity (u, v) at arbitrary points (x, y arrays of equal shape),
    in units of the free-stream speed. Points inside the body give meaningless
    values; use `inside_mask` to hide them. Evaluated in chunks to bound memory."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    pts = np.column_stack([x.ravel(), y.ravel()])

    a = np.radians(sol.alpha_deg)
    vinf = np.array([np.cos(a), np.sin(a)])
    vel = np.empty_like(pts)
    for start in range(0, len(pts), chunk):
        part = pts[start:start + chunk]
        src, vor = _unit_panel_velocity(part, sol.nodes, sol.tangents,
                                        sol.normals, sol.lengths)
        vel[start:start + chunk] = (np.einsum("mnk,n->mk", src, sol.sources)
                                    + sol.gamma * vor.sum(axis=1) + vinf)
    return vel[:, 0].reshape(x.shape), vel[:, 1].reshape(x.shape)


def inside_mask(sol: PanelSolution, x, y, margin: float = 0.0) -> np.ndarray:
    """True where (x, y) lies inside the airfoil outline."""
    pts = np.column_stack([np.asarray(x).ravel(), np.asarray(y).ravel()])
    inside = Path(sol.nodes).contains_points(pts, radius=margin)
    return inside.reshape(np.shape(x))
