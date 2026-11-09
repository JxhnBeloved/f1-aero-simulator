"""
test_invariants.py
Stage 9: behaviour tests across many configurations. Instead of checking a few
hand-picked numbers, these tests check physical INVARIANTS that must hold for
every wing and flow condition, plus numerical convergence of the panel method.
"""
import itertools

import numpy as np
import pytest

from aero.airfoil import airfoil_nodes
from aero.coefficients import lift_coefficient, lift_curve_slope_per_rad
from aero.configs import PRESETS
from aero.forces import FlowCondition, compute_performance
from aero.panel_method import solve_panels
from aero.theory import thin_airfoil_alpha_l0_deg, thin_airfoil_cl
from aero.wing import WingConfig

ANGLES = [-5.0, -2.0, 0.0, 4.0, 8.0, 12.0, 14.0, 16.0, 20.0, 25.0]
SPEEDS_MS = [20.0, 50.0, 80.0, 97.2, 120.0]
DENSITIES = [0.9, 1.225, 1.3]


def _all_configurations():
    for wing, aoa, v, rho in itertools.product(PRESETS, ANGLES, SPEEDS_MS, DENSITIES):
        yield wing.with_changes(aoa_deg=aoa), FlowCondition(v, rho)


def test_every_configuration_gives_finite_positive_results():
    count = 0
    for wing, flow in _all_configurations():
        r = compute_performance(wing, flow)
        values = [r.downforce_n, r.drag_n, r.cl, r.cd, r.l_over_d, r.dynamic_pressure_pa]
        assert np.all(np.isfinite(values)), (wing.name, wing.aoa_deg, flow)
        assert r.downforce_n > 0 and r.drag_n > 0, (wing.name, wing.aoa_deg, flow)
        assert r.is_stalled == (wing.aoa_deg > wing.alpha_stall_deg)
        count += 1
    assert count == len(PRESETS) * len(ANGLES) * len(SPEEDS_MS) * len(DENSITIES)


def test_geometric_similarity_forces_scale_with_area():
    # Scaling chord and span together keeps AR, so CL and CD are unchanged
    # and forces scale with the area, i.e. with the square of the scale factor.
    flow = FlowCondition(80.0)
    for wing in PRESETS:
        base = compute_performance(wing, flow)
        for k in (0.5, 2.0, 3.0):
            big = compute_performance(
                wing.with_changes(chord_m=wing.chord_m * k, span_m=wing.span_m * k), flow)
            assert big.cl == pytest.approx(base.cl)
            assert big.downforce_n / base.downforce_n == pytest.approx(k**2)
            assert big.drag_n / base.drag_n == pytest.approx(k**2)


def test_more_aspect_ratio_means_less_induced_drag_and_better_efficiency():
    flow = FlowCondition(80.0)
    wing = WingConfig()
    results = [compute_performance(wing.with_changes(span_m=s), flow)
               for s in (0.6, 0.95, 1.4)]
    assert results[0].l_over_d < results[1].l_over_d < results[2].l_over_d
    assert results[0].cd_induced > results[1].cd_induced > results[2].cd_induced


def test_better_span_efficiency_and_endplates_improve_efficiency():
    flow = FlowCondition(80.0)
    wing = WingConfig()
    low_e = compute_performance(wing.with_changes(oswald_e=0.6), flow)
    high_e = compute_performance(wing.with_changes(oswald_e=1.0), flow)
    assert high_e.l_over_d > low_e.l_over_d
    no_plates = compute_performance(wing.with_changes(endplate_factor=1.0), flow)
    plates = compute_performance(wing.with_changes(endplate_factor=1.3), flow)
    assert plates.l_over_d > no_plates.l_over_d


def test_lift_is_zero_at_the_zero_lift_angle():
    for wing in PRESETS:
        slope_per_deg = lift_curve_slope_per_rad(wing) * np.pi / 180.0
        alpha_zero = -wing.cl0 / slope_per_deg
        assert lift_coefficient(wing, alpha_zero) == pytest.approx(0.0, abs=1e-9)


def test_negative_cl_means_the_wing_produces_lift_not_downforce():
    # With no camber and a negative angle the wing pushes UP. The sign convention
    # must report that as negative downforce rather than hiding it.
    wing = WingConfig(cl0=0.0, aoa_deg=-3.0)
    r = compute_performance(wing, FlowCondition(80.0))
    assert r.cl < 0 and r.downforce_n < 0


def test_zero_airspeed_gives_zero_forces():
    r = compute_performance(WingConfig(), FlowCondition(0.0))
    assert r.downforce_n == 0.0 and r.drag_n == 0.0


def test_panel_solution_is_mirror_symmetric_for_symmetric_airfoil():
    plus = solve_panels(airfoil_nodes(0.0, 0.4, 0.12), 6.0)
    minus = solve_panels(airfoil_nodes(0.0, 0.4, 0.12), -6.0)
    # Panel i on the lower surface at +alpha mirrors the upper-surface panel at -alpha.
    assert np.max(np.abs(plus.cp - minus.cp[::-1])) < 1e-9


def test_panel_lift_slope_is_nearly_constant_in_the_linear_range():
    angles = np.arange(-4.0, 9.0, 1.0)
    cl = [solve_panels(airfoil_nodes(0.04, 0.4, 0.12), a).cl for a in angles]
    slopes = np.diff(cl)
    assert slopes.max() / slopes.min() < 1.03
    # Thin-airfoil slope is 2*pi per radian = 0.1097 per degree; thickness raises it ~9 %.
    assert 0.115 < slopes.mean() < 0.125


def test_panel_agrees_with_thin_airfoil_theory_with_thickness_correction():
    for camber in (0.0, 0.02, 0.04, 0.06):
        for alpha in (0.0, 3.0, 6.0):
            if camber == 0.0 and alpha == 0.0:
                continue
            panel = solve_panels(airfoil_nodes(camber, 0.4, 0.12), alpha).cl
            theory = thin_airfoil_cl(alpha, camber, 0.4, 0.12)
            assert panel == pytest.approx(theory, rel=0.05), (camber, alpha)


def test_thin_airfoil_zero_lift_angle_matches_published_values():
    # Published zero-lift angles: NACA 2412 about -2.1 deg, NACA 4412 about -4.2 deg.
    assert thin_airfoil_alpha_l0_deg(0.02, 0.4) == pytest.approx(-2.1, abs=0.1)
    assert thin_airfoil_alpha_l0_deg(0.04, 0.4) == pytest.approx(-4.2, abs=0.1)


def test_panel_method_converges_as_panels_are_added():
    # Doubling the number of panels should change CL by less than 1 %, and the
    # change should shrink as the mesh is refined.
    cl = {n: solve_panels(airfoil_nodes(0.04, 0.4, 0.12, n=n), 6.0).cl
          for n in (31, 61, 121, 241)}
    assert abs(cl[121] - cl[61]) / cl[121] < 0.01
    assert abs(cl[241] - cl[121]) < abs(cl[121] - cl[61]) < abs(cl[61] - cl[31])
