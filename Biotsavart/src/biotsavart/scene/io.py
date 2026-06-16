from __future__ import annotations
import json
from pathlib import Path
import numpy as np

from ..core import Charge
from ..core import Wire, CartesianGrid, PRESETS
from .scene import Scene, DisplaySettings


def save_scene(scene: Scene, path: str | Path) -> None:
    data = {
        "charges": [
        {
        "id": c.id,
        "position": c.position.tolist(),
        "q": c.q,
        "mass": c.mass,
        "velocity": c.velocity.tolist()
        }
        for c in scene.charges
    ],
        "wires": [w.serialize() for w in scene.wires],
        "grid": {"origin": list(scene.grid.origin),
                 "spacing": scene.grid.spacing,
                 "dims": list(scene.grid.dims)},
        "material": _material_key(scene.material),
        "display": scene.display.__dict__,
    }
    Path(path).write_text(json.dumps(data, indent=2))


def load_scene(path: str | Path) -> Scene:
    data = json.loads(Path(path).read_text())
    s = Scene()
    s.wires = [Wire.from_dict(d) for d in data.get("wires", [])]
    g = data.get("grid", {})
    if g:
        s.grid = CartesianGrid(origin=np.array(g["origin"]),
                               spacing=g["spacing"],
                               dims=tuple(g["dims"]))
    for c in data.get("charges", []):
     s.charges.append(
        Charge(
            position=np.array(c["position"]),
            q=c["q"],
            mass=c["mass"],
            velocity=np.array(c.get("velocity", [0.0, 0.0, 0.0])),
            id=c["id"]
        )
    )
    s.material = PRESETS.get(data.get("material", "vacuum"), PRESETS["vacuum"])
    disp = data.get("display", {})
    s.display = DisplaySettings(**{k: v for k, v in disp.items()
                                   if k in DisplaySettings.__dataclass_fields__})
    return s


def _material_key(mat) -> str:
    for k, v in PRESETS.items():
        if v == mat: return k
    return "vacuum"
