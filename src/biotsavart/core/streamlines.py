from __future__ import annotations
import numpy as np
from scipy.interpolate import RegularGridInterpolator


def build_interpolator(B_grid: np.ndarray, grid):
    """
    Construye una función interpoladora espacial para el campo magnético.
    
    Args:
        B_grid: Arreglo 4D [Nx, Ny, Nz, 3] con los vectores de campo precalculados en la malla.
        grid: Objeto CartesianGrid que define las coordenadas espaciales.
        
    Retorna:
        Una función (callable) que toma una posición [x, y, z] y devuelve el vector B interpolado en ese punto.
    """
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
    """
    Calcula la trayectoria de una línea de campo magnético usando integración de Runge-Kutta de 4to orden (RK4).
    El campo magnético se normaliza para garantizar pasos espaciales constantes a lo largo del arco.
    
    Args:
        seed: Posición inicial (semilla) para comenzar a trazar la línea.
        B_interp: Función interpoladora del campo magnético (generada por build_interpolator).
        step: Tamaño del paso de integración en metros.
        max_steps: Número máximo de pasos para evitar bucles infinitos.
        both_dirs: Si es True, integra tanto hacia adelante como hacia atrás desde la semilla.
        min_speed: Tolerancia para evitar integración en zonas de campo cero.
        
    Retorna:
        Un arreglo bidimensional con las posiciones [P, 3] que forman la línea de campo.
    """
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
