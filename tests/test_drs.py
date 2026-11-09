"""test_drs.py: DRS open versus closed model."""
import numpy as np
import pytest

from aero.configs import BALANCED, PRESETS
from aero.drs import DRSModel, apply_drs, compare_drs, sweep_drs
from aero.forces import FlowCondition

FLOW = FlowCondition(80.0)


def test_drs_with_no_change_leaves_performance_unchanged():
    cmp = compare_drs(BALANCED, FLOW, DRSModel(cl0_fraction=1.0, aoa_reduction_deg=0.0))
    assert cmp.downforce_change_n == pytest.approx(0.0, abs=1e-9)
    assert cmp.drag_change_n == pytest.approx(0.0, abs=1e-9)


def test_opening_drs_reduces_both_downforce_and_drag():
    for wing in PRESETS:
        for angle in np.arange(0.0, 25.5, 0.5):
            cmp = compare_drs(wing.with_changes(aoa_deg=float(angle)), FLOW)
            assert cmp.opened.downforce_n < cmp.closed.downforce_n, (wing.name, angle)
            assert cmp.opened.drag_n < cmp.closed.drag_n, (wing.name, angle)


def test_drag_falls_by_a_larger_fraction_than_downforce_in_attached_flow():
    # Induced drag scales with CL^2, so a lift reduction removes proportionally more drag.
    for wing in PRESETS:
        for angle in np.arange(0.0, wing.alpha_stall_deg + 0.1, 0.5):
            cmp = compare_drs(wing.with_changes(aoa_deg=float(angle)), FLOW)
            assert cmp.drag_change_pct < cmp.downforce_change_pct, (wing.name, angle)


def test_efficiency_improves_at_the_preset_settings():
    for wing in PRESETS:
        cmp = compare_drs(wing, FLOW)
        assert cmp.opened.l_over_d > cmp.closed.l_over_d


def test_drag_power_saved_is_force_saved_times_speed():
    cmp = compare_drs(BALANCED, FLOW)
    expected = (cmp.closed.drag_n - cmp.opened.drag_n) * FLOW.velocity_ms / 1000.0
    assert cmp.drag_power_saved_kw == pytest.approx(expected)
    assert cmp.drag_power_saved_kw > 0


def test_stronger_drs_saves_more_drag():
    mild = compare_drs(BALANCED, FLOW, DRSModel(0.8, 1.0))
    strong = compare_drs(BALANCED, FLOW, DRSModel(0.3, 4.0))
    assert strong.drag_change_n < mild.drag_change_n < 0


def test_apply_drs_changes_only_camber_and_angle():
    opened = apply_drs(BALANCED, DRSModel(0.5, 3.0))
    assert opened.cl0 == pytest.approx(BALANCED.cl0 * 0.5)
    assert opened.aoa_deg == pytest.approx(BALANCED.aoa_deg - 3.0)
    assert opened.area_m2 == BALANCED.area_m2
    assert opened.cd0 == BALANCED.cd0
    assert "DRS open" in opened.name


def test_sweep_uses_the_set_angle_and_matches_the_single_point_comparison():
    angles = np.array([4.0, 8.0, 12.0])
    closed, opened = sweep_drs(BALANCED, FLOW, angles)
    assert np.allclose(closed["aoa_deg"], angles)
    assert np.allclose(opened["aoa_deg"], angles)
    cmp = compare_drs(BALANCED, FLOW)          # BALANCED is set at 8 degrees
    assert opened["downforce_n"][1] == pytest.approx(cmp.opened.downforce_n)
    assert opened["drag_n"][1] == pytest.approx(cmp.opened.drag_n)
    assert closed["downforce_n"][1] == pytest.approx(cmp.closed.downforce_n)


def test_invalid_drs_parameters_are_rejected():
    with pytest.raises(ValueError):
        DRSModel(cl0_fraction=1.5)
    with pytest.raises(ValueError):
        DRSModel(cl0_fraction=-0.1)
    with pytest.raises(ValueError):
        DRSModel(aoa_reduction_deg=-1.0)
