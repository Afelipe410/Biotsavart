from dataclasses import dataclass
import numpy as np
import uuid

@dataclass
class Charge:

    position: np.ndarray
    q: float
    mass: float = 1.0
    velocity: np.ndarray = None
    id: str = ""

    def __post_init__(self):
     self.position = np.array(
        self.position,
        dtype=float
    )
     if self.velocity is None:
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
        self.id = str(uuid.uuid4())

    def update(self, force, dt):
     a = force / self.mass
     self.velocity += a * dt
     self.velocity *= 0.999
     max_speed = 3.0
     speed = np.linalg.norm(
        self.velocity
     )
     if speed > max_speed:
        self.velocity = (
            self.velocity / speed
        ) * max_speed
     self.position += self.velocity * dt