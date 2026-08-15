"""Grip pattern library.

Each `GripPattern` defines the joint targets and safe velocity/force limits
for one prosthetic hand configuration. Limits here are conservative defaults
for a reference platform and must be tuned per-device during clinical
fitting.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GripPattern(str, Enum):
    REST = "rest"
    POWER = "power"          # whole-hand power grasp
    PINCH = "pinch"           # thumb-index precision pinch
    TRIPOD = "tripod"         # thumb-index-middle tripod grasp
    POINT = "point"           # index extended, others flexed
    LATERAL_KEY = "lateral_key"  # key/lateral pinch
    OPEN = "open"             # full hand release


@dataclass(frozen=True)
class GripLimits:
    max_close_velocity_pct_per_s: float
    max_grip_force_n: float
    max_joint_travel_pct: float  # 0-100, cap on how far joints may close


GRIP_LIBRARY: dict[GripPattern, GripLimits] = {
    GripPattern.REST: GripLimits(0.0, 0.0, 0.0),
    GripPattern.POWER: GripLimits(max_close_velocity_pct_per_s=120.0, max_grip_force_n=45.0, max_joint_travel_pct=100.0),
    GripPattern.PINCH: GripLimits(max_close_velocity_pct_per_s=80.0, max_grip_force_n=15.0, max_joint_travel_pct=70.0),
    GripPattern.TRIPOD: GripLimits(max_close_velocity_pct_per_s=90.0, max_grip_force_n=20.0, max_joint_travel_pct=80.0),
    GripPattern.POINT: GripLimits(max_close_velocity_pct_per_s=100.0, max_grip_force_n=5.0, max_joint_travel_pct=100.0),
    GripPattern.LATERAL_KEY: GripLimits(max_close_velocity_pct_per_s=90.0, max_grip_force_n=25.0, max_joint_travel_pct=75.0),
    GripPattern.OPEN: GripLimits(max_close_velocity_pct_per_s=150.0, max_grip_force_n=0.0, max_joint_travel_pct=100.0),
}
