"""
theory.py
Closed-form reference results used to VALIDATE the numerical code. Nothing in the
simulator's results depends on this module; it exists so that tests and the
validation report can compare numerical output against independent theory.

Thin-airfoil theory (small angles, inviscid, incompressible):
    CL = 2*pi*(alpha - alpha_L0)             alpha in radians
    alpha_L0 = -(1/pi) * Integral_0^pi (dyc/dx) (cos(theta) - 1) dtheta
with x = (1 - cos(theta)) / 2 and yc the camber line.

Thickness correction (common empirical rule of thumb): multiply the lift slope by
about (1 + 0.77 * t/c). It is approximate, so comparisons use a tolerance.
"""
from __future__ import annotations

import numpy as np

THICKNESS_SLOPE_FACTOR = 0.77


def thin_airfoil_alpha_l0_deg(camber: float, camber_pos: float, n: int = 20000) -> float:
    """Zero-lift angle (degrees, negative for positive camber) of a NACA 4-digit camber line."""
    if camber == 0.0:
        return 0.0
    theta = (np.arange(n) + 0.5) * np.pi / n
    x = 0.5 * (1.0 - np.cos(theta))
    p, m = camber_pos, camber
    dyc = np.where(x < p, 2 * m / p**2 * (p - x), 2 * m / (1 - p) ** 2 * (p - x))
    alpha_l0 = -(1.0 / np.pi) * np.sum(dyc * (np.cos(theta) - 1.0)) * (np.pi / n)
    return float(np.degrees(alpha_l0))


def thin_airfoil_cl(alpha_deg: float, camber: float = 0.0, camber_pos: float = 0.4,
                    thickness: float = 0.0) -> float:
    """Thin-airfoil lift coefficient, optionally with the thickness slope correction."""
    alpha_l0 = thin_airfoil_alpha_l0_deg(camber, camber_pos)
    cl = 2.0 * np.pi * np.radians(alpha_deg - alpha_l0)
    return float(cl * (1.0 + THICKNESS_SLOPE_FACTOR * thickness))
