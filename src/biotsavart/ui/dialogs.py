from __future__ import annotations
import numpy as np
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QDoubleSpinBox, QDialogButtonBox, QComboBox,
    QSpinBox, QHBoxLayout, QWidget, QVBoxLayout, QLabel,QTableWidget,
    QTableWidgetItem,
    QPushButton
)


from ..core import Wire, Line, Loop, Polygon, Spline
from ..core.geometry import Arc


def _vec3(default=(0.0, 0.0, 0.0)) -> tuple[QWidget, list[QDoubleSpinBox]]:
    w = QWidget(); h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0)
    spins = []
    for v in default:
        s = QDoubleSpinBox(); s.setRange(-1e6, 1e6); s.setDecimals(3); s.setValue(v)
        s.setSingleStep(0.1); h.addWidget(s); spins.append(s)
    return w, spins


class AddWireDialog(QDialog):
    """Modal to create a new Wire — pick geometry kind and parameters."""
    def _add_vertex(self):
     table = self._fields["vertex_table"]
     table.insertRow(table.rowCount())

     for c in range(3):
        table.setItem(
            table.rowCount()-1,
            c,
            QTableWidgetItem("0")
        )
    def _remove_vertex(self):
     table = self._fields["vertex_table"]

     if table.rowCount() > 3:
        table.removeRow(table.rowCount()-1)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo cable")
        self.resize(380, 320)
        outer = QVBoxLayout(self)

        self.cb_kind = QComboBox()
        self.cb_kind.addItems(["Line", "Loop", "Arc", "Polygon",
                               "Spline (helix)"])
        self.cb_kind.currentIndexChanged.connect(self._rebuild_form)
        outer.addWidget(QLabel("Tipo de geometría:"))
        outer.addWidget(self.cb_kind)

        self.form_holder = QWidget(); outer.addWidget(self.form_holder)
        self.form = QFormLayout(self.form_holder)

        self.sp_current = QDoubleSpinBox(); self.sp_current.setRange(-1e6, 1e6)
        self.sp_current.setValue(10.0); self.sp_current.setSuffix(" A")
        self.sp_disc = QSpinBox(); self.sp_disc.setRange(8, 5000); self.sp_disc.setValue(200)

        self._fields: dict = {}
        self._rebuild_form()

        bb = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok
                              | QDialogButtonBox.StandardButton.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        outer.addWidget(bb)

    def _rebuild_form(self):
        # Save current values if they exist and are not deleted by PyQt
        try:
            cur_val = self.sp_current.value()
            disc_val = self.sp_disc.value()
        except RuntimeError:
            cur_val = 10.0
            disc_val = 200

        while self.form.rowCount():
            self.form.removeRow(0)
        self._fields.clear()
        
        # Recreate the widgets to avoid using C++ deleted objects
        self.sp_current = QDoubleSpinBox()
        self.sp_current.setRange(-1e6, 1e6)
        self.sp_current.setValue(cur_val)
        self.sp_current.setSuffix(" A")
        
        self.sp_disc = QSpinBox()
        self.sp_disc.setRange(8, 5000)
        self.sp_disc.setValue(disc_val)
        
        kind = self.cb_kind.currentText()
        if kind == "Line":
            w0, sp0 = _vec3((0, 0, -0.5)); w1, sp1 = _vec3((0, 0, 0.5))
            self.form.addRow("Inicio:", w0); self.form.addRow("Fin:", w1)
            self._fields["start"] = sp0; self._fields["end"] = sp1
        elif kind == "Loop":
            wc, spc = _vec3((0, 0, 0)); wn, spn = _vec3((0, 0, 1))
            sr = QDoubleSpinBox(); sr.setRange(0.001, 1e3); sr.setValue(1.0); sr.setSingleStep(0.1)
            self.form.addRow("Centro:", wc); self.form.addRow("Normal:", wn)
            self.form.addRow("Radio:", sr)
            self._fields["center"] = spc; self._fields["normal"] = spn; self._fields["radius"] = sr
        elif kind == "Arc":
            wc, spc = _vec3((0, 0, 0)); wn, spn = _vec3((0, 0, 1))
            sr = QDoubleSpinBox(); sr.setRange(0.001, 1e3); sr.setValue(1.0)
            sa = QDoubleSpinBox(); sa.setRange(-1e3, 1e3); sa.setValue(0.0); sa.setSuffix(" rad")
            ea = QDoubleSpinBox(); ea.setRange(-1e3, 1e3); ea.setValue(3.14159); ea.setSuffix(" rad")
            self.form.addRow("Centro:", wc); self.form.addRow("Normal:", wn)
            self.form.addRow("Radio:", sr); self.form.addRow("θ₀:", sa); self.form.addRow("θ₁:", ea)
            self._fields = dict(center=spc, normal=spn, radius=sr, start_angle=sa, end_angle=ea)
        elif kind == "Polygon":
         self.vertex_table = QTableWidget(3, 3)

         self.vertex_table.setHorizontalHeaderLabels(
          ["X", "Y", "Z"]
        )

         defaults = [
         [0,0,0],
         [1,0,0],
         [0.5,1,0]
        ]

         for r in range(3):
          for c in range(3):
             self.vertex_table.setItem(
                r,
                c,
                QTableWidgetItem(str(defaults[r][c]))
            )

         btn_add = QPushButton("Añadir vértice")
         btn_add.clicked.connect(self._add_vertex)

         btn_remove = QPushButton("Eliminar vértice")
         btn_remove.clicked.connect(self._remove_vertex)

         self.form.addRow(self.vertex_table)
         self.form.addRow(btn_add)
         self.form.addRow(btn_remove)

         self._fields["vertex_table"] = self.vertex_table

        elif kind == "Spline (helix)":
            sr = QDoubleSpinBox(); sr.setRange(0.001, 1e3); sr.setValue(0.5)
            sh = QDoubleSpinBox(); sh.setRange(0.001, 1e3); sh.setValue(1.0); sh.setSuffix(" m/turn")
            st = QSpinBox(); st.setRange(1, 200); st.setValue(5)
            self.form.addRow("Radio:", sr); self.form.addRow("Paso:", sh); self.form.addRow("Vueltas:", st)
            self._fields = dict(radius=sr, pitch=sh, turns=st)
        self.form.addRow("Corriente:", self.sp_current)
        self.form.addRow("Segmentos:", self.sp_disc)

    def build_wire(self) -> Wire:
        kind = self.cb_kind.currentText()
        f = self._fields
        if kind == "Line":
            geom = Line(start=np.array([s.value() for s in f["start"]]),
                        end=np.array([s.value() for s in f["end"]]))
        elif kind == "Loop":
            geom = Loop(center=np.array([s.value() for s in f["center"]]),
                        normal=np.array([s.value() for s in f["normal"]]),
                        radius=f["radius"].value())
        elif kind == "Arc":
            geom = Arc(center=np.array([s.value() for s in f["center"]]),
                       normal=np.array([s.value() for s in f["normal"]]),
                       radius=f["radius"].value(),
                       start_angle=f["start_angle"].value(),
                       end_angle=f["end_angle"].value())
        elif kind == "Polygon":

         table = f["vertex_table"]

         verts = []

         for row in range(table.rowCount()):

          x = float(table.item(row,0).text())
          y = float(table.item(row,1).text())
          z = float(table.item(row,2).text())

          verts.append([x,y,z])

         verts = np.array(verts)

         geom = Polygon(
            vertices=verts,
            closed=True
         )
        else:  # helix spline
            r = f["radius"].value(); pitch = f["pitch"].value(); n = f["turns"].value()
            t = np.linspace(0, 1, max(8, 8 * n))
            x = r * np.cos(2*np.pi*n*t); y = r * np.sin(2*np.pi*n*t); z = pitch*n*(t - 0.5)
            cp = np.stack([x, y, z], axis=1)
            geom = Spline(control_points=cp, closed=False, degree=3)
        return Wire(geometry=geom, current=self.sp_current.value(),
                    discretization=self.sp_disc.value())