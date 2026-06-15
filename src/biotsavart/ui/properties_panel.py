from __future__ import annotations
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QGroupBox, QLabel, QDoubleSpinBox,
    QSpinBox, QComboBox, QCheckBox, QPushButton, QSlider, QHBoxLayout,
    QScrollArea,
)

from ..scene import Scene
from ..core import PRESETS, Loop, Line, Wire, Spline, Polygon
from ..core.geometry import Arc
from .statistics_panel import StatisticsPanel


class PropertiesPanel(QWidget):
    """Right-side dock: material, grid, display, and selected wire properties."""

    selected_wire_changed = pyqtSignal(str)  # wire id

    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self._selected_id: str | None = None
        self._building = False  # guard against feedback loops

        self._current_debounce = QTimer(self)
        self._current_debounce.setSingleShot(True)
        self._current_debounce.setInterval(120)
        self._current_debounce.timeout.connect(self._apply_current)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)

        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner = QWidget(); scroll.setWidget(inner)
        layout = QVBoxLayout(inner); layout.setSpacing(8)
        outer.addWidget(scroll)

        # ----- Statistics Panel (NEW) -----
        self.stats_panel = StatisticsPanel()
        layout.addWidget(self.stats_panel)

        # ----- Material -----
        gb_mat = QGroupBox("Medio material"); fm = QFormLayout(gb_mat)
        self.cb_material = QComboBox()
        for key, mat in PRESETS.items():
            self.cb_material.addItem(f"{mat.name}  (μr={mat.mu_r:g})", key)
        self.cb_material.currentIndexChanged.connect(self._on_material)
        fm.addRow("Tipo:", self.cb_material)
        self.lb_mu = QLabel("1.0")
        fm.addRow("μr:", self.lb_mu)
        layout.addWidget(gb_mat)

        # ----- Grid -----
        gb_grid = QGroupBox("Malla de campo"); fg = QFormLayout(gb_grid)
        self.sp_extent = QDoubleSpinBox(); self.sp_extent.setRange(0.2, 50.0)
        self.sp_extent.setValue(2.0); self.sp_extent.setSingleStep(0.5)
        self.sp_extent.setSuffix(" m")
        self.sp_n = QSpinBox(); self.sp_n.setRange(8, 120); self.sp_n.setValue(40)
        self.btn_apply_grid = QPushButton("Aplicar malla")
        self.btn_apply_grid.clicked.connect(self._on_apply_grid)
        fg.addRow("Semi-extensión:", self.sp_extent)
        fg.addRow("Resolución (N³):", self.sp_n)
        fg.addRow(self.btn_apply_grid)
        layout.addWidget(gb_grid)

        # ----- Display -----
        gb_disp = QGroupBox("Visualización"); fd = QVBoxLayout(gb_disp)
        self.ck_wires = QCheckBox("Cables");        self.ck_wires.setChecked(True)
        self.ck_arrows = QCheckBox("Vectores B");   self.ck_arrows.setChecked(True)
        self.ck_stream = QCheckBox("Líneas de campo"); self.ck_stream.setChecked(False)
        self.ck_iso = QCheckBox("Isosuperficies"); self.ck_iso.setChecked(False)
        self.ck_log = QCheckBox("Escala log de |B|"); self.ck_log.setChecked(True)
        for cb in (self.ck_wires, self.ck_arrows, self.ck_stream, self.ck_iso, self.ck_log):
            cb.toggled.connect(self._on_display)
            fd.addWidget(cb)
        layout.addWidget(gb_disp)

        # ----- Selected wire -----
        self.gb_wire = QGroupBox("Cable seleccionado")
        fw = QFormLayout(self.gb_wire)
        self.lb_wire_id = QLabel("—")
        self.sp_current = QDoubleSpinBox()
        self.sp_current.setRange(-1e6, 1e6); self.sp_current.setDecimals(3)
        self.sp_current.setSuffix(" A"); self.sp_current.setSingleStep(0.5)
        self.sp_current.valueChanged.connect(lambda _: self._current_debounce.start())
        self.sl_current = QSlider(Qt.Orientation.Horizontal)
        self.sl_current.setRange(-1000, 1000); self.sl_current.setValue(10)
        self.sl_current.valueChanged.connect(self._on_slider)
        self.sp_disc = QSpinBox(); self.sp_disc.setRange(8, 5000); self.sp_disc.setValue(200)
        self.sp_disc.valueChanged.connect(self._on_disc)
        self.btn_delete = QPushButton("Eliminar cable")
        self.btn_delete.clicked.connect(self._on_delete)
        fw.addRow("ID:", self.lb_wire_id)
        fw.addRow("Corriente:", self.sp_current)
        fw.addRow("", self.sl_current)
        fw.addRow("Segmentos:", self.sp_disc)
        fw.addRow(self.btn_delete)
        layout.addWidget(self.gb_wire)
        self.gb_wire.setEnabled(False)

        layout.addStretch(1)

        # subscribe to scene
        scene.material_changed.connect(self._refresh_material_label)

    def select_wire(self, wire_id: str | None) -> None:
        self._selected_id = wire_id
        self._building = True
        if wire_id is None:
            self.gb_wire.setEnabled(False)
            self.lb_wire_id.setText("—")
        else:
            w = self.scene.find(wire_id)
            if w is None:
                self.gb_wire.setEnabled(False)
                self.lb_wire_id.setText("—")
            else:
                self.gb_wire.setEnabled(True)
                self.lb_wire_id.setText(w.label or wire_id[:8])
                self.sp_current.setValue(w.current)
                self.sl_current.setValue(int(round(w.current * 100)))
                self.sp_disc.setValue(w.discretization)
        self._building = False

    # --- handlers ---
    def _on_material(self):
        key = self.cb_material.currentData()
        self.scene.set_material(PRESETS[key])

    def _refresh_material_label(self):
        self.lb_mu.setText(f"{self.scene.material.mu_r:g}")

    def _on_apply_grid(self):
        from ..core import CartesianGrid
        ext = self.sp_extent.value(); n = self.sp_n.value()
        self.scene.set_grid(CartesianGrid.centered(ext, n))

    def _on_display(self):
        d = self.scene.display
        d.show_wires = self.ck_wires.isChecked()
        d.show_arrows = self.ck_arrows.isChecked()
        d.show_streamlines = self.ck_stream.isChecked()
        d.show_isosurfaces = self.ck_iso.isChecked()
        d.log_scale = self.ck_log.isChecked()
        self.scene.display_changed.emit()

    def _on_slider(self, v: int):
        if self._building: return
        self.sp_current.setValue(v / 100.0)

    def _apply_current(self):
        if self._building or self._selected_id is None: return
        self.scene.update_wire(self._selected_id, current=self.sp_current.value())

    def _on_disc(self, v: int):
        if self._building or self._selected_id is None: return
        self.scene.update_wire(self._selected_id, discretization=v)

    def _on_delete(self):
        if self._selected_id is None: return
        wid = self._selected_id
        self.select_wire(None)
        self.scene.remove_wire(wid)
        self.selected_wire_changed.emit("")
    
    def update_statistics(self, B_array=None, compute_time_ms=None):
        """Actualizar panel de estadísticas después de un cálculo.
        
        Args:
            B_array: Array [P, 3] con campo magnético o None
            compute_time_ms: Tiempo de cálculo en ms o None
        """
        self.stats_panel.update_from_scene(self.scene, B_array, compute_time_ms)
