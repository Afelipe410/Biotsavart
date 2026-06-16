from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np

from PyQt6.QtCore import QObject, pyqtSignal

from ..core import Wire, CartesianGrid, Material, VACUUM


@dataclass
class DisplaySettings:
    show_wires: bool = True
    show_charges: bool = True
    show_arrows: bool = True
    show_streamlines: bool = False
    show_isosurfaces: bool = False
    log_scale: bool = True
    glyph_factor: float = 0.5
    glyph_tolerance: float = 0.04
    iso_count: int = 5
    streamline_seeds: int = 12


class Scene(QObject):
    """Mutable scene state. Emits Qt signals when changed."""
    wires_changed = pyqtSignal()   # geometry or list changed → recompute B
    current_changed = pyqtSignal() # only currents changed → can rescale B
    material_changed = pyqtSignal()
    grid_changed = pyqtSignal()
    display_changed = pyqtSignal() # viz-only toggles

    def __init__(self):
        super().__init__()
        self.wires: list[Wire] = []
        self.charges = []
        self.grid: CartesianGrid = CartesianGrid.centered(half_extent=2.0, n=40)
        self.material: Material = VACUUM
        self.display: DisplaySettings = DisplaySettings()

    # --- mutations ---
    def add_wire(self, w: Wire) -> None:
        self.wires.append(w)
        self.wires_changed.emit()

    def remove_wire(self, wire_id: str) -> None:
        self.wires = [w for w in self.wires if w.id != wire_id]
        self.wires_changed.emit()

    def update_wire(self, wire_id: str, *, geometry=None, current=None,
                    discretization=None, label=None) -> None:
        for w in self.wires:
            if w.id == wire_id:
                only_current = (geometry is None and discretization is None
                                and current is not None)
                if geometry is not None: w.geometry = geometry
                if current is not None: w.current = float(current)
                if discretization is not None: w.discretization = int(discretization)
                if label is not None: w.label = label
                (self.current_changed if only_current else self.wires_changed).emit()
                return

    def set_material(self, mat: Material) -> None:
        self.material = mat
        self.material_changed.emit()

    def set_grid(self, grid: CartesianGrid) -> None:
        self.grid = grid
        self.grid_changed.emit()

    def find(self, wire_id: str) -> Wire | None:
        for w in self.wires:
            if w.id == wire_id: return w
        return None
    
    def add_charge(self, charge):
     self.charges.append(charge)
     self.display_changed.emit()

    def remove_charge(self, charge_id):
     self.charges = [c for c in self.charges if c.id != charge_id]
     self.display_changed.emit()

    def clear(self) -> None:
     self.wires.clear()
     self.charges.clear()
     self.wires_changed.emit()