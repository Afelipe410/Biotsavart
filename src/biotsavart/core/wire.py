from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
import numpy as np
from .geometry import GeometryPrimitive, deserialize as geom_deserialize


@dataclass
class Wire:
    """
    Representa un conductor eléctrico en la escena.
    Contiene la geometría que le da forma, la corriente que fluye por él
    y la cantidad de segmentos en los que se debe discretizar para los cálculos numéricos.
    """
    geometry: GeometryPrimitive
    current: float = 1.0
    discretization: int = 200
    id: str = field(default_factory=lambda: str(uuid4()))
    label: str = ""

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())

    def sample(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Discretiza el conductor en múltiples segmentos rectos.
        
        Retorna:
            midpoints: Arreglo [N,3] con los centros de cada segmento.
            dl: Arreglo [N,3] con el vector director de cada segmento (diferencial de longitud).
            path: Arreglo [N+1,3] con los vértices de los segmentos a lo largo del cable.
        """
        path = self.geometry.sample(self.discretization)
        dl = np.diff(path, axis=0)
        mid = 0.5 * (path[:-1] + path[1:])
        return mid, dl, path

    def serialize(self) -> dict:
        """Convierte el objeto Wire a un diccionario (serialización JSON)."""
        return {"id": self.id, "label": self.label, "current": self.current,
                "discretization": self.discretization,
                "geometry": self.geometry.serialize()}

    @classmethod
    def from_dict(cls, d: dict) -> "Wire":
        """Reconstruye un objeto Wire a partir de un diccionario serializado."""
        return cls(
            geometry=geom_deserialize(d["geometry"]),
            current=d.get("current", 1.0),
            discretization=d.get("discretization", 200),
            id=d.get("id", str(uuid4())),
            label=d.get("label", ""),
        )
