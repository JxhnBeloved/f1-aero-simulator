"""
sweeps.py
Vectorised parameter sweeps over the calculation engine.
No plotting and no UI code here; this module only returns NumPy arrays.
"""
from __future__ import annotations

import numpy as np

from .coefficients import drag_coefficient, lift_coefficient
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
