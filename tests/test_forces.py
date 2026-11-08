"""
test_forces.py
Validation tests for the Stage 4 calculation engine.
Run from the project root with:  pytest -v
"""
import math

import numpy as np
import pytest

from aero.coefficients import (
    A0_PER_RAD,
    drag_coefficient,
    induced_drag_coefficient,
    lift_coefficient,
    lift_curve_slope_per_rad,
)
from aero.forces import FlowCondition, compute_performance, dynamic_pressure
from aero.wing import WingConfig


def test_dynamic_pressure_known_value():
    # 0.5 * 1.225 * 80^2 = 3920 Pa
    assert dynamic_pressure(80.0, 1.225) == pytest.approx(3920.0)


def test_geometry():
    wing = WingConfig(chord_m=0.5, span_m=1.0)
    assert wing.area_m2 == pytest.approx(0.5)
    assert wing.aspect_ratio == pytest.approx(2.0)


def test_slope_approaches_thin_airfoil_limit_for_huge_aspect_ratio():
    # As AR -> infinity the finite-wing slope must approach 2*pi per radian.
    wing = WingConfig(chord_m=1.0, span_m=1e9, oswald_e=1.0, endplate_factor=1.0)
    assert lift_curve_slope_per_rad(wing) == pytest.approx(A0_PER_RAD, rel=1e-6)


def test_finite_wing_slope_is_below_2d_slope():
    assert lift_curve_slope_per_rad(WingConfig()) < A0_PER_RAD


def test_zero_lift_wing_has_only_profile_drag():
    wing = WingConfig(cl0=0.0, aoa_deg=0.0, cd0=0.02)
    assert lift_coefficient(wing) == pytest.approx(0.0)
    assert drag_coefficient(wing) == pytest.approx(0.02)


def test_induced_drag_formula():
    wing = WingConfig(chord_m=0.5, span_m=1.0, oswald_e=1.0, endplate_factor=1.0)
    # AR = 2, so CDi = CL^2 / (pi * 2)
    assert induced_drag_coefficient(wing, 1.0) == pytest.approx(1.0 / (2 * math.pi))


def test_downforce_increases_with_angle_below_stall():
    wing = WingConfig()
    angles = np.arange(0, wing.alpha_stall_deg + 0.1, 1.0)
    cl = lift_coefficient(wing, angles)
    assert np.all(np.diff(cl) > 0)


def test_cl_falls_after_stall_and_drag_keeps_rising():
    wing = WingConfig()
    at_stall = wing.with_changes(aoa_deg=wing.alpha_stall_deg)
    after = wing.with_changes(aoa_deg=wing.alpha_stall_deg + 6)
    assert lift_coefficient(after) < lift_coefficient(at_stall)
    assert drag_coefficient(after) > drag_coefficient(at_stall)


def test_forces_scale_with_velocity_squared():
    wing = WingConfig()
    slow = compute_performance(wing, FlowCondition(velocity_ms=40.0))
    fast = compute_performance(wing, FlowCondition(velocity_ms=80.0))
    assert fast.downforce_n / slow.downforce_n == pytest.approx(4.0)
    assert fast.drag_n / slow.drag_n == pytest.approx(4.0)
    # Coefficients do not depend on speed in this model.
    assert fast.cl == pytest.approx(slow.cl)


def test_forces_scale_linearly_with_density():
    wing = WingConfig()
    thin = compute_performance(wing, FlowCondition(80.0, 0.6))
    sea = compute_performance(wing, FlowCondition(80.0, 1.2))
    assert sea.downforce_n / thin.downforce_n == pytest.approx(2.0)


def test_l_over_d_matches_force_ratio():
    result = compute_performance(WingConfig(), FlowCondition())
    assert result.l_over_d == pytest.approx(result.downforce_n / result.drag_n)


def test_plausible_magnitude_for_baseline_wing():
    # An F1-style rear wing at ~288 km/h should make roughly 1-4 kN.
    result = compute_performance(WingConfig(), FlowCondition(80.0))
    assert 1000 < result.downforce_n < 4000


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        WingConfig(chord_m=-0.1)
    with pytest.raises(ValueError):
        WingConfig(oswald_e=1.5)
    with pytest.raises(ValueError):
        FlowCondition(velocity_ms=-5)
    with pytest.raises(ValueError):
        FlowCondition(air_density=0)
