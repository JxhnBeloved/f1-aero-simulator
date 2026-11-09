"""test_derived.py: derived dashboard quantities."""
import pytest

from aero.derived import drag_power_kw, induced_drag_share, kw_to_hp


def test_drag_power_is_force_times_velocity():
    # 500 N at 80 m/s = 40 kW
    assert drag_power_kw(500.0, 80.0) == pytest.approx(40.0)


def test_kw_to_metric_horsepower():
    assert kw_to_hp(0.7355) == pytest.approx(1.0)


def test_induced_share_is_a_fraction():
    assert induced_drag_share(0.25, 0.30) == pytest.approx(25.0 / 30.0)
