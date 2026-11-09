"""
test_panel_method.py
Validation of the 2D panel method against known analytical and reference results.
"""
import numpy as np
import pytest

from aero.airfoil import airfoil_nodes, circle_nodes, naca4_surfaces
from aero.panel_method import inside_mask, solve_panels, velocity_field

NACA0012 = (0.0, 0.4, 0.12)
NACA2412 = (0.02, 0.4, 0.12)
NACA4412 = (0.04, 0.4, 0.12)


def test_circle_matches_exact_potential_flow():
    # Exact result for a cylinder: Cp = 1 - 4 sin^2(theta), CL = 0
    sol = solve_panels(circle_nodes(100), 0.0, kutta=False)
    exact = 1.0 - 4.0 * sol.centers[:, 1] ** 2
    assert np.max(np.abs(sol.cp - exact)) < 0.01
    assert sol.cl == pytest.approx(0.0, abs=1e-9)


def test_geometry_is_closed_with_expected_panel_count():
    nodes = airfoil_nodes(*NACA4412, n=61)
    assert len(nodes) == 2 * (61 - 1) + 1
    assert np.allclose(nodes[0], nodes[-1])


def test_naca0012_maximum_thickness_is_12_percent():
    (_, yu), (_, yl) = naca4_surfaces(*NACA0012, n=121)
    assert np.max(yu - yl) == pytest.approx(0.12, abs=0.002)


def test_invalid_geometry_is_rejected():
    with pytest.raises(ValueError):
        naca4_surfaces(0.5, 0.4, 0.12)
    with pytest.raises(ValueError):
        naca4_surfaces(0.04, 0.4, 0.9)


def test_symmetric_airfoil_has_zero_lift_at_zero_alpha():
    assert solve_panels(airfoil_nodes(*NACA0012), 0.0).cl == pytest.approx(0.0, abs=1e-3)


def test_lift_is_odd_in_alpha_for_symmetric_airfoil():
    plus = solve_panels(airfoil_nodes(*NACA0012), 5.0).cl
    minus = solve_panels(airfoil_nodes(*NACA0012), -5.0).cl
    assert minus == pytest.approx(-plus, rel=1e-3)


def test_naca0012_lift_slope_is_close_to_thin_airfoil_theory():
    # Thin-airfoil theory: 2*pi*sin(5 deg) = 0.548; a 12 % thick section is a bit higher.
    cl = solve_panels(airfoil_nodes(*NACA0012), 5.0).cl
    assert 0.55 < cl < 0.68


def test_cambered_airfoil_lifts_at_zero_alpha():
    # NACA 2412: zero-lift angle is about -2 deg, so CL(0) is roughly 0.23 - 0.26
    cl = solve_panels(airfoil_nodes(*NACA2412), 0.0).cl
    assert 0.20 < cl < 0.30


def test_more_camber_gives_more_lift():
    low = solve_panels(airfoil_nodes(*NACA2412), 4.0).cl
    high = solve_panels(airfoil_nodes(*NACA4412), 4.0).cl
    assert high > low


def test_dalembert_paradox_zero_drag():
    # Inviscid flow past a closed body has no drag.
    sol = solve_panels(airfoil_nodes(*NACA0012), 5.0)
    assert abs(sol.cd) < 0.005


def test_kutta_condition_trailing_edge_speeds_match():
    sol = solve_panels(airfoil_nodes(*NACA4412), 6.0)
    assert sol.vt[0] + sol.vt[-1] == pytest.approx(0.0, abs=1e-9)


def test_pressure_integration_agrees_with_kutta_joukowski():
    sol = solve_panels(airfoil_nodes(*NACA4412), 6.0)
    cl_kj = -2.0 * sol.gamma * sol.lengths.sum()        # CL = 2*Gamma/(V*c)
    assert sol.cl == pytest.approx(cl_kj, rel=0.03)


def test_field_velocity_matches_surface_velocity_just_outside_the_body():
    sol = solve_panels(airfoil_nodes(*NACA4412), 8.0)
    i = 90
    point = sol.centers[i] + 1e-3 * sol.normals[i]
    u, v = velocity_field(sol, np.array([point[0]]), np.array([point[1]]))
    assert np.hypot(u, v)[0] == pytest.approx(abs(sol.vt[i]), rel=0.01)


def test_far_field_recovers_free_stream():
    sol = solve_panels(airfoil_nodes(*NACA4412), 8.0)
    u, v = velocity_field(sol, np.array([40.0]), np.array([25.0]))
    a = np.radians(8.0)
    assert u[0] == pytest.approx(np.cos(a), abs=0.01)
    assert v[0] == pytest.approx(np.sin(a), abs=0.01)


def test_inside_mask():
    sol = solve_panels(airfoil_nodes(*NACA4412), 0.0)
    inside = inside_mask(sol, np.array([0.3, 0.3]), np.array([0.03, 0.3]))
    assert list(inside) == [True, False]
