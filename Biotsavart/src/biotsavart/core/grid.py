from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class CartesianGrid:
    """
    Define una cuadrícula cartesiana 3D para evaluar el campo magnético.
    """
    origin: np.ndarray = field(default_factory=lambda: np.array([-1.0, -1.0, -1.0]))
    spacing: float = 0.05
    dims: tuple[int, int, int] = (40, 40, 40)

    def __post_init__(self):
        self.origin = np.asarray(self.origin, dtype=np.float64)

    @classmethod
    def centered(cls, half_extent: float, n: int) -> "CartesianGrid":
        """
        Crea una cuadrícula cúbica centrada en el origen (0,0,0).
        
        Args:
            half_extent: Distancia desde el centro a los bordes.
            n: Número de puntos a lo largo de cada eje.
        """
        return cls(origin=np.array([-half_extent]*3),
                   spacing=2*half_extent/(n-1),
                   dims=(n, n, n))

    @property
    def shape(self) -> tuple[int, int, int]:
        """Devuelve las dimensiones de la cuadrícula (nx, ny, nz)."""
        return self.dims

    @property
    def n_points(self) -> int:
        """Devuelve el número total de puntos en la cuadrícula."""
        return int(np.prod(self.dims))

    def axes(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Devuelve los tres arreglos unidimensionales (x, y, z) que definen 
        los ejes de la cuadrícula.
        """
        nx, ny, nz = self.dims
        ox, oy, oz = self.origin
        s = self.spacing
        return (np.linspace(ox, ox + s*(nx-1), nx),
                np.linspace(oy, oy + s*(ny-1), ny),
                np.linspace(oz, oz + s*(nz-1), nz))

    def points(self) -> np.ndarray:
        """
        Devuelve un arreglo [Nx*Ny*Nz, 3] con las coordenadas de cada punto en el espacio.
        (Orden indexing='ij', lo que coincide con VTK al remodelar matrices).
        """
        xs, ys, zs = self.axes()
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        return np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
