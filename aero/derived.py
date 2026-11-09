"""
derived.py
Small derived quantities for the dashboard. Pure functions, SI units.
"""
from __future__ import annotations

METRIC_HP_PER_KW = 1.0 / 0.7355   # 1 PS (metric horsepower) = 0.7355 kW


def drag_power_kw(drag_n: float, velocity_ms: float) -> float:
    """Power needed to overcome aerodynamic drag: P = D * V, in kilowatts."""
    return drag_n * velocity_ms / 1000.0


def kw_to_hp(power_kw: float) -> float:
    """Kilowatts to metric horsepower."""
    return power_kw * METRIC_HP_PER_KW


def induced_drag_share(cd_induced: float, cd_total: float) -> float:
    """Fraction (0 to 1) of total drag that is induced drag."""
    return cd_induced / cd_total
