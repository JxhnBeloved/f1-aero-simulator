"""
coefficients.py
Simplified aerodynamic coefficient model for a finite wing.

MODEL LEVEL: "Level 1.5". Linear lift curve with a finite-wing correction,
induced drag from lifting-line theory, and a simple empirical stall model.

Assumptions and limitations:
  * Incompressible, steady, attached flow below stall.
  * Prandtl finite-wing correction: a = a0 / (1 + a0 / (pi * e * AR_eff)),
    with a0 = 2*pi per radian (thin-airfoil theory).
  * Induced drag: CDi = CL^2 / (pi * e * AR_eff).
  * Stall is an EMPIRICAL shape (linear CL loss + linear drag growth),
    NOT a prediction from boundary-layer physics.
  * Reynolds number effects, ground effect and multi-element interaction
    are not modelled here (they come in later stages).
  * Valid for roughly -5 to +25 degrees; do not trust it outside that.
"""
from __future__ import annotations

import numpy as np

from .wing import WingConfig

A0_PER_RAD = 2.0 * np.pi        # thin-airfoil lift-curve slope, per radian
STALL_DRAG_GAIN = 0.50          # extra CD at 10 deg beyond stall (empirical)


def _out(x):
    """Return a plain float for scalar input, an array otherwise."""
    x = np.asarray(x)
    return float(x) if x.ndim == 0 else x


def lift_curve_slope_per_rad(wing: WingConfig) -> float:
    """Finite-wing lift-curve slope dCL/dalpha (per radian)."""
    return A0_PER_RAD / (
        1.0 + A0_PER_RAD / (np.pi * wing.oswald_e * wing.effective_aspect_ratio)
    )


def lift_coefficient(wing: WingConfig, aoa_deg=None):
    """Downforce coefficient CL. aoa_deg may be a scalar or a NumPy array."""
    alpha = np.asarray(wing.aoa_deg if aoa_deg is None else aoa_deg, dtype=float)
    slope_per_deg = lift_curve_slope_per_rad(wing) * np.pi / 180.0

    cl_linear = wing.cl0 + slope_per_deg * alpha
    cl_at_stall = wing.cl0 + slope_per_deg * wing.alpha_stall_deg

    excess = np.clip(alpha - wing.alpha_stall_deg, 0.0, None)
    loss = wing.post_stall_drop * np.minimum(excess / 10.0, 1.0)
    cl_stalled = cl_at_stall * (1.0 - loss)

    return _out(np.where(alpha <= wing.alpha_stall_deg, cl_linear, cl_stalled))


def induced_drag_coefficient(wing: WingConfig, cl):
    """CDi = CL^2 / (pi * e * AR_eff)."""
    cl = np.asarray(cl, dtype=float)
    return _out(cl ** 2 / (np.pi * wing.oswald_e * wing.effective_aspect_ratio))


def separation_drag_coefficient(wing: WingConfig, aoa_deg=None):
    """Extra drag after stall (empirical, zero below the stall angle)."""
    alpha = np.asarray(wing.aoa_deg if aoa_deg is None else aoa_deg, dtype=float)
    excess = np.clip(alpha - wing.alpha_stall_deg, 0.0, None)
    return _out(STALL_DRAG_GAIN * np.minimum(excess / 10.0, 2.0))


def drag_coefficient(wing: WingConfig, aoa_deg=None):
    """Total CD = CD0 + CDi + CD_separation."""
    cl = lift_coefficient(wing, aoa_deg)
    return _out(
        wing.cd0
        + induced_drag_coefficient(wing, cl)
        + separation_drag_coefficient(wing, aoa_deg)
    )
