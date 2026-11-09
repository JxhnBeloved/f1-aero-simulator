"""
run_validation.py
Runs a battery of validation checks on the simulator and writes
    docs/validation_report.md           (tables of expected vs observed)
    docs/images/validation_summary.png  (four validation plots)

Run from the project root:   python scripts/run_validation.py
"""
import itertools
import platform
import sys
from datetime import date
from pathlib import Path

import matplotlib
import numpy as np
from matplotlib.figure import Figure

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aero.airfoil import airfoil_nodes, circle_nodes  # noqa: E402
from aero.coefficients import lift_coefficient, lift_curve_slope_per_rad  # noqa: E402
from aero.configs import PRESETS  # noqa: E402
from aero.derived import drag_power_kw  # noqa: E402
from aero.forces import FlowCondition, compute_performance, dynamic_pressure  # noqa: E402
from aero.panel_method import solve_panels, velocity_field  # noqa: E402
from aero.sweeps import sweep_aoa  # noqa: E402
from aero.theory import thin_airfoil_alpha_l0_deg, thin_airfoil_cl  # noqa: E402
from aero.wing import WingConfig  # noqa: E402

CHECKS = []   # (section, id, description, expected, observed, passed)


def check(section, cid, description, expected, observed, passed):
    CHECKS.append((section, cid, description, expected, observed, bool(passed)))


# ------------------------------------------------------------ A. analytical model
def run_analytical():
    s = "A. Analytical wing model"
    wing, flow = WingConfig(), FlowCondition(80.0)
    base = compute_performance(wing, flow)

    q = dynamic_pressure(80.0, 1.225)
    check(s, "A1", "Dynamic pressure at 80 m/s, sea level", "3920 Pa", f"{q:.1f} Pa",
          abs(q - 3920.0) < 1e-6)

    fast = compute_performance(wing, FlowCondition(160.0))
    check(s, "A2", "Doubling airspeed multiplies downforce and drag by 4",
          "4.000 and 4.000",
          f"{fast.downforce_n / base.downforce_n:.3f} and {fast.drag_n / base.drag_n:.3f}",
          np.isclose(fast.downforce_n / base.downforce_n, 4.0)
          and np.isclose(fast.drag_n / base.drag_n, 4.0))

    dense = compute_performance(wing, FlowCondition(80.0, 2.45))
    check(s, "A3", "Doubling air density doubles the forces", "2.000",
          f"{dense.downforce_n / base.downforce_n:.3f}",
          np.isclose(dense.downforce_n / base.downforce_n, 2.0))

    big = compute_performance(wing.with_changes(chord_m=0.70, span_m=1.90), flow)
    check(s, "A4", "Geometric similarity: chord and span x2 gives forces x4, CL unchanged",
          "x4.000, CL ratio 1.000",
          f"x{big.downforce_n / base.downforce_n:.3f}, CL ratio {big.cl / base.cl:.3f}",
          np.isclose(big.downforce_n / base.downforce_n, 4.0) and np.isclose(big.cl, base.cl))

    inf_wing = WingConfig(chord_m=1.0, span_m=1e9, oswald_e=1.0, endplate_factor=1.0)
    ratio = lift_curve_slope_per_rad(inf_wing) / (2 * np.pi)
    check(s, "A5", "Lift slope tends to the thin-airfoil value 2*pi as aspect ratio grows",
          "ratio 1.000", f"ratio {ratio:.6f}", np.isclose(ratio, 1.0, rtol=1e-6))

    unit = WingConfig(chord_m=0.5, span_m=1.0, oswald_e=1.0, endplate_factor=1.0)
    cdi = compute_performance(unit.with_changes(cl0=1.0, aoa_deg=0.0), flow).cd_induced
    expected = 1.0 / (2 * np.pi)
    check(s, "A6", "Induced drag = CL^2/(pi e AR) for CL = 1, AR = 2, e = 1",
          f"{expected:.5f}", f"{cdi:.5f}", np.isclose(cdi, expected))

    slope = lift_curve_slope_per_rad(wing) * np.pi / 180.0
    alpha0 = -wing.cl0 / slope
    cl0 = lift_coefficient(wing, alpha0)
    check(s, "A7", "CL is zero at the analytically derived zero-lift angle",
          "0.0", f"{cl0:.1e} at {alpha0:.2f} deg", abs(cl0) < 1e-9)

    angles = np.linspace(-5, 25, 1201)
    peak = angles[np.argmax(lift_coefficient(wing, angles))]
    check(s, "A8", "Downforce peaks at the stall angle",
          f"{wing.alpha_stall_deg:.2f} deg", f"{peak:.2f} deg",
          abs(peak - wing.alpha_stall_deg) < 0.05)

    ld = [compute_performance(wing.with_changes(span_m=sp), flow).l_over_d
          for sp in (0.6, 0.95, 1.4)]
    check(s, "A9", "Efficiency L/D rises with span (aspect ratio 1.7 -> 2.7 -> 4.0)",
          "increasing", " < ".join(f"{x:.2f}" for x in ld), ld[0] < ld[1] < ld[2])

    p = drag_power_kw(base.drag_n, 80.0)
    check(s, "A10", "Power absorbed by drag = D * V", f"{base.drag_n * 80.0 / 1000:.1f} kW",
          f"{p:.1f} kW", np.isclose(p, base.drag_n * 80.0 / 1000.0))


# ---------------------------------------------------------------- B. panel method
def run_panel():
    s = "B. 2D panel method"
    circ = solve_panels(circle_nodes(100), 0.0, kutta=False)
    err = np.max(np.abs(circ.cp - (1.0 - 4.0 * circ.centers[:, 1] ** 2)))
    check(s, "B1", "Circular cylinder: Cp = 1 - 4 sin^2(theta), max error", "< 0.010",
          f"{err:.4f}", err < 0.01)

    sym0 = solve_panels(airfoil_nodes(0.0, 0.4, 0.12), 0.0)
    check(s, "B2", "Symmetric NACA 0012 at 0 deg gives zero lift", "abs(CL) < 0.001",
          f"{sym0.cl:.1e}", abs(sym0.cl) < 1e-3)

    p5 = solve_panels(airfoil_nodes(0.0, 0.4, 0.12), 5.0)
    m5 = solve_panels(airfoil_nodes(0.0, 0.4, 0.12), -5.0)
    check(s, "B3", "Lift is odd in angle for a symmetric airfoil: CL(-5) = -CL(5)",
          f"{-p5.cl:.4f}", f"{m5.cl:.4f}", np.isclose(m5.cl, -p5.cl, rtol=1e-3))

    th = thin_airfoil_cl(5.0, 0.0, 0.4, 0.12)
    check(s, "B4", "NACA 0012 at 5 deg vs thin-airfoil theory with thickness correction",
          f"{th:.3f} (+/- 5 %)", f"{p5.cl:.3f}", np.isclose(p5.cl, th, rtol=0.05))

    c4 = solve_panels(airfoil_nodes(0.04, 0.4, 0.12), 0.0)
    th4 = thin_airfoil_cl(0.0, 0.04, 0.4, 0.12)
    check(s, "B5", "NACA 4412 at 0 deg vs thin-airfoil theory with thickness correction",
          f"{th4:.3f} (+/- 5 %)", f"{c4.cl:.3f}", np.isclose(c4.cl, th4, rtol=0.05))

    alphas = np.arange(-4.0, 9.0, 1.0)
    cls = np.array([solve_panels(airfoil_nodes(0.04, 0.4, 0.12), a).cl for a in alphas])
    mean_slope = np.diff(cls).mean()
    check(s, "B6", "Lift slope per degree (thin airfoil 0.110, thickness raises ~9 %)",
          "0.115 to 0.125", f"{mean_slope:.4f}", 0.115 < mean_slope < 0.125)

    check(s, "B7", "d'Alembert: zero drag for a closed body in inviscid flow",
          "abs(CD) < 0.005", f"{p5.cd:.5f}", abs(p5.cd) < 0.005)

    kutta = solve_panels(airfoil_nodes(0.04, 0.4, 0.12), 6.0)
    te = kutta.vt[0] + kutta.vt[-1]
    check(s, "B8", "Kutta condition: trailing-edge speeds from both surfaces match",
          "sum = 0", f"{te:.1e}", abs(te) < 1e-9)

    cl_kj = -2.0 * kutta.gamma * kutta.lengths.sum()
    check(s, "B9", "Lift from pressure integration vs Kutta-Joukowski (CL = 2 Gamma / V c)",
          f"{cl_kj:.4f} (+/- 3 %)", f"{kutta.cl:.4f}", np.isclose(kutta.cl, cl_kj, rtol=0.03))

    cl_n = {n: solve_panels(airfoil_nodes(0.04, 0.4, 0.12, n=n), 6.0).cl
            for n in (31, 61, 121, 241)}
    change = abs(cl_n[121] - cl_n[61]) / cl_n[121]
    shrinking = abs(cl_n[241] - cl_n[121]) < abs(cl_n[121] - cl_n[61]) < abs(cl_n[61] - cl_n[31])
    check(s, "B10", "Mesh convergence: CL change from 120 to 240 panels",
          "< 1 %, shrinking with refinement", f"{change * 100:.2f} %", change < 0.01 and shrinking)

    sol = solve_panels(airfoil_nodes(0.04, 0.4, 0.12), 8.0)
    i = 90
    point = sol.centers[i] + 1e-3 * sol.normals[i]
    u, v = velocity_field(sol, np.array([point[0]]), np.array([point[1]]))
    speed_field, speed_surface = float(np.hypot(u, v)[0]), float(abs(sol.vt[i]))
    check(s, "B11", "Field velocity just outside the surface equals surface velocity",
          f"{speed_surface:.4f} (+/- 1 %)", f"{speed_field:.4f}",
          np.isclose(speed_field, speed_surface, rtol=0.01))

    mirror = np.max(np.abs(p5.cp - m5.cp[::-1]))
    check(s, "B12", "Cp distribution mirror symmetry for a symmetric airfoil", "< 1e-9",
          f"{mirror:.1e}", mirror < 1e-9)


# -------------------------------------------------------- C. configuration matrix
def run_matrix():
    s = "C. Configuration matrix"
    angles = [-5, -2, 0, 4, 8, 12, 14, 16, 20, 25]
    speeds = [20.0, 50.0, 80.0, 97.2, 120.0]
    densities = [0.9, 1.225, 1.3]
    total = bad = 0
    for wing, aoa, v, rho in itertools.product(PRESETS, angles, speeds, densities):
        r = compute_performance(wing.with_changes(aoa_deg=aoa), FlowCondition(v, rho))
        vals = [r.downforce_n, r.drag_n, r.cl, r.cd, r.l_over_d]
        ok = (np.all(np.isfinite(vals)) and r.downforce_n > 0 and r.drag_n > 0
              and r.is_stalled == (aoa > wing.alpha_stall_deg))
        total += 1
        bad += 0 if ok else 1
    check(s, "C1", f"{len(PRESETS)} presets x {len(angles)} angles x {len(speeds)} speeds x "
          f"{len(densities)} densities = {total} configurations: finite, positive, "
          "stall flag consistent", "0 failures", f"{bad} failures", bad == 0)

    flow = FlowCondition(80.0)
    res = [compute_performance(w, flow) for w in PRESETS]
    ordered_df = res[0].downforce_n < res[1].downforce_n < res[2].downforce_n
    ordered_dr = res[0].drag_n < res[1].drag_n < res[2].drag_n
    check(s, "C2", "Presets are ordered: low drag < balanced < high downforce in downforce and drag",
          "both increasing", f"downforce {ordered_df}, drag {ordered_dr}", ordered_df and ordered_dr)
    check(s, "C3", "The low-drag preset has the best L/D", "low drag highest",
          ", ".join(f"{r.l_over_d:.2f}" for r in res),
          res[0].l_over_d == max(r.l_over_d for r in res))
    return res


# -------------------------------------------------------------------- figure
def make_figure(path: Path):
    fig = Figure(figsize=(11, 7.5), dpi=130, constrained_layout=True)
    (ax1, ax2), (ax3, ax4) = fig.subplots(2, 2)

    alphas = np.linspace(-6, 10, 17)
    panel = [solve_panels(airfoil_nodes(0.0, 0.4, 0.12), a).cl for a in alphas]
    ax1.plot(alphas, panel, "o-", label="Panel method (NACA 0012)")
    ax1.plot(alphas, [thin_airfoil_cl(a) for a in alphas], "--", label="Thin-airfoil theory")
    ax1.plot(alphas, [thin_airfoil_cl(a, thickness=0.12) for a in alphas], ":",
             label="Thin-airfoil x (1 + 0.77 t/c)")
    ax1.set(xlabel="Angle of attack (deg)", ylabel="CL", title="Lift curve of a symmetric airfoil")
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    circ = solve_panels(circle_nodes(100), 0.0, kutta=False)
    phi = np.arctan2(circ.centers[:, 1], circ.centers[:, 0])
    grid = np.linspace(-np.pi, np.pi, 400)
    ax2.plot(np.degrees(grid), 1 - 4 * np.sin(grid) ** 2, "-", label="Exact: 1 - 4 sin^2")
    ax2.plot(np.degrees(phi), circ.cp, ".", label="Panel method (100 panels)")
    ax2.set(xlabel="Angle around cylinder (deg)", ylabel="Cp", title="Circular cylinder pressure")
    ax2.set_ylim(-4.0, 1.3)
    ax2.legend(fontsize=8, loc="lower center", ncol=2)
    ax2.grid(True, alpha=0.3)

    ns = [21, 31, 61, 121, 241, 481]
    cl = [solve_panels(airfoil_nodes(0.04, 0.4, 0.12, n=n), 6.0).cl for n in ns]
    ax3.semilogx([2 * (n - 1) for n in ns], cl, "o-")
    ax3.set(xlabel="Number of panels", ylabel="CL (NACA 4412, 6 deg)",
            title="Mesh convergence")
    ax3.grid(True, which="both", alpha=0.3)

    ars = np.linspace(1, 40, 80)
    slopes = [lift_curve_slope_per_rad(WingConfig(chord_m=1.0, span_m=a, oswald_e=1.0,
                                                  endplate_factor=1.0)) for a in ars]
    ax4.plot(ars, slopes, label="Finite-wing slope (model)")
    ax4.axhline(2 * np.pi, color="gray", linestyle="--", label="2D limit 2*pi")
    ax4.set(xlabel="Aspect ratio", ylabel="dCL/dalpha (per radian)",
            title="Finite-wing lift slope approaches the 2D limit")
    ax4.legend(fontsize=8)
    ax4.grid(True, alpha=0.3)

    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)


# -------------------------------------------------------------------- report
def write_report(path: Path, preset_results):
    passed = sum(1 for c in CHECKS if c[5])
    lines = [
        "# Validation report",
        "",
        f"Generated {date.today().isoformat()} with Python {platform.python_version()} "
        f"and NumPy {np.__version__}. Reproduce with `python scripts/run_validation.py`.",
        "",
        f"**Result: {passed} of {len(CHECKS)} checks passed.**",
        "",
        "These checks compare the simulator against analytical results, exact solutions and "
        "its own invariants. They show the code solves its equations correctly. They do not "
        "show that the models match a real car or a wind tunnel.",
        "",
    ]
    for section in dict.fromkeys(c[0] for c in CHECKS):
        lines += [f"## {section}", "", "| ID | Check | Expected | Observed | Result |",
                  "|---|---|---|---|---|"]
        for sec, cid, desc, exp, obs, ok in CHECKS:
            if sec == section:
                lines.append(f"| {cid} | {desc} | {exp} | {obs} | {'PASS' if ok else 'FAIL'} |")
        lines.append("")

    lines += ["## Preset behaviour at 288 km/h", "",
              "| Preset | AoA (deg) | Downforce (N) | Drag (N) | L/D |", "|---|---|---|---|---|"]
    for w, r in zip(PRESETS, preset_results):
        lines.append(f"| {w.name} | {w.aoa_deg:.1f} | {r.downforce_n:,.0f} | "
                     f"{r.drag_n:,.0f} | {r.l_over_d:.2f} |")

    lines += [
        "", "## Known behaviours and limits", "",
        "- **Negative CL:** if the angle is below the zero-lift angle (possible when the CL-at-0-deg "
        "parameter is small), the wing produces lift, and the simulator reports negative downforce and a "
        "negative L/D. This is the correct sign, not an error.",
        "- **Zero airspeed:** forces are exactly zero; L/D is a ratio of coefficients and "
        "stays finite.",
        "- **Stall:** the analytical model's stall is an empirical shape. The panel method "
        "has no boundary layer, so it cannot stall at all.",
        "- **Mesh error:** at the default 120 panels the panel-method lift is within about "
        "1 % of the converged value (check B10).",
        "- **Not validated against experiment:** no wind-tunnel or on-track data was used.",
        "", "## Figures", "", "![Validation summary](images/validation_summary.png)", "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    matplotlib.use("Agg")
    run_analytical()
    run_panel()
    preset_results = run_matrix()
    make_figure(ROOT / "docs" / "images" / "validation_summary.png")
    write_report(ROOT / "docs" / "validation_report.md", preset_results)

    passed = sum(1 for c in CHECKS if c[5])
    for sec, cid, desc, exp, obs, ok in CHECKS:
        print(f"[{'PASS' if ok else 'FAIL'}] {cid:4s} {desc}  (expected {exp}; observed {obs})")
    print(f"\n{passed} of {len(CHECKS)} checks passed.")
    print("Wrote docs/validation_report.md and docs/images/validation_summary.png")
    if passed != len(CHECKS):
        sys.exit(1)


if __name__ == "__main__":
    main()
