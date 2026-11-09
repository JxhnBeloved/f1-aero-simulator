"""
drs.py
Drag Reduction System (DRS) model: rear wing flap open versus closed.

MODEL (deliberately simple and illustrative)
    Opening the DRS flap flattens the wing: it loses camber and effective incidence.
    We represent that with two parameters applied to the closed-wing configuration:
        * cl0_fraction       fraction of the camber lift (CL at 0 deg) that is kept
        * aoa_reduction_deg  reduction of the effective angle of attack, degrees
    Everything else (area, aspect ratio, profile drag, stall angle) is unchanged.

LIMITS
    The parameters are NOT calibrated to any real car. The model has no flap-gap flow,
    no wake interaction and no car-level effects. Treat results as trends.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .forces import AeroResult, FlowCondition, compute_performance
from .sweeps import sweep_aoa
from .wing import WingConfig


@dataclass(frozen=True)
class DRSModel:
    cl0_fraction: float = 0.55
    aoa_reduction_deg: float = 2.5

    def __post_init__(self) -> None:
        if not 0.0 <= self.cl0_fraction <= 1.0:
            raise ValueError("cl0_fraction must be between 0 and 1")
        if self.aoa_reduction_deg < 0.0:
            raise ValueError("aoa_reduction_deg must be >= 0")


@dataclass(frozen=True)
class DRSComparison:
    closed: AeroResult
    opened: AeroResult
    downforce_change_n: float      # opened - closed (negative = downforce lost)
    downforce_change_pct: float
    drag_change_n: float           # opened - closed (negative = drag saved)
    drag_change_pct: float
    drag_power_saved_kw: float     # (closed drag - opened drag) * V


def apply_drs(wing: WingConfig, model: DRSModel = DRSModel()) -> WingConfig:
    """The same wing with the DRS flap open."""
    return wing.with_changes(
        name=f"{wing.name} (DRS open)",
        cl0=wing.cl0 * model.cl0_fraction,
        aoa_deg=wing.aoa_deg - model.aoa_reduction_deg,
    )


def compare_drs(wing: WingConfig, flow: FlowCondition,
                model: DRSModel = DRSModel()) -> DRSComparison:
    """Closed versus open performance at one flow condition."""
    closed = compute_performance(wing, flow)
    opened = compute_performance(apply_drs(wing, model), flow)
    d_df = opened.downforce_n - closed.downforce_n
    d_dr = opened.drag_n - closed.drag_n
    return DRSComparison(
        closed=closed,
        opened=opened,
        downforce_change_n=d_df,
        downforce_change_pct=100.0 * d_df / closed.downforce_n,
        drag_change_n=d_dr,
        drag_change_pct=100.0 * d_dr / closed.drag_n,
        drag_power_saved_kw=-d_dr * flow.velocity_ms / 1000.0,
    )


def sweep_drs(wing: WingConfig, flow: FlowCondition, set_angles_deg,
              model: DRSModel = DRSModel()):
    """Closed and open sweeps over the SAME driver-set wing angle.

    Returns (closed_sweep, open_sweep). Both use the set angle on the x axis; the
    open wing's effective angle is the set angle minus the DRS reduction.
    """
    set_angles = np.asarray(set_angles_deg, dtype=float)
    closed = sweep_aoa(wing, flow, set_angles)
    opened = sweep_aoa(apply_drs(wing, model), flow, set_angles - model.aoa_reduction_deg)
    opened["aoa_deg"] = set_angles
    return closed, opened
