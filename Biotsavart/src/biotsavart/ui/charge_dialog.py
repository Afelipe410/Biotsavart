from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QDialogButtonBox,
    QVBoxLayout,
    QComboBox,
    QLabel
)

class ChargeDialog(QDialog):
    """Modal to create a new point charge."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva carga puntual")
        self.setModal(True)
        self.resize(300, 200)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # Position spinboxes
        self.x = QDoubleSpinBox()
        self.y = QDoubleSpinBox()
        self.z = QDoubleSpinBox()
        
        for box in [self.x, self.y, self.z]:
            box.setRange(-100, 100)
            box.setDecimals(3)
            box.setSingleStep(0.1)
            box.setValue(0.0)

        # Velocity spinboxes
        self.vx = QDoubleSpinBox()
        self.vy = QDoubleSpinBox()
        self.vz = QDoubleSpinBox()

        for box in [self.vx, self.vy, self.vz]:
            box.setRange(-100, 100)
            box.setDecimals(3)
            box.setSingleStep(0.1)
            box.setValue(0.0)
        self.vx.setValue(0.5)  # Default initial velocity

        # Mass and Charge spinboxes
        self.mass = QDoubleSpinBox()
        self.mass.setRange(1e-15, 1000)
        self.mass.setDecimals(12)
        self.mass.setSingleStep(1e-11)
        self.mass.setValue(1e-10)  # Very small mass for visible movement

        self.charge_mag = QDoubleSpinBox()
        self.charge_mag.setRange(1e-9, 1000)
        self.charge_mag.setDecimals(6)
        self.charge_mag.setSingleStep(0.1)
        self.charge_mag.setValue(1.0)  # 1.0 microCoulombs default

        # Charge type selector
        self.charge_type = QComboBox()
        self.charge_type.addItems(["Positiva", "Negativa"])

        # Add to form
        form.addRow("X (m):", self.x)
        form.addRow("Y (m):", self.y)
        form.addRow("Z (m):", self.z)
        form.addRow("Vx (m/s):", self.vx)
        form.addRow("Vy (m/s):", self.vy)
        form.addRow("Vz (m/s):", self.vz)
        form.addRow("Masa (kg):", self.mass)
        form.addRow("Carga (μC):", self.charge_mag)
        form.addRow("Signo:", self.charge_type)
        
        layout.addLayout(form)

        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)