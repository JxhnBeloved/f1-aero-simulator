"""
wing.py
Geometry and aerodynamic parameters of a single wing, as one immutable object.

Sign convention (important):
    The wing is an INVERTED wing. We define aoa_deg so that a POSITIVE angle
    means MORE DOWNFORCE. "CL" in this project therefore means
    downforce coefficient (positive = pushes the car down).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class WingConfig:
    name: str = "Baseline rear wing"

    # --- geometry ---
    chord_m: float = 0.35            # mean chord (flow direction), m
    span_m: float = 0.95             # span (across the car), m
    aoa_deg: float = 8.0             # angle of attack, deg (positive = more downforce)

    # --- aerodynamic model parameters (see coefficients.py for meaning) ---
    cl0: float = 1.0                 # downforce coefficient at 0 deg (camber effect)
    alpha_stall_deg: float = 14.0    # angle where flow starts to separate
    post_stall_drop: float = 0.30    # fraction of CL lost 10 deg beyond stall
    cd0: float = 0.020               # profile (friction + form) drag coefficient
    oswald_e: float = 0.90           # span efficiency factor, 0 < e <= 1
    endplate_factor: float = 1.15    # effective aspect-ratio multiplier from endplates

    def __post_init__(self) -> None:
        positive = {
            "chord_m": self.chord_m,
            "span_m": self.span_m,
            "alpha_stall_deg": self.alpha_stall_deg,
            "cd0": self.cd0,
            "oswald_e": self.oswald_e,
            "endplate_factor": self.endplate_factor,
        }
        for field_name, value in positive.items():
            if not value > 0:
                raise ValueError(f"{field_name} must be > 0 (got {value})")
        if self.oswald_e > 1.0:
            raise ValueError(f"oswald_e must be <= 1 (got {self.oswald_e})")
        if not 0.0 <= self.post_stall_drop < 1.0:
            raise ValueError("post_stall_drop must be in [0, 1)")

    @property
    def area_m2(self) -> float:
        """Planform area S = chord * span."""
        return self.chord_m * self.span_m

    @property
    def aspect_ratio(self) -> float:
        """Geometric aspect ratio AR = span^2 / S = span / chord."""
        return self.span_m ** 2 / self.area_m2

    @property
    def effective_aspect_ratio(self) -> float:
        """Aspect ratio including the (approximate) benefit of endplates."""
        return self.aspect_ratio * self.endplate_factor

    def with_changes(self, **changes) -> "WingConfig":
        """Return a copy with some fields changed (used for comparison mode)."""
        return replace(self, **changes)
