from __future__ import annotations
from dataclasses import dataclass, field
import numpy as np


@dataclass
class CartesianGrid:
    origin: np.ndarray = field(default_factory=lambda: np.array([-1.0, -1.0, -1.0]))
    spacing: float = 0.05
    dims: tuple[int, int, int] = (40, 40, 40)

    def __post_init__(self):
        self.origin = np.asarray(self.origin, dtype=np.float64)

    @classmethod
    def centered(cls, half_extent: float, n: int) -> "CartesianGrid":
        return cls(origin=np.array([-half_extent]*3),
                   spacing=2*half_extent/(n-1),
                   dims=(n, n, n))

    @property
    def shape(self) -> tuple[int, int, int]:
        return self.dims

    @property
    def n_points(self) -> int:
        return int(np.prod(self.dims))

    def axes(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nx, ny, nz = self.dims
        ox, oy, oz = self.origin
        s = self.spacing
        return (np.linspace(ox, ox + s*(nx-1), nx),
                np.linspace(oy, oy + s*(ny-1), ny),
                np.linspace(oz, oz + s*(nz-1), nz))

    def points(self) -> np.ndarray:
        """Returns [Nx*Ny*Nz, 3] in C order (z fastest? no — x,y,z meshgrid 'ij')."""
        xs, ys, zs = self.axes()
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        return np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
