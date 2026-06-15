"""Closed-form Biot-Savart solutions for validation."""
from __future__ import annotations
import numpy as np
from .biot_savart import MU0


def circular_loop_axis_B(I: float, R: float, z: np.ndarray) -> np.ndarray:
    """B_z on the axis of a circular loop in the z=0 plane."""
    return MU0 * I * R**2 / (2.0 * (R**2 + z**2) ** 1.5)


def infinite_wire_B(I: float, d: np.ndarray) -> np.ndarray:
    """|B| at perpendicular distance d from an infinite straight wire."""
    return MU0 * I / (2.0 * np.pi * d)


def ideal_solenoid_B(I: float, turns_per_meter: float) -> float:
    """Uniform |B| inside an ideal infinite solenoid."""
    return MU0 * turns_per_meter * I
