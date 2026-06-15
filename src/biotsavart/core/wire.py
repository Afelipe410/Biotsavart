from __future__ import annotations
from dataclasses import dataclass, field
from uuid import uuid4
import numpy as np
from .geometry import GeometryPrimitive, deserialize as geom_deserialize


@dataclass
class Wire:
    geometry: GeometryPrimitive
    current: float = 1.0
    discretization: int = 200
    id: str = field(default_factory=lambda: str(uuid4()))
    label: str = ""

    def sample(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return (midpoints[N,3], dl[N,3], path[N+1,3])."""
        path = self.geometry.sample(self.discretization)
        dl = np.diff(path, axis=0)
        mid = 0.5 * (path[:-1] + path[1:])
        return mid, dl, path

    def serialize(self) -> dict:
        return {"id": self.id, "label": self.label, "current": self.current,
                "discretization": self.discretization,
                "geometry": self.geometry.serialize()}

    @classmethod
    def from_dict(cls, d: dict) -> "Wire":
        return cls(
            geometry=geom_deserialize(d["geometry"]),
            current=d.get("current", 1.0),
            discretization=d.get("discretization", 200),
            id=d.get("id", str(uuid4())),
            label=d.get("label", ""),
        )
