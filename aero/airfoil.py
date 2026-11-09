"""
airfoil.py
Airfoil geometry: NACA 4-digit sections and the node ordering the panel method needs.

All coordinates are normalised by the chord (chord = 1) and describe an UPRIGHT
airfoil (positive lift points up, +y). An F1 wing is an inverted wing; because
the physics is mirror-symmetric we solve the upright problem and flip the picture
when we draw it (see viz/flow_field.py).
"""
from __future__ import annotations

import numpy as np


def naca4_surfaces(camber: float, camber_pos: float, thickness: float, n: int = 61):
    """Upper and lower surface coordinates of a NACA 4-digit airfoil.

    camber      maximum camber as a fraction of chord (0.04 = 4 %)
    camber_pos  chordwise position of maximum camber (0.4 = 40 %)
    thickness   maximum thickness as a fraction of chord (0.12 = 12 %)
    n           points per surface (cosine spacing, dense at the leading/trailing edge)

    Uses the closed-trailing-edge thickness polynomial.
    """
    if not 0.0 <= camber <= 0.15:
        raise ValueError("camber must be between 0 and 0.15")
    if not 0.05 <= thickness <= 0.30:
        raise ValueError("thickness must be between 0.05 and 0.30")
    if camber > 0 and not 0.1 <= camber_pos <= 0.9:
        raise ValueError("camber_pos must be between 0.1 and 0.9")

    beta = np.linspace(0.0, np.pi, n)
    x = 0.5 * (1.0 - np.cos(beta))

    yt = 5.0 * thickness * (
        0.2969 * np.sqrt(x) - 0.1260 * x - 0.3516 * x**2
        + 0.2843 * x**3 - 0.1036 * x**4
    )

    if camber == 0.0:
        yc = np.zeros_like(x)
        dyc = np.zeros_like(x)
    else:
        p, m = camber_pos, camber
        front = x < p
        yc = np.where(front, m / p**2 * (2 * p * x - x**2),
                      m / (1 - p) ** 2 * ((1 - 2 * p) + 2 * p * x - x**2))
        dyc = np.where(front, 2 * m / p**2 * (p - x),
                       2 * m / (1 - p) ** 2 * (p - x))

    theta = np.arctan(dyc)
    xu, yu = x - yt * np.sin(theta), yc + yt * np.cos(theta)
    xl, yl = x + yt * np.sin(theta), yc - yt * np.cos(theta)
    return (xu, yu), (xl, yl)


def airfoil_nodes(camber: float, camber_pos: float, thickness: float, n: int = 61):
    """Closed polygon of panel nodes, ordered clockwise starting at the trailing edge:
    trailing edge -> along the lower surface -> leading edge -> along the upper
    surface -> back to the trailing edge. Returns an (N+1, 2) array whose last
    row equals the first, giving N = 2*(n-1) panels.
    """
    (xu, yu), (xl, yl) = naca4_surfaces(camber, camber_pos, thickness, n)
    xs = np.concatenate([xl[::-1], xu[1:]])
    ys = np.concatenate([yl[::-1], yu[1:]])
    nodes = np.column_stack([xs, ys])
    nodes[-1] = nodes[0]          # close the polygon exactly
    return nodes


def circle_nodes(n_panels: int = 100) -> np.ndarray:
    """Unit-radius circle, clockwise from (1, 0). Used only to validate the solver."""
    phi = -np.linspace(0.0, 2.0 * np.pi, n_panels + 1)
    nodes = np.column_stack([np.cos(phi), np.sin(phi)])
    nodes[-1] = nodes[0]
    return nodes
