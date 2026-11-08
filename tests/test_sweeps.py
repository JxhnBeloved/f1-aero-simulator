"""test_sweeps.py: the vectorised sweep must agree with the single-point engine."""
import numpy as np
import pytest

from aero.forces import FlowCondition, compute_performance
from aero.sweeps import sweep_aoa
from aero.wing import WingConfig


def test_sweep_matches_single_point_calculation():
    wing = WingConfig()
    flow = FlowCondition(velocity_ms=70.0, air_density=1.1)
    angles = np.array([0.0, 5.0, 10.0, 16.0, 20.0])
    sweep = sweep_aoa(wing, flow, angles)

    for i, angle in enumerate(angles):
        single = compute_performance(wing.with_changes(aoa_deg=float(angle)), flow)
        assert sweep["downforce_n"][i] == pytest.approx(single.downforce_n)
        assert sweep["drag_n"][i] == pytest.approx(single.drag_n)
        assert sweep["l_over_d"][i] == pytest.approx(single.l_over_d)


def test_sweep_returns_equal_length_arrays():
    sweep = sweep_aoa(WingConfig(), FlowCondition(), np.linspace(-5, 25, 31))
    lengths = {len(v) for v in sweep.values()}
    assert lengths == {31}
