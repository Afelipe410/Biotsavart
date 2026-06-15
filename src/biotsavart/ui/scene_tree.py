from __future__ import annotations
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QTreeWidget, QTreeWidgetItem

from ..scene import Scene


class SceneTree(QTreeWidget):
    wire_selected = pyqtSignal(str)  # wire id

    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.setHeaderLabels(["Escena"])
        self.setRootIsDecorated(True)
        self.itemSelectionChanged.connect(self._on_select)

        scene.wires_changed.connect(self.refresh)
        scene.current_changed.connect(self.refresh)
        self.refresh()

    def refresh(self):
        self.blockSignals(True)
        self.clear()
        root_wires = QTreeWidgetItem(self, ["Cables"])
        for i, w in enumerate(self.scene.wires):
            label = w.label or f"{type(w.geometry).__name__} #{i+1}"
            txt = f"{label} · I={w.current:.3g} A"
            it = QTreeWidgetItem(root_wires, [txt])
            it.setData(0, 0x0100, w.id)  # UserRole
        root_wires.setExpanded(True)
        self.blockSignals(False)

    def _on_select(self):
        items = self.selectedItems()
        if not items: return
        wid = items[0].data(0, 0x0100)
        if wid: self.wire_selected.emit(wid)
