from __future__ import annotations
import numpy as np

try:
    from numba import njit, prange
    _HAS_NUMBA = True
except ImportError:
    _HAS_NUMBA = False
    def njit(*a, **k):
        def deco(f): return f
        return deco
    prange = range

MU0 = 4e-7 * np.pi  # vacuum permeability [T·m/A]


@njit(parallel=True, fastmath=True, cache=True)
def _kernel(M, DL, I, R, eps2):
    """
    Núcleo del cálculo de Biot-Savart sin estado (excluyendo el factor μ₀/(4π)).
    Usa Numba para paralelización y optimización matemática agresiva.
    
    Args:
        M: Matriz [N,3] con los puntos medios de cada segmento del cable.
        DL: Matriz [N,3] con los vectores directores de cada segmento.
        I: Arreglo [N] con las corrientes en cada segmento.
        R: Matriz [P,3] con los puntos del espacio donde evaluar el campo.
        eps2: Parámetro de suavizado al cuadrado (evita singularidades).
        
    Retorna:
        Arreglo [P,3] con el vector de campo magnético bruto.
    """
    P = R.shape[0]
    N = M.shape[0]
    B = np.zeros((P, 3))
    for p in prange(P):
        bx = 0.0; by = 0.0; bz = 0.0
        rx = R[p, 0]; ry = R[p, 1]; rz = R[p, 2]
        for i in range(N):
            dx = rx - M[i, 0]; dy = ry - M[i, 1]; dz = rz - M[i, 2]
            r2 = dx*dx + dy*dy + dz*dz + eps2
            inv = 1.0 / (r2 * np.sqrt(r2))
            cx = DL[i, 1]*dz - DL[i, 2]*dy
            cy = DL[i, 2]*dx - DL[i, 0]*dz
            cz = DL[i, 0]*dy - DL[i, 1]*dx
            k = I[i] * inv
            bx += k*cx; by += k*cy; bz += k*cz
        B[p, 0] = bx; B[p, 1] = by; B[p, 2] = bz
    return B


def assemble(wires) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Ensambla y concatena los puntos medios, vectores de longitud y corrientes de una lista de cables.
    Prepara los datos para introducirlos en el kernel matemático optimizado.
    """
    Ms, DLs, Is = [], [], []
    for w in wires:
        m, dl, _ = w.sample()
        Ms.append(m); DLs.append(dl); Is.append(np.full(len(m), w.current))
    if not Ms:
        return (np.zeros((0, 3)), np.zeros((0, 3)), np.zeros(0))
    return np.vstack(Ms), np.vstack(DLs), np.concatenate(Is)


def compute_B(wires, points: np.ndarray, mu_r: float = 1.0,
              eps: float | None = None) -> np.ndarray:
    """
    Calcula el campo magnético B en un conjunto de puntos de evaluación.
    
    Args:
        wires: Lista de objetos Wire (conductores).
        points: Arreglo [P,3] de puntos en el espacio.
        mu_r: Permeabilidad magnética relativa del medio.
        eps: Longitud de suavizado en metros. Si es None, toma 1/4 de la longitud promedio de segmento.
        
    Retorna:
        Arreglo [P,3] de los vectores de campo magnético en Teslas.
    """
    M, DL, I = assemble(wires)
    if M.shape[0] == 0:
        return np.zeros_like(points)
    if eps is None:
        seg_len = np.linalg.norm(DL, axis=1).mean()
        eps = seg_len * 0.25
    B = _kernel(M.astype(np.float64), DL.astype(np.float64),
                I.astype(np.float64), points.astype(np.float64), eps*eps)
    return (MU0 * mu_r / (4.0 * np.pi)) * B


def compute_B_on_grid(wires, grid, mu_r: float = 1.0,
                      eps: float | None = None) -> np.ndarray:
    """
    Método de conveniencia: calcula el campo en una malla y lo remodela a las dimensiones [Nx,Ny,Nz,3].
    """
    pts = grid.points()
    B = compute_B(wires, pts, mu_r=mu_r, eps=eps)
    return B.reshape(*grid.dims, 3)

import numpy as np

def lorentz_force(q, velocity, B):
    """
    Calcula la fuerza de Lorentz (magnética) sobre una carga puntual.
    F = q(v x B)
    """
    return q * np.cross(
        velocity,
        B
    )
def field_at_point(scene, point):
    """
    Calcula el vector de campo magnético en un único punto del espacio,
    tomando en cuenta todos los cables de la escena actual.
    """
    if len(scene.wires) == 0:

        return np.zeros(3)

    point_array = np.array(
        [point],
        dtype=float
    )

    B = compute_B(
        scene.wires,
        point_array,
        mu_r=scene.material.mu_r
    )

    return B[0]