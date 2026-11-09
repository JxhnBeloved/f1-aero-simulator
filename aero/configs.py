"""
configs.py
Three illustrative wing presets for comparison mode.

IMPORTANT: these are NOT measurements of any real car or circuit package. They
are plausible, internally consistent parameter sets chosen to show the classic
trade-off between a low-drag (high-speed track) and a high-downforce
(slow, twisty track) rear-wing philosophy.
"""
from __future__ import annotations

from .wing import WingConfig

LOW_DRAG = WingConfig(
    name="Low drag (Monza-style)",
    chord_m=0.30, span_m=0.95, aoa_deg=4.0,
    cl0=0.80, alpha_stall_deg=12.0, cd0=0.018,
    oswald_e=0.90, endplate_factor=1.10,
)

BALANCED = WingConfig(
    name="Balanced",
    chord_m=0.35, span_m=0.95, aoa_deg=8.0,
    cl0=1.00, alpha_stall_deg=14.0, cd0=0.020,
    oswald_e=0.90, endplate_factor=1.15,
)

HIGH_DOWNFORCE = WingConfig(
    name="High downforce (Monaco-style)",
    chord_m=0.42, span_m=0.95, aoa_deg=12.0,
    cl0=1.20, alpha_stall_deg=16.0, cd0=0.025,
    oswald_e=0.88, endplate_factor=1.25,
)

PRESETS = (LOW_DRAG, BALANCED, HIGH_DOWNFORCE)
