"""Soluciones analíticas exactas de la ley de Biot-Savart para validación."""
from __future__ import annotations
import numpy as np
from .biot_savart import MU0


def circular_loop_axis_B(I: float, R: float, z: np.ndarray) -> np.ndarray:
    """
    Calcula el componente Z del campo magnético (B_z) en el eje de una espira circular 
    ubicada en el plano z=0.
    
    Args:
        I: Corriente en amperios.
        R: Radio de la espira.
        z: Arreglo de posiciones en el eje z.
    """
    return MU0 * I * R**2 / (2.0 * (R**2 + z**2) ** 1.5)


def infinite_wire_B(I: float, d: np.ndarray) -> np.ndarray:
    """
    Calcula la magnitud del campo magnético |B| a una distancia perpendicular 'd' 
    de un cable recto infinito.
    """
    return MU0 * I / (2.0 * np.pi * d)


def ideal_solenoid_B(I: float, turns_per_meter: float) -> float:
    """
    Calcula el campo magnético uniforme |B| en el interior de un solenoide ideal infinito.
    """
    return MU0 * turns_per_meter * I
