"""
forces.py
Turns coefficients into forces in newtons for a given flow condition.

    q          = 0.5 * rho * V^2
    Downforce  = q * S * CL
    Drag       = q * S * CD
    Efficiency = Downforce / Drag   (L/D, "aerodynamic efficiency")
"""
from __future__ import annotations

from dataclasses import dataclass

from .coefficients import (
    drag_coefficient,
    induced_drag_coefficient,
    lift_coefficient,
)
from .constants import GRAVITY, MS_TO_KMH, RHO_SEA_LEVEL
from .wing import WingConfig


@dataclass(frozen=True)
class FlowCondition:
    velocity_ms: float = 80.0            # ~288 km/h
    air_density: float = RHO_SEA_LEVEL   # kg/m^3

    def __post_init__(self) -> None:
        if self.velocity_ms < 0:
            raise ValueError("velocity_ms must be >= 0")
        if self.air_density <= 0:
            raise ValueError("air_density must be > 0")


@dataclass(frozen=True)
class AeroResult:
    name: str
    aoa_deg: float
    velocity_kmh: float
    dynamic_pressure_pa: float
    cl: float
    cd: float
    cd_induced: float
    downforce_n: float
    drag_n: float
    l_over_d: float
    downforce_kgf: float      # downforce expressed as an equivalent mass load
    is_stalled: bool


def dynamic_pressure(velocity_ms: float, air_density: float = RHO_SEA_LEVEL) -> float:
    """q = 0.5 * rho * V^2, in pascals."""
    return 0.5 * air_density * velocity_ms ** 2


def compute_performance(wing: WingConfig, flow: FlowCondition) -> AeroResult:
    """Full performance of one wing at one flow condition."""
    q = dynamic_pressure(flow.velocity_ms, flow.air_density)
    cl = lift_coefficient(wing)
    cd = drag_coefficient(wing)

    downforce = q * wing.area_m2 * cl
    drag = q * wing.area_m2 * cd

    return AeroResult(
        name=wing.name,
        aoa_deg=wing.aoa_deg,
        velocity_kmh=flow.velocity_ms * MS_TO_KMH,
        dynamic_pressure_pa=q,
        cl=cl,
        cd=cd,
        cd_induced=induced_drag_coefficient(wing, cl),
        downforce_n=downforce,
        drag_n=drag,
        l_over_d=cl / cd,
        downforce_kgf=downforce / GRAVITY,
        is_stalled=wing.aoa_deg > wing.alpha_stall_deg,
    )
