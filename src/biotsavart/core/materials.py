from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """
    Define un material magnético con su permeabilidad relativa (mu_r) y
    un color sugerido para representarlo gráficamente.
    """
    name: str
    mu_r: float
    color_hint: str = "#cccccc"


# Materiales básicos
VACUUM = Material(
    "Vacío",
    1.0,
    "#cccccc"
)

AIR = Material(
    "Aire",
    1.00000037,
    "#dfe6e9"
)

ALUMINUM = Material(
    "Aluminio",
    1.000022,
    "#74b9ff"
)

COPPER = Material(
    "Cobre",
    0.999994,
    "#e17055"
)

FERRITE = Material(
    "Ferrita",
    2000.0,
    "#6c5ce7"
)

IRON = Material(
    "Hierro dulce",
    5000.0,
    "#ff7675"
)

STEEL = Material(
    "Acero",
    1000.0,
    "#636e72"
)

SUPERCONDUCTOR = Material(
    "Superconductor",
    0.000001,
    "#00ff88"
)


PRESETS = {
    "vacuum": VACUUM,
    "air": AIR,
    "aluminum": ALUMINUM,
    "copper": COPPER,
    "ferrite": FERRITE,
    "iron": IRON,
    "steel": STEEL,
    "superconductor": SUPERCONDUCTOR,
}