"""
verify_setup.py
Checks that Python and all dependencies work, and runs one tiny
aerodynamics calculation as a sanity test.
"""
import sys
from importlib import import_module

REQUIRED = ["numpy", "scipy", "matplotlib", "streamlit", "pytest"]


def check_python():
    v = sys.version_info
    ok = (3, 10) <= (v.major, v.minor) <= (3, 12)
    status = "OK  " if ok else "WARN"
    print(f"[{status}] Python {v.major}.{v.minor}.{v.micro}")
    if not ok:
        print("       Recommended: Python 3.10 - 3.12 (other versions may still work)")
    return True  # a warning, not a failure


def check_packages():
    all_ok = True
    for name in REQUIRED:
        try:
            module = import_module(name)
            version = getattr(module, "__version__", "unknown")
            print(f"[OK  ] {name} {version}")
        except ImportError:
            print(f"[FAIL] {name} is not installed")
            all_ok = False
    return all_ok


def check_physics():
    """Dynamic pressure q = 0.5 * rho * V^2 at 80 m/s, sea level."""
    import numpy as np

    rho = 1.225   # kg/m^3, ISA sea level
    v = 80.0      # m/s
    q = 0.5 * rho * v**2
    ok = bool(np.isclose(q, 3920.0))
    print(f"[{'OK  ' if ok else 'FAIL'}] Dynamic pressure at 80 m/s = {q:.1f} Pa")
    return ok


def check_plotting():
    import matplotlib
    matplotlib.use("Agg")  # no window needed
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots()
    v = np.linspace(0, 100, 50)
    ax.plot(v, 0.5 * 1.225 * v**2)
    ax.set_xlabel("Velocity (m/s)")
    ax.set_ylabel("Dynamic pressure (Pa)")
    fig.savefig("setup_test_plot.png", dpi=100)
    plt.close(fig)
    print("[OK  ] Matplotlib saved setup_test_plot.png")
    return True


def main():
    print("=== F1 Aero Simulator: environment check ===")
    print()
    results = [check_python(), check_packages()]
    if results[1]:
        results += [check_physics(), check_plotting()]
    print()
    if all(results):
        print("All checks passed. Ready for Stage 4.")
    else:
        print("Some checks failed. Fix the items marked FAIL above.")


if __name__ == "__main__":
    main()
