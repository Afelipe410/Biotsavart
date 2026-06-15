from __future__ import annotations
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt6.QtWidgets import QWidget, QVBoxLayout

from ..scene import Scene
from PyQt6.QtCore import QTimer
from ..core.biot_savart import (
    lorentz_force,
    field_at_point
)
class Viewport(QWidget):
    """Embedded PyVista viewport; rebuilds actors from Scene + B field."""

    def __init__(self, scene: Scene, parent=None):
        super().__init__(parent)
        self.scene = scene
        self.plotter = QtInteractor(self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plotter.interactor)
        self._actors: dict[str, object] = {}
        self._B: np.ndarray | None = None
        self._scale: float = 1.0  # multiplier applied at draw time (current-only changes)

        self.plotter.set_background("white")
        self.plotter.add_axes()
        self.plotter.show_grid(color="gray", font_size=10)
        self.timer = QTimer()

        self.timer.timeout.connect(
        self._update_charges
          )
        self.timer.start(16)
    

    # --- public API ---
    def set_field(self, B: np.ndarray, scale: float = 1.0) -> None:
        """B [Nx,Ny,Nz,3] in Tesla. scale lets us multiply at render time."""
        self._B = B
        self._scale = scale
        self.refresh()

    def set_scale(self, scale: float) -> None:
        self._scale = scale
        self.refresh()

    def set_theme_mode(self, is_dark: bool) -> None:
        if is_dark:
            self.plotter.set_background("#1e1e1e")
        else:
            self.plotter.set_background("white")
        # Ensure grid stays visible
        self.plotter.show_grid(color="gray", font_size=10)

    # --- internal ---
    def _clear(self):
        for key, a in list(self._actors.items()):
            try:
                self.plotter.remove_actor(a, render=False)
            except Exception:
                pass
        self._actors.clear()

    def refresh(self) -> None:
        self._clear()
        d = self.scene.display

        if d.show_wires:
            self._draw_wires()
        if getattr(d, 'show_charges', True):
            self._draw_charges()

        if self._B is None:
            self.plotter.render()
            return

        grid_pv = self._build_imagedata()

        if d.show_arrows:
            self._draw_arrows(grid_pv)
        if d.show_streamlines:
            self._draw_streamlines(grid_pv)
        if d.show_isosurfaces:
            self._draw_isosurfaces(grid_pv)

        self.plotter.render()

    def _build_imagedata(self):
        g = self.scene.grid
        grid_pv = pv.ImageData(dimensions=g.dims,
                               spacing=(g.spacing, g.spacing, g.spacing),
                               origin=tuple(g.origin))
        B_scaled = self._B * self._scale
        # ImageData uses Fortran ordering of point_data. Our B is [Nx,Ny,Nz,3]
        # in 'ij' meshgrid order which matches VTK ImageData when reshaped:
        flat = B_scaled.reshape(-1, 3, order="F")
        mag = np.linalg.norm(flat, axis=1)
        grid_pv["B"] = flat
        grid_pv["|B|"] = mag
        grid_pv.set_active_vectors("B")
        grid_pv.set_active_scalars("|B|")
        return grid_pv

    def _draw_wires(self):
        for w in self.scene.wires:
            pts = w.geometry.sample(max(60, w.discretization // 2))
            if len(pts) < 2: continue
            line = pv.lines_from_points(pts, close=getattr(w.geometry, "closed", False))
            radius = 0.02 * max(1.0, abs(w.current) ** 0.25)
            tube = line.tube(radius=radius, n_sides=12)
            color = "#cc7a3a" if w.current >= 0 else "#3a8acc"
            a = self.plotter.add_mesh(tube, color=color, smooth_shading=True,
                                      name=f"wire_{w.id}")
            self._actors[f"wire_{w.id}"] = a

    def _draw_charges(self):
        for c in self.scene.charges:
            sphere = pv.Sphere(radius=0.06, center=(0, 0, 0))
            color = "red" if c.q > 0 else "blue"
            actor = self.plotter.add_mesh(
                sphere,
                color=color,
                smooth_shading=True
            )
            actor.position = tuple(c.position)
            self._actors[f"charge_{c.id}"] = actor

    def _draw_arrows(self, grid_pv):
        material = self.scene.material.name
        if "Vacío" in material:
          cmap = "viridis"

        elif "Aire" in material:
          cmap = "cool"

        elif "Aluminio" in material:
          cmap = "Blues"

        elif "Cobre" in material:
           cmap = "Oranges"

        elif "Ferrita" in material:
          cmap = "Purples"

        elif "Hierro" in material:
          cmap = "autumn"

        elif "Acero" in material:
          cmap = "Greys"

        elif "Superconductor" in material:
          cmap = "Greens"

        else:
          cmap = "turbo"
        d = self.scene.display
        mag = grid_pv["|B|"]
        if mag.max() <= 0: return
        glyphs = grid_pv.glyph(orient="B", scale="|B|",
                               factor=d.glyph_factor / max(mag.max(), 1e-30),
                               tolerance=d.glyph_tolerance)
        a = self.plotter.add_mesh(glyphs, scalars="|B|", cmap= cmap,
                                  log_scale=d.log_scale,
                                  scalar_bar_args={"title": "|B| [T]"},
                                  name="arrows")
        self._actors["arrows"] = a
        print("Material:", self.scene.material.name)
        print("mu_r:", self.scene.material.mu_r)
        print("B max:", mag.max())

    def _draw_streamlines(self, grid_pv):
        d = self.scene.display
        # seeds: rings around each wire
        seeds_pts = []
        for w in self.scene.wires:
            mid, dl, path = w.sample()
            if len(mid) == 0: continue
            # pick a handful of midpoints, offset radially in a plane perpendicular to dl
            idxs = np.linspace(0, len(mid) - 1, d.streamline_seeds).astype(int)
            for i in idxs:
                t = dl[i] / max(np.linalg.norm(dl[i]), 1e-12)
                a = np.array([1.0, 0.0, 0.0]) if abs(t[0]) < 0.9 else np.array([0.0, 1.0, 0.0])
                u = np.cross(t, a); u /= max(np.linalg.norm(u), 1e-12)
                v = np.cross(t, u)
                r = self.scene.grid.spacing * 3
                for ang in np.linspace(0, 2*np.pi, 6, endpoint=False):
                    seeds_pts.append(mid[i] + r*(np.cos(ang)*u + np.sin(ang)*v))
        if not seeds_pts:
            return
        seeds = pv.PolyData(np.array(seeds_pts))
        stream = grid_pv.streamlines_from_source(
            seeds, vectors="B",
            integration_direction="both",
            max_steps=2000,
            initial_step_length=self.scene.grid.spacing,
            terminal_speed=1e-20,
        )
        if stream.n_points == 0:
            return
        if "|B|" not in stream.array_names:
            if "B" in stream.array_names:
                stream["|B|"] = np.linalg.norm(stream["B"], axis=1)
            else:
                stream["|B|"] = np.zeros(stream.n_points)
        
        stream.set_active_scalars("|B|")
        tubes = stream.tube(radius=self.scene.grid.spacing * 0.15)
        if tubes.n_points == 0:
            return
        a = self.plotter.add_mesh(tubes, scalars="|B|", cmap="plasma",
                                  log_scale=self.scene.display.log_scale,
                                  show_scalar_bar=False, name="streamlines")
        self._actors["streamlines"] = a

    def _draw_isosurfaces(self, grid_pv):
        d = self.scene.display
        mag = grid_pv["|B|"]
        m_max = float(mag.max())
        if m_max <= 0: return
        # log-spaced isovalues
        levels = np.geomspace(m_max * 1e-3, m_max * 0.5, d.iso_count)
        iso = grid_pv.contour(isosurfaces=levels.tolist(), scalars="|B|")
        if iso.n_points == 0: return
        a = self.plotter.add_mesh(iso, scalars="|B|", cmap="inferno",
                                  opacity=0.25, show_scalar_bar=False,
                                  name="iso")
        self._actors["iso"] = a

    def reset_camera(self):
        self.plotter.reset_camera()

    def close_plotter(self):
        self.plotter.close()

    def _update_charges(self):
        """Update charge positions based on Lorentz force. Only refresh if charges exist."""
        if not self.scene.charges or len(self.scene.charges) == 0:
            return  # No charges, skip update
        
        # Cache wire segments once per frame to avoid recalculating per charge
        from ..core.biot_savart import assemble, _kernel, MU0
        M, DL, I = assemble(self.scene.wires)
        has_wires = M.shape[0] > 0
        
        if has_wires:
            mu_r = self.scene.material.mu_r
            eps = np.linalg.norm(DL, axis=1).mean() * 0.25
            eps2 = eps * eps
        else:
            B_zero = np.zeros(3)
        
        dt = 0.003
        for c in self.scene.charges:
            if has_wires:
                point_array = np.array([c.position], dtype=float)
                B_raw = _kernel(M.astype(np.float64), DL.astype(np.float64), I.astype(np.float64), point_array, eps2)
                B = (MU0 * mu_r / (4.0 * np.pi)) * B_raw[0]
            else:
                B = B_zero

            F = lorentz_force(c.q, c.velocity, B)
            c.update(F, dt)
            limit = 5
            c.position = np.clip(c.position, -limit, limit)
            
            # Update the actor position directly without rebuilding scene
            actor_key = f"charge_{c.id}"
            if actor_key in self._actors:
                self._actors[actor_key].position = tuple(c.position)
        
        # Render the updated positions
        self.plotter.render()

    