"""
Módulo de estadísticas: Panel para mostrar información de campos magnéticos
y estadísticas de cálculo en tiempo real.
"""

from __future__ import annotations
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QGroupBox, QFormLayout, QLabel, QGridLayout, QWidget, QVBoxLayout


class StatisticsPanel(QGroupBox):
    """Panel que muestra estadísticas del campo magnético y cálculo.
    
    Información mostrada:
    - Número de conductores y segmentos totales
    - Rango y promedio de magnitud de campo
    - Tiempo de último cálculo
    - Uso de memoria estimado
    - Puntos de malla
    """
    
    def __init__(self, parent=None):
        super().__init__("Estadísticas", parent)
        
        self.layout = QFormLayout(self)
        self.layout.setSpacing(4)
        self.layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        
        # Conductores y segmentos
        self.lb_wires = QLabel("0")
        self.lb_segments = QLabel("0")
        self.layout.addRow("Cables:", self.lb_wires)
        self.layout.addRow("Segmentos total:", self.lb_segments)
        
        self.layout.addRow("", QWidget())  # Spacer
        
        # Información de malla
        self.lb_grid_points = QLabel("0")
        self.lb_grid_size = QLabel("—")
        self.layout.addRow("Puntos malla:", self.lb_grid_points)
        self.layout.addRow("Resolución:", self.lb_grid_size)
        
        self.layout.addRow("", QWidget())  # Spacer
        
        # Campo magnético
        self.lb_B_min = QLabel("—")
        self.lb_B_max = QLabel("—")
        self.lb_B_mean = QLabel("—")
        self.lb_B_std = QLabel("—")
        self.layout.addRow("B mín:", self.lb_B_min)
        self.layout.addRow("B máx:", self.lb_B_max)
        self.layout.addRow("B prom:", self.lb_B_mean)
        self.layout.addRow("B std:", self.lb_B_std)
        
        self.layout.addRow("", QWidget())  # Spacer
        
        # Cálculo
        self.lb_time = QLabel("—")
        self.lb_memory = QLabel("—")
        self.layout.addRow("Tiempo cálculo:", self.lb_time)
        self.layout.addRow("Mem. estimada:", self.lb_memory)
        
        self.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                padding-top: 1ex;
                color: #333;
            }
            QLabel {
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }
        """)
    
    def update_from_scene(self, scene, B_array=None, compute_time_ms=None):
        """Actualizar estadísticas desde la escena y resultado de cálculo.
        
        Args:
            scene: Scene object
            B_array: Array de campo magnético [P, 3] o None
            compute_time_ms: Tiempo de cálculo en milisegundos o None
        """
        # Conductores y segmentos
        n_wires = len(scene.wires)
        total_segments = sum(len(w.geometry.sample(w.discretization)) - 1 
                            for w in scene.wires)
        self.lb_wires.setText(str(n_wires))
        self.lb_segments.setText(str(total_segments))
        
        # Malla
        grid = scene.grid
        n_points = grid.n_points
        self.lb_grid_points.setText(f"{n_points:,}")
        self.lb_grid_size.setText(f"{grid.dims[0]}³ = {n_points:,}")
        
        # Estadísticas de campo
        if B_array is not None and B_array.size > 0:
            B_mag = np.linalg.norm(B_array, axis=-1)
            
            # Formato: número con unidades apropiadas
            def format_field(value):
                if value < 1e-9:
                    return f"{value*1e12:.2f} pT"
                elif value < 1e-6:
                    return f"{value*1e9:.2f} nT"
                elif value < 1e-3:
                    return f"{value*1e6:.2f} μT"
                elif value < 1.0:
                    return f"{value*1e3:.2f} mT"
                else:
                    return f"{value:.2f} T"
            
            B_min = np.min(B_mag)
            B_max = np.max(B_mag)
            B_mean = np.mean(B_mag)
            B_std = np.std(B_mag)
            
            self.lb_B_min.setText(format_field(B_min))
            self.lb_B_max.setText(format_field(B_max))
            self.lb_B_mean.setText(format_field(B_mean))
            self.lb_B_std.setText(format_field(B_std))
        else:
            self.lb_B_min.setText("—")
            self.lb_B_max.setText("—")
            self.lb_B_mean.setText("—")
            self.lb_B_std.setText("—")
        
        # Tiempo de cálculo
        if compute_time_ms is not None:
            if compute_time_ms < 1000:
                self.lb_time.setText(f"{compute_time_ms:.1f} ms")
            else:
                self.lb_time.setText(f"{compute_time_ms/1000:.2f} s")
        else:
            self.lb_time.setText("—")
        
        # Estimación de memoria
        if B_array is not None:
            # B_array [P, 3] float64 = 8 bytes * 3 * P
            mem_bytes = B_array.nbytes
            # Agregar overhead de Scene, Grid, etc. (~20%)
            mem_bytes_total = int(mem_bytes * 1.2)
            
            if mem_bytes_total < 1e6:
                self.lb_memory.setText(f"{mem_bytes_total/1e3:.1f} KB")
            elif mem_bytes_total < 1e9:
                self.lb_memory.setText(f"{mem_bytes_total/1e6:.1f} MB")
            else:
                self.lb_memory.setText(f"{mem_bytes_total/1e9:.2f} GB")
        else:
            self.lb_memory.setText("—")


class FieldRangeWidget(QWidget):
    """Widget para mostrar rango de magnitud de campo con barra visual."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Grid con información
        grid = QGridLayout()
        self.lb_min_val = QLabel("—")
        self.lb_max_val = QLabel("—")
        self.lb_range_val = QLabel("—")
        
        grid.addWidget(QLabel("Min:"), 0, 0)
        grid.addWidget(self.lb_min_val, 0, 1)
        grid.addWidget(QLabel("Max:"), 1, 0)
        grid.addWidget(self.lb_max_val, 1, 1)
        grid.addWidget(QLabel("Rango:"), 2, 0)
        grid.addWidget(self.lb_range_val, 2, 1)
        
        layout.addLayout(grid)
    
    def update(self, B_array):
        """Actualizar desde array de campo."""
        if B_array is not None and B_array.size > 0:
            B_mag = np.linalg.norm(B_array, axis=-1)
            B_min = np.min(B_mag)
            B_max = np.max(B_mag)
            B_range = B_max - B_min
            
            def format_field(value):
                if value < 1e-9:
                    return f"{value*1e12:.2f} pT"
                elif value < 1e-6:
                    return f"{value*1e9:.2f} nT"
                elif value < 1e-3:
                    return f"{value*1e6:.2f} μT"
                elif value < 1.0:
                    return f"{value*1e3:.2f} mT"
                else:
                    return f"{value:.2f} T"
            
            self.lb_min_val.setText(format_field(B_min))
            self.lb_max_val.setText(format_field(B_max))
            self.lb_range_val.setText(format_field(B_range))
        else:
            self.lb_min_val.setText("—")
            self.lb_max_val.setText("—")
            self.lb_range_val.setText("—")


def format_field_magnitude(value):
    """Formato automático de magnitud de campo.
    
    Convierte a unidades apropiadas (pT, nT, μT, mT, T).
    """
    if value < 1e-9:
        return f"{value*1e12:.2f} pT"
    elif value < 1e-6:
        return f"{value*1e9:.2f} nT"
    elif value < 1e-3:
        return f"{value*1e6:.2f} μT"
    elif value < 1.0:
        return f"{value*1e3:.2f} mT"
    else:
        return f"{value:.2f} T"

