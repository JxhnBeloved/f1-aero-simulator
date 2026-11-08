"""
demo_stage4.py
Quick command-line demo of the Stage 4 calculation engine.
Run:  python demo_stage4.py
"""
from aero.forces import FlowCondition, compute_performance
from aero.wing import WingConfig


def main() -> None:
    wing = WingConfig()
    flow = FlowCondition(velocity_ms=80.0)

    print(f"Wing: {wing.name}")
    print(f"  chord {wing.chord_m} m, span {wing.span_m} m, "
          f"area {wing.area_m2:.3f} m^2, AR {wing.aspect_ratio:.2f}")
    print(f"Flow: {flow.velocity_ms} m/s, rho {flow.air_density} kg/m^3\n")

    print(f"{'AoA':>5} {'CL':>6} {'CD':>6} {'L/D':>6} "
          f"{'Downforce N':>12} {'Drag N':>8}  note")
    for aoa in range(0, 25, 2):
        r = compute_performance(wing.with_changes(aoa_deg=aoa), flow)
        note = "STALLED" if r.is_stalled else ""
        print(f"{r.aoa_deg:5.1f} {r.cl:6.3f} {r.cd:6.3f} {r.l_over_d:6.2f} "
              f"{r.downforce_n:12.0f} {r.drag_n:8.0f}  {note}")


if __name__ == "__main__":
    main()
