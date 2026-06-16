import sys
import os
import numpy as np

# Ensure the module can be imported
sys.path.insert(0, r"c:\Users\Lenovo\OneDrive\Escritorio\BiotSavart1\src")

from biotsavart.core import Wire, Loop, Charge, Line
from biotsavart.scene import Scene
from biotsavart.scene.io import save_scene

scene = Scene()

# 1. Botella Magnética (Magnetic Bottle) - Dos bobinas separadas con la misma corriente
# Esto crea un campo magnético que es más fuerte en los extremos y atrapa las cargas en el medio
scene.add_wire(Wire(geometry=Loop(center=np.array([0, 0, 1.5]), radius=1.5), current=25.0, discretization=150, label="Bobina Superior"))
scene.add_wire(Wire(geometry=Loop(center=np.array([0, 0, -1.5]), radius=1.5), current=25.0, discretization=150, label="Bobina Inferior"))

# 2. Cargas interactivas de prueba
# Esta carga estará rebotando dentro de la botella magnética (efecto espejo magnético)
scene.add_charge(Charge(position=np.array([0.5, 0.0, 0.0]), velocity=np.array([3.0, 3.0, 1.0]), q=5e-6, mass=1e-11))

# Una segunda carga con velocidad distinta
scene.add_charge(Charge(position=np.array([-0.5, 0.0, 0.0]), velocity=np.array([-2.0, -2.0, -0.5]), q=-3e-6, mass=1e-11))

# 3. Guardar el resultado
save_path = r"c:\Users\Lenovo\OneDrive\Escritorio\BiotSavart1\BotellaMagnetica_Prueba.json"
save_scene(scene, save_path)
print(f"Escena guardada en: {save_path}")
