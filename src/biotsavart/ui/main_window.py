from __future__ import annotations
import numpy as np
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QAction, QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QStatusBar,
    QFileDialog, QMessageBox, QApplication,
    QLabel, QComboBox
)

from ..core import Wire, Loop, Charge
from ..scene import Scene, save_scene, load_scene
from ..viz import Viewport
from .scene_tree import SceneTree
from .properties_panel import PropertiesPanel
from .dialogs import AddWireDialog
from .compute_worker import FieldWorker
from .charge_dialog import ChargeDialog
from PyQt6.QtCore import QSize

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.apply_theme("dark_theme")

        self.setWindowTitle("Biot-Savart Studio")
        self.resize(1800, 1000)
        self.scene = Scene()
        self.viewport = Viewport(self.scene, self)
        self.setCentralWidget(self.viewport)

        # docks
        self.tree = SceneTree(self.scene, self)
        dock_tree = QDockWidget("Escena", self); dock_tree.setWidget(self.tree)
        dock_tree.setMinimumWidth(280)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock_tree)

        self.props = PropertiesPanel(self.scene, self)
        dock_props = QDockWidget("Propiedades", self); dock_props.setWidget(self.props)
        dock_props.setMinimumWidth(380)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock_props)

        self.tree.wire_selected.connect(self.props.select_wire)

        # status bar
        self.setStatusBar(QStatusBar(self))
        self.status_label = self.statusBar()

        # toolbar
        self._build_toolbar()

        # signals
        self.scene.wires_changed.connect(self._on_wires_changed)
        self.scene.grid_changed.connect(self._on_wires_changed)
        self.scene.current_changed.connect(self._on_currents_changed)
        self.scene.material_changed.connect(self._on_material_changed)
        self.scene.display_changed.connect(self._refresh_viewport)

        # async compute infrastructure
        self._thread: QThread | None = None
        self._worker: FieldWorker | None = None
        self._pending = False
        self._B_unit: np.ndarray | None = None  # last computed B with current values

        # default scene
        self._seed_default_scene()
        
        # Initialize statistics panel
        self.props.stats_panel.update_from_scene(self.scene)

        
    def apply_theme(self, theme_name):
        from pathlib import Path
        theme_file = Path(__file__).parent / f"{theme_name}.qss"
        if theme_file.exists():
            with open(theme_file, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        
        # Synchronize viewport background
        if hasattr(self, 'viewport'):
            self.viewport.set_theme_mode(is_dark="dark" in theme_name)

    # ----- toolbar -----
    def _build_toolbar(self):
        tb = QToolBar("Main", self)
        tb.setMovable(False)
        tb.setIconSize(QSize(24,24))
        self.addToolBar(tb)
        act_add = QAction("+ Nuevo Conductor", self); act_add.triggered.connect(self._on_add_wire)
        act_charge = QAction("+ Carga", self)
        act_charge.triggered.connect(self._add_charge)
        tb.addAction(act_charge)
        tb.addAction(act_add)
        act_demo = QAction("Demo: Helmholtz", self); act_demo.triggered.connect(self._on_demo_helmholtz)
        tb.addAction(act_demo)
        tb.addSeparator()
        act_recompute = QAction("Recalcular", self); act_recompute.setShortcut("F5")
        act_recompute.triggered.connect(self._schedule_compute)
        tb.addAction(act_recompute)
        act_reset = QAction("Reset cámara", self); act_reset.triggered.connect(self.viewport.reset_camera)
        tb.addAction(act_reset)
        tb.addSeparator()
        act_save = QAction("Guardar…", self); act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._on_save); tb.addAction(act_save)
        act_open = QAction("Abrir…", self); act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._on_open); tb.addAction(act_open)
        tb.addSeparator()

        tb.addWidget(QLabel("Tema:"))

        self.theme_combo = QComboBox()

        self.theme_combo.addItem(" Oscuro", "dark_theme")
        self.theme_combo.addItem(" Claro", "light_theme")

        tb.addWidget(self.theme_combo)

        self.theme_combo.currentIndexChanged.connect(
        lambda: self.apply_theme(
        self.theme_combo.currentData()
         )
        )

    # ----- seed -----
    def _seed_default_scene(self):
        # one circular loop on z=0, radius 1, 10 A
        self.scene.add_wire(Wire(geometry=Loop(radius=1.0), current=10.0,
                                 discretization=200, label="Loop demo"))

    # ----- actions -----
    def _on_add_wire(self):
        dlg = AddWireDialog(self)
        if dlg.exec():
            self.scene.add_wire(dlg.build_wire())

    def _on_demo_helmholtz(self):
        self.scene.clear()
        R = 1.0
        self.scene.add_wire(Wire(geometry=Loop(center=np.array([0, 0, +R/2]), radius=R),
                                 current=10.0, discretization=240, label="Loop +"))
        self.scene.add_wire(Wire(geometry=Loop(center=np.array([0, 0, -R/2]), radius=R),
                                 current=10.0, discretization=240, label="Loop −"))

    def _on_save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Guardar escena", filter="JSON (*.json)")
        if path:
            try:
                save_scene(self.scene, path)
                self.statusBar().showMessage(f"Escena guardada: {path}", 5000)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_open(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir escena", filter="JSON (*.json)")
        if path:
            try:
                new_scene = load_scene(path)
                self.scene.clear()
                for w in new_scene.wires:
                    self.scene.add_wire(w)
                self.scene.set_material(new_scene.material)
                self.scene.set_grid(new_scene.grid)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    # ----- recompute orchestration -----
    def _on_wires_changed(self):
        self._schedule_compute()

    def _on_currents_changed(self):
        # B is linear in I per segment; but per-segment current means total B is the
        # *same arrays* recomputed only if currents change relative to the cached B.
        # Cheapest correct strategy here: recompute (still fast). For a slider-heavy
        # workflow, we'd precompute per-wire unit fields. Future optimization.
        self._schedule_compute()

    def _on_material_changed(self):
        self.props._refresh_material_label()
        self._refresh_viewport()  # only scale changes, no recompute

    def _schedule_compute(self):
        if self._thread is not None and self._thread.isRunning():
            self._pending = True
            return
        self._pending = False
        self._thread = QThread(self)
        self._worker = FieldWorker(self.scene)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_compute_done)
        self._worker.failed.connect(self._on_compute_failed)
        self.statusBar().showMessage("Calculando campo B…")
        self._thread.start()

    def _cleanup_thread(self):
        if self._thread is not None:
            self._thread.quit(); self._thread.wait()
            self._thread = None; self._worker = None
        if self._pending:
            QTimer.singleShot(0, self._schedule_compute)

    def _on_compute_done(self, B: np.ndarray, dt: float):
        self._B_unit = B
        dt_ms = dt * 1000.0
        self.statusBar().showMessage(
            f"B calculado en {dt_ms:.0f} ms · {B.size//3} puntos · "
            f"|B|max = {np.linalg.norm(B, axis=-1).max():.3e} T"
        )
        # Update statistics panel with new data
        self.props.update_statistics(B, dt_ms)
        self._refresh_viewport()
        self._cleanup_thread()

    def _on_compute_failed(self, msg: str):
        QMessageBox.warning(self, "Error en cálculo", msg)
        self.statusBar().showMessage("Cálculo fallido")
        self._cleanup_thread()

    def _refresh_viewport(self):
        if self._B_unit is None:
            self.viewport.refresh()
            return
        self.viewport.set_field(self._B_unit, scale=self.scene.material.mu_r)

    # ----- shutdown -----
    def closeEvent(self, ev):
        try:
            self.viewport.close_plotter()
        except Exception:
            pass
        super().closeEvent(ev)

    def _add_charge(self):
        dialog = ChargeDialog()
        if not dialog.exec():
            return

        x = dialog.x.value()
        y = dialog.y.value()
        z = dialog.z.value()
        vx = dialog.vx.value()
        vy = dialog.vy.value()
        vz = dialog.vz.value()
        
        mass = dialog.mass.value()
        charge_mag = dialog.charge_mag.value() * 1e-6  # uC to C
        
        charge_sign = 1 if dialog.charge_type.currentText() == "Positiva" else -1

        c = Charge(
            position=np.array([x, y, z], dtype=float),
            q=charge_sign * charge_mag,
            mass=mass,
            velocity=np.array([vx, vy, vz], dtype=float)
        )

        self.scene.add_charge(c)
        self.viewport.refresh()