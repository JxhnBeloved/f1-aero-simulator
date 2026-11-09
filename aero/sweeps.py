"""
sweeps.py
Vectorised parameter sweeps over the calculation engine.
No plotting and no UI code here; this module only returns NumPy arrays.
"""
from __future__ import annotations

import numpy as np

from .coefficients import drag_coefficient, lift_coefficient
from .constants import MS_TO_KMH
from .forces import FlowCondition, dynamic_pressure
from .wing import WingConfig


def sweep_aoa(wing: WingConfig, flow: FlowCondition, angles_deg) -> dict:
    """Performance of one wing over a range of angles of attack.

    Returns a dict of equal-length NumPy arrays:
    aoa_deg, cl, cd, l_over_d, downforce_n, drag_n.
    """
    angles = np.asarray(angles_deg, dtype=float)
    q = dynamic_pressure(flow.velocity_ms, flow.air_density)

    cl = np.asarray(lift_coefficient(wing, angles))
    cd = np.asarray(drag_coefficient(wing, angles))

    return {
        "aoa_deg": angles,
        "cl": cl,
        "cd": cd,
        "l_over_d": cl / cd,
        "downforce_n": q * wing.area_m2 * cl,
        "drag_n": q * wing.area_m2 * cd,
    }


def sweep_velocity(wing: WingConfig, air_density: float, velocities_ms) -> dict:
    """Performance of one wing (at its own angle of attack) over a range of airspeeds.

    Returns a dict of equal-length NumPy arrays:
    velocity_ms, velocity_kmh, downforce_n, drag_n, l_over_d.
    In this model CL and CD do not depend on speed, so forces scale as V^2.
    """
    v = np.asarray(velocities_ms, dtype=float)
    q = 0.5 * air_density * v**2

    cl = lift_coefficient(wing)
    cd = drag_coefficient(wing)

    return {
        "velocity_ms": v,
        "velocity_kmh": v * MS_TO_KMH,
        "downforce_n": q * wing.area_m2 * cl,
        "drag_n": q * wing.area_m2 * cd,
        "l_over_d": np.full_like(v, cl / cd),
    }
