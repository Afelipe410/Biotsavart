from dataclasses import dataclass
import numpy as np
import uuid

@dataclass
class Charge:
    """
    Representa una carga puntual en el simulador.
    Almacena propiedades físicas como posición, carga eléctrica (q), masa y velocidad.
    """
    position: np.ndarray
    q: float
    mass: float = 1.0
    velocity: np.ndarray = None
    id: str = ""

    def __post_init__(self):
        """
        Método de inicialización posterior. 
        Asegura que los vectores de posición y velocidad sean arreglos de NumPy (flotantes),
        y genera un identificador único (UUID) si no se provee uno.
        """
        self.position = np.array(
            self.position,
            dtype=float
        )
        if self.velocity is None:
            # Si no hay velocidad inicial, se asume que está en reposo
            self.velocity = np.zeros(
                3,
                dtype=float
            )
        else:
            self.velocity = np.array(
                self.velocity,
                dtype=float
            )
        if not self.id:
            # Asignar un identificador único para poder rastrear esta carga en la interfaz
            self.id = str(uuid.uuid4())

    def update(self, force, dt):
        """
        Actualiza la posición y velocidad de la carga basado en la fuerza aplicada.
        Utiliza el método de Euler para la integración numérica, pero asegurando
        la conservación de la energía (la rapidez se mantiene constante),
        ya que el campo magnético solo cambia la dirección del movimiento, no la magnitud.
        
        Args:
            force (np.ndarray): Vector de fuerza 3D (por ejemplo, fuerza de Lorentz).
            dt (float): Diferencial de tiempo (tamaño del paso de simulación).
        """
        # Calcular la rapidez (magnitud de la velocidad) inicial
        initial_speed = np.linalg.norm(self.velocity)
        if initial_speed == 0:
            return # Si está completamente quieta, no hay fuerza magnética (F=qv x B=0)
            
        # Segunda ley de Newton: a = F / m
        a = force / self.mass
        
        # Actualizar la velocidad usando aceleración (Método de Euler hacia adelante)
        self.velocity += a * dt
        
        # La fuerza magnética no hace trabajo, por lo tanto la energía cinética no debe cambiar.
        # Ajustamos el vector de la nueva velocidad para que tenga exactamente la misma rapidez que al inicio.
        new_speed = np.linalg.norm(self.velocity)
        if new_speed > 0:
            self.velocity = (self.velocity / new_speed) * initial_speed
            
        # Actualizar la posición de acuerdo a la velocidad corregida
        self.position += self.velocity * dt