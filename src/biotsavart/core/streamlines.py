from __future__ import annotations
import numpy as np
from scipy.interpolate import RegularGridInterpolator


def build_interpolator(B_grid: np.ndarray, grid):
    """B_grid: [Nx,Ny,Nz,3]; grid: CartesianGrid. Returns callable pos[3]->B[3]."""
    xs, ys, zs = grid.axes()
    interps = [RegularGridInterpolator((xs, ys, zs), B_grid[..., d],
                                       method="linear",
                                       bounds_error=False, fill_value=0.0)
               for d in range(3)]
    def f(pos: np.ndarray) -> np.ndarray:
        pos = np.atleast_2d(pos)
        return np.stack([i(pos) for i in interps], axis=-1).reshape(pos.shape)
    return f


def rk4_streamline(seed: np.ndarray, B_interp, step: float = 0.05,
                   max_steps: int = 2000, both_dirs: bool = True,
                   min_speed: float = 1e-12) -> np.ndarray:
    """Integrate a field line via RK4 with normalized B (constant arc step)."""
    def integrate(direction: float):
        pos = np.asarray(seed, dtype=float).copy()
        out = [pos.copy()]
        for _ in range(max_steps):
            def nB(p):
                v = B_interp(p).ravel()
                m = np.linalg.norm(v)
                return v / m if m > min_speed else None
            k1 = nB(pos)
            if k1 is None: break
            k2 = nB(pos + 0.5 * step * direction * k1)
            if k2 is None: break
            k3 = nB(pos + 0.5 * step * direction * k2)
            if k3 is None: break
            k4 = nB(pos + step * direction * k3)
            if k4 is None: break
            pos = pos + (step * direction / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
            out.append(pos.copy())
        return np.array(out)

    fwd = integrate(+1.0)
    if not both_dirs:
        return fwd
    bwd = integrate(-1.0)
    return np.vstack([bwd[::-1], fwd[1:]]) if len(bwd) > 1 else fwd
