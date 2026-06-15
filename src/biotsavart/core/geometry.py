from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import numpy as np
from scipy.interpolate import splprep, splev


class GeometryPrimitive(ABC):
    closed: bool = False

    @abstractmethod
    def sample(self, n: int) -> np.ndarray:
        """Return [n+1, 3] points along the curve (n segments)."""

    def serialize(self) -> dict:
        return {"type": type(self).__name__, **self._payload()}

    def _payload(self) -> dict:
        return {}


@dataclass
class Line(GeometryPrimitive):
    start: np.ndarray = field(default_factory=lambda: np.zeros(3))
    end: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0]))
    closed: bool = False

    def sample(self, n: int) -> np.ndarray:
        t = np.linspace(0.0, 1.0, n + 1)[:, None]
        return (1 - t) * np.asarray(self.start) + t * np.asarray(self.end)

    def _payload(self):
        return {"start": list(self.start), "end": list(self.end)}


@dataclass
class Arc(GeometryPrimitive):
    """Arc of a circle in a plane defined by `normal`, centered at `center`."""
    center: np.ndarray = field(default_factory=lambda: np.zeros(3))
    radius: float = 1.0
    normal: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 1.0]))
    start_angle: float = 0.0
    end_angle: float = 2 * np.pi
    closed: bool = False

    def sample(self, n: int) -> np.ndarray:
        n_hat = np.asarray(self.normal, dtype=float)
        n_hat = n_hat / np.linalg.norm(n_hat)
        # build orthonormal basis in plane
        a = np.array([1.0, 0.0, 0.0]) if abs(n_hat[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
        u = np.cross(n_hat, a); u /= np.linalg.norm(u)
        v = np.cross(n_hat, u)
        theta = np.linspace(self.start_angle, self.end_angle, n + 1)
        pts = (np.asarray(self.center)
               + self.radius * (np.cos(theta)[:, None] * u + np.sin(theta)[:, None] * v))
        return pts

    def _payload(self):
        return {"center": list(self.center), "radius": self.radius,
                "normal": list(self.normal),
                "start_angle": self.start_angle, "end_angle": self.end_angle}


@dataclass
class Loop(GeometryPrimitive):
    """Closed circular loop — Arc 0→2π with closed=True."""
    center: np.ndarray = field(default_factory=lambda: np.zeros(3))
    radius: float = 1.0
    normal: np.ndarray = field(default_factory=lambda: np.array([0.0, 0.0, 1.0]))
    closed: bool = True

    def sample(self, n: int) -> np.ndarray:
        arc = Arc(center=self.center, radius=self.radius, normal=self.normal,
                  start_angle=0.0, end_angle=2*np.pi)
        pts = arc.sample(n)
        pts[-1] = pts[0]  # ensure exact closure
        return pts

    def _payload(self):
        return {"center": list(self.center), "radius": self.radius,
                "normal": list(self.normal)}


@dataclass
class Polygon(GeometryPrimitive):
    vertices: np.ndarray = field(default_factory=lambda: np.zeros((3, 3)))
    closed: bool = True

    def sample(self, n: int) -> np.ndarray:
        verts = np.asarray(self.vertices, dtype=float)
        if self.closed:
            verts = np.vstack([verts, verts[0]])
        seg = np.linalg.norm(np.diff(verts, axis=0), axis=1)
        total = float(seg.sum())
        # distribute n segments across edges proportional to length; ensure corners kept
        per_edge = np.maximum(1, np.round(n * seg / total).astype(int))
        # adjust to hit exactly n total segments
        diff = n - int(per_edge.sum())
        while diff != 0:
            idx = int(np.argmax(seg / per_edge)) if diff > 0 else int(np.argmin(seg / np.maximum(per_edge - 1, 1)))
            per_edge[idx] += 1 if diff > 0 else -1
            per_edge[idx] = max(per_edge[idx], 1)
            diff = n - int(per_edge.sum())
        pieces = []
        for i, ne in enumerate(per_edge):
            t = np.linspace(0.0, 1.0, ne + 1)[:-1, None]
            pieces.append((1 - t) * verts[i] + t * verts[i + 1])
        pieces.append(verts[-1:])
        return np.vstack(pieces)

    def _payload(self):
        return {"vertices": [list(v) for v in self.vertices], "closed": self.closed}


@dataclass
class Spline(GeometryPrimitive):
    """Cubic B-spline through control_points, uniform arc-length sampling."""
    control_points: np.ndarray = field(default_factory=lambda: np.zeros((4, 3)))
    closed: bool = False
    degree: int = 3

    def sample(self, n: int) -> np.ndarray:
        pts = np.asarray(self.control_points, dtype=float)
        k = min(self.degree, len(pts) - 1)
        if k < 1:
            return Line(start=pts[0], end=pts[-1]).sample(n)
        per = 1 if self.closed else 0
        tck, _ = splprep([pts[:, 0], pts[:, 1], pts[:, 2]], s=0.0, k=k, per=per)
        # arc-length reparametrization
        u_fine = np.linspace(0.0, 1.0, 1000)
        x, y, z = splev(u_fine, tck)
        d = np.cumsum(np.sqrt(np.diff(x)**2 + np.diff(y)**2 + np.diff(z)**2))
        d = np.concatenate([[0.0], d])
        target = np.linspace(0.0, d[-1], n + 1)
        u_arc = np.interp(target, d, u_fine)
        xs, ys, zs = splev(u_arc, tck)
        out = np.stack([xs, ys, zs], axis=1)
        if self.closed:
            out[-1] = out[0]
        return out

    def _payload(self):
        return {"control_points": [list(p) for p in self.control_points],
                "closed": self.closed, "degree": self.degree}


GEOMETRY_REGISTRY = {
    "Line": Line, "Arc": Arc, "Loop": Loop, "Polygon": Polygon, "Spline": Spline,
}


def deserialize(d: dict) -> GeometryPrimitive:
    cls = GEOMETRY_REGISTRY[d["type"]]
    payload = {k: v for k, v in d.items() if k != "type"}
    for key in ("start", "end", "center", "normal"):
        if key in payload:
            payload[key] = np.array(payload[key])
    if "vertices" in payload:
        payload["vertices"] = np.array(payload["vertices"])
    if "control_points" in payload:
        payload["control_points"] = np.array(payload["control_points"])
    return cls(**payload)
