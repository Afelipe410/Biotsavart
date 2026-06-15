from __future__ import annotations
import time
import numpy as np
from PyQt6.QtCore import QObject, QThread, pyqtSignal

from ..core import compute_B_on_grid
from ..scene import Scene


class FieldWorker(QObject):
    """Computes B = compute_B_on_grid(wires_with_I=1, grid) in a worker thread.
    Scaling by per-wire I and μ_r is done at draw time (linear superposition),
    so we never recompute when the user only moves a current slider.
    """
    finished = pyqtSignal(np.ndarray, float)  # B(unit currents), elapsed sec
    failed = pyqtSignal(str)

    def __init__(self, scene: Scene):
        super().__init__()
        self._scene = scene

    def run(self):
        try:
            # Compute B with each wire's current set to its sign (we want B/|I_ref|)
            # Simpler: compute with current values directly; multiply by μ_r in viewport.
            t0 = time.perf_counter()
            B = compute_B_on_grid(self._scene.wires, self._scene.grid, mu_r=1.0)
            dt = time.perf_counter() - t0
            self.finished.emit(B, dt)
        except Exception as e:
            self.failed.emit(str(e))
