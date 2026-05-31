# Biot-Savart Magnetic Field Simulator

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Status: Active](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

Simulador interactivo 3D del campo magnético generado por conductores de geometría arbitraria usando la **ley de Biot-Savart**. Herramienta educativa y de investigación para visualizar y analizar campos magnéticos con precisión en tiempo real.

![Biot-Savart Simulator](https://img.shields.io/badge/Physics-Simulation-purple) ![3D Visualization](https://img.shields.io/badge/3D-Visualization-cyan) ![Scientific Computing](https://img.shields.io/badge/Scientific-Computing-orange)

---

## Tabla de contenidos

- [Características principales](#características-principales)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Uso rápido](#uso-rápido)
- [Arquitectura](#arquitectura)
- [API y ejemplos](#api-y-ejemplos)
- [Validación y pruebas](#validación-y-pruebas)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

---

## Características principales

- **Simulación precisa**: Cálculo del campo magnético mediante la ley de Biot-Savart con núcleo optimizado en Numba
- **Geometrías versátiles**: Línea recta, espira circular, arco, polígono, hélice y geometrías spline personalizadas
- **Visualización 3D interactiva**: Viewport basado en PyVista con soporte para:
  - Vectores de campo magnético
  - Líneas de campo (streamlines)
  - Tubos conductores
  - Isosuperficies
- **Materiales magnéticos**: Soporte para vacío, materiales paramagnéticos y ferromagnéticos (μᵣ)
- **Persistencia de datos**: Guardar y cargar escenas completas en formato JSON
- **Multihilo**: Cálculos en hilo separado sin bloquear la interfaz
- **Demos predefinidas**: Incluye ejemplo de bobinas de Helmholtz
- **Tests validados**: Comparación con soluciones analíticas conocidas

---

## Requisitos previos

- **Python**: 3.10 o superior
- **pip**: Gestor de paquetes de Python
- **Entorno virtual**: Recomendado (venv, conda, etc.)
- **Espacio en disco**: ~500 MB (incluye dependencias PyVista, PyQt6, VTK)

**Stack tecnológico**:
- **Python** — Lenguaje principal
- **PyQt6** — Interfaz gráfica de usuario
- **PyVista** — Visualización 3D (VTK)
- **NumPy** — Cálculos numéricos
- **Numba** — Aceleración JIT del kernel de cálculo
- **SciPy** — Utilidades científicas

---

## Instalación

### Opción 1: Instalación estándar (Windows, Linux, macOS)

```bash
# Clonar el repositorio
git clone <repository-url>
cd biotsavart

# Crear entorno virtual (recomendado)
python -m venv .venv

# Activar entorno virtual
# En Windows:
.\.venv\Scripts\Activate.ps1
# En Linux/macOS:
source .venv/bin/activate

# Instalar en modo desarrollo
pip install -e .
```

**Nota**: Las dependencias pesadas (PyVista, PyQt6, VTK) pueden tardar 5-10 minutos en la primera instalación.

### Opción 2: Instalación con dependencias de desarrollo

```bash
pip install -e ".[dev]"
```

Esto incluye pytest y snakeviz para análisis de rendimiento.

---

## Uso rápido

### Ejecutar la aplicación

```bash
# Opción 1: Desde el directorio del proyecto
python -m biotsavart

# Opción 2: Como comando instalado (tras `pip install -e .`)
biotsavart
```

### Guía básica de la interfaz

1. **Inicio**: La aplicación carga una espira de demostración (radio 1 m, corriente 10 A)

2. **Visualización**:
   - Marca las casillas `Vectores B` y `Líneas de campo` en el panel derecho
   - Presiona **F5** o haz clic en **Recalcular** para actualizar

3. **Añadir conductores**:
   - Haz clic en **+ Cable** para abrir el diálogo de geometrías
   - Opciones disponibles: línea, espira, arco, polígono, hélice, spline personalizado

4. **Demos predefinidas**:
   - **Demo: Helmholtz** — Carga dos espiras coaxiales con campo casi uniforme

5. **Propiedades del material**:
   - Selector de medio: vacío, paramagnético o ferromagnético
   - Modifica μᵣ sin necesidad de recalcular

6. **Persistencia**:
   - **Guardar** — Exporta la escena completa como JSON
   - **Abrir** — Carga una escena previamente guardada

---

## Arquitectura

La aplicación está organizada en módulos independientes:

```
src/biotsavart/
├── core/          # Física pura (sin dependencias Qt)
│   ├── wire.py             # Modelo de conductores
│   ├── geometry.py         # Geometrías: línea, espira, arco, etc.
│   ├── biot_savart.py      # Kernel Numba para cálculo de B
│   ├── grid.py             # Generación de mallas 3D
│   ├── streamlines.py      # Cálculo de líneas de campo
│   ├── analytic.py         # Soluciones analíticas (validación)
│   └── materials.py        # Propiedades magnéticas de materiales
├── scene/         # Modelo de estado y serialización
│   ├── scene.py            # Estado de la escena y gestión de cables
│   └── io.py               # Serialización JSON
├── viz/           # Visualización 3D (PyVista)
│   └── viewport.py         # Viewport interactivo con actores 3D
└── ui/            # Interfaz gráfica (PyQt6)
    ├── main_window.py      # Ventana principal
    ├── properties_panel.py  # Panel lateral de propiedades
    ├── scene_tree.py       # Árbol de cables y configuración
    ├── dialogs.py          # Diálogos de entrada (geometrías, etc.)
    └── compute_worker.py   # Worker thread para cálculos
```

**Flujo de datos**:
1. Usuario interactúa con la UI (PyQt6)
2. Cambios en la escena se notifican via señales Qt
3. `compute_worker` calcula B en hilo separado (Numba)
4. Resultados se visualizan en `viewport` (PyVista)

**Optimizaciones**:
- El cálculo de B se ejecuta en `QThread` para no bloquear la UI
- El kernel usa Numba con compilación JIT para máxima velocidad
- Cambiar material **no recalcula** — solo escala por μᵣ (lineal)

---

## API y ejemplos

### Ejemplo 1: Cálculo de campo desde código

```python
from biotsavart.core.wire import Wire
from biotsavart.core.geometry import CircleGeometry
from biotsavart.core.biot_savart import compute_magnetic_field
import numpy as np

# Crear una espira
wire = Wire(
    name="demo_loop",
    geometry=CircleGeometry(radius=1.0),
    current=10.0  # Amperios
)

# Definir puntos de evaluación (malla 3D)
points = np.linspace(-2, 2, 10)
x, y, z = np.meshgrid(points, points, [0])  # Plano z=0
eval_points = np.column_stack([x.ravel(), y.ravel(), z.ravel()])

# Calcular campo magnético
B = compute_magnetic_field([wire], eval_points)
print(f"Campo magnético en {len(eval_points)} puntos calculado")
```

### Ejemplo 2: Crear y guardar una escena

```python
from biotsavart.scene.scene import Scene
from biotsavart.scene.io import save_scene

# Crear escena
scene = Scene()
scene.add_wire(wire)

# Guardar
save_scene(scene, "my_scene.json")
print("Escena guardada exitosamente")
```

---

## Validación y pruebas

La precisión del kernel se valida contra soluciones analíticas conocidas:

```bash
# Ejecutar tests
pip install pytest
set PYTHONPATH=src
pytest -v
```

### Resultados de validación

| Test | Caso de referencia | Tolerancia | Estado |
|------|-------------------|-----------|---------|
| Espira en eje | Solución analítica | <1% | ✅ |
| Hilo recto infinito | μ₀I/(2πd) | <2% | ✅ |
| Centro de espira | Fórmula exacta | <0.1% | ✅ |
| Superposición lineal | Aditividad | <0.1% | ✅ |
| Solenoide finito | L/R=20 (ideal) | 7% | ✅ |

Todos los tests validan que el simulador produce resultados precisos en régimen lineal.

---

## Limitaciones conocidas

**Alcance intermedio** (v0.1.0):

- ❌ **Material no homogéneo**: Solo material homogéneo en todo el espacio (sin fronteras entre medios)
- ❌ **Efectos no lineales**: Sin histéresis ni saturación ferromagnética
- ❌ **GPU no soportada**: Usa CPU con paralelización Numba (eficiente hasta mallas ~80³)
- ❌ **Edición 3D limitada**: Geometrías solo editable vía diálogo (no drag en viewport)
- ⚠️ **Campos cuasi-estáticos**: Asume corrientes continuas, sin radiación electromagnética

**Roadmap futuro** (fases planeadas):
- [ ] Fase 2: Edición geométrica interactiva (picking y drag en 3D)
- [ ] Fase 3: Soporte GPU (CUDA/OpenCL)
- [ ] Fase 4: Materiales ferromagnéticos no lineales
- [ ] Fase 5: Fem 3D con condiciones de frontera entre medios

---

## Contribuir

Las contribuciones son bienvenidas. Para reportar bugs o sugerir mejoras:

1. Abre un **issue** describiendo el problema o mejora
2. Proporciona contexto: reproducción, versión Python, SO
3. Para pull requests: asegúrate de que los tests pasen

```bash
# Ejecutar tests localmente antes de PR
pytest -v
```

**Estándares**:
- Código: PEP 8 (formateado con autopep8 o black)
- Tests: Mínimo 80% de cobertura en núcleo
- Documentación: Docstrings en inglés, comentarios en caso complejo

---


**Hecho por**
1. Andrés Felipe Giraldo Rojas
2. Julian Santiago Parra Arias
3. Jeronimo Jimenez Valencia
