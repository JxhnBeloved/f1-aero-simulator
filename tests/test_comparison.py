"""test_comparison.py: presets, speed sweep and comparison behaviour."""
import numpy as np
import pytest

from aero.configs import BALANCED, HIGH_DOWNFORCE, LOW_DRAG, PRESETS
from aero.forces import FlowCondition, compute_performance
from aero.sweeps import sweep_velocity


def test_three_valid_presets_exist():
    assert len(PRESETS) == 3
    assert len({w.name for w in PRESETS}) == 3


def test_high_downforce_preset_makes_most_downforce_and_most_drag():
    flow = FlowCondition(80.0)
    low = compute_performance(LOW_DRAG, flow)
    mid = compute_performance(BALANCED, flow)
    high = compute_performance(HIGH_DOWNFORCE, flow)
    assert low.downforce_n < mid.downforce_n < high.downforce_n
    assert low.drag_n < mid.drag_n < high.drag_n


def test_low_drag_preset_is_most_efficient():
    flow = FlowCondition(80.0)
    ratios = [compute_performance(w, flow).l_over_d for w in PRESETS]
    assert ratios[0] == max(ratios)


def test_speed_sweep_scales_with_velocity_squared():
    speeds = np.array([40.0, 80.0])
    sweep = sweep_velocity(BALANCED, 1.225, speeds)
    assert sweep["downforce_n"][1] / sweep["downforce_n"][0] == pytest.approx(4.0)
    assert sweep["drag_n"][1] / sweep["drag_n"][0] == pytest.approx(4.0)


def test_speed_sweep_matches_single_point_calculation():
    sweep = sweep_velocity(HIGH_DOWNFORCE, 1.2, np.array([70.0]))
    single = compute_performance(HIGH_DOWNFORCE, FlowCondition(70.0, 1.2))
    assert sweep["downforce_n"][0] == pytest.approx(single.downforce_n)
    assert sweep["drag_n"][0] == pytest.approx(single.drag_n)
    assert sweep["l_over_d"][0] == pytest.approx(single.l_over_d)
    assert sweep["velocity_kmh"][0] == pytest.approx(70.0 * 3.6)
