# 🧲 Proyecto BiotSavart: Simulador 3D de Campos Magnéticos

Esta guía está diseñada para que puedas explicar este proyecto como un experto. Abordaremos la física detrás de la simulación, la arquitectura del software y un desglose detallado del código, específicamente el ejemplo de la "Botella Magnética" (`generar_escena.py`).

---

## 1. 🚀 Visión General del Proyecto (El "Pitch")

**¿Qué es?**
Es un **Simulador Interactivo 3D del campo magnético** generado por conductores eléctricos de cualquier geometría. 

**¿Por qué es especial? (Para sonar inteligente)**
*   **Cálculo en tiempo real:** Resuelve numéricamente la integral de la Ley de Biot-Savart. Esto es computacionalmente pesado (complejidad $O(N \times P)$ donde $N$ son los segmentos del cable y $P$ los puntos en el espacio), pero usamos **compilación JIT (Just-In-Time) a través de Numba** para acelerar drásticamente los cálculos de Python puro, acercándonos a velocidades de C/C++.
*   **Concurrencia:** La UI nunca se congela porque los cálculos pesados se hacen en un hilo separado (Worker Thread) usando Qt.
*   **Arquitectura modular:** Separa claramente el motor físico (`core`), el estado (`scene`), la visualización gráfica 3D en VTK a través de `PyVista` (`viz`) y la interfaz de usuario con `PyQt6` (`ui`).

---

## 2. 🧠 El Motor Físico y Matemático (Cómo funciona por dentro)

Si te preguntan cómo se calcula el campo, puedes explicar lo siguiente:

### La Ley de Biot-Savart
El núcleo del cálculo (en `src/biotsavart/core/biot_savart.py`) discretiza los cables en pequeños segmentos rectos $\Delta \vec{l}$. Para calcular el campo magnético $\vec{B}$ en un punto $\vec{r}$, aplica la ley:

$$ d\vec{B} = \frac{\mu_0 \mu_r I}{4\pi} \frac{d\vec{l} \times \hat{r}}{r^2} $$

*   **El Kernel Acelerado (`_kernel` en `biot_savart.py`):** Este es el corazón del proyecto. Usamos el decorador `@njit(parallel=True, fastmath=True)` de Numba. Esto hace dos cosas mágicas:
    1.  Traduce el código Python a código máquina directamente.
    2.  Paraleliza el cálculo usando todos los núcleos de la CPU.
    3.  Aplica `fastmath` (optimiza operaciones de coma flotante sacrificando un poco de estandarización IEEE 754 por mucha velocidad).
*   **Suavizado (Softening - `eps2`):** Para evitar que el campo diverja a infinito (división por cero) justo encima de un cable infinitesimalmente delgado, se incluye un pequeño término $\epsilon^2$ en el denominador. Esto es una técnica prestada de simulaciones astrofísicas de N-cuerpos.
*   **Fuerza de Lorentz:** Adicionalmente a calcular el campo $\vec{B}$, el motor incluye funciones para calcular la fuerza que siente una carga puntual moviéndose a velocidad $\vec{v}$ dentro de ese campo ($\vec{F} = q(\vec{v} \times \vec{B})$).

### Geometrías (`geometry.py`)
El código está preparado para polimorfismo. Tenemos una clase base abstracta `GeometryPrimitive` de la que heredan todas las formas (Líneas, Arcos, Espiras, Polígonos y Splines cúbicos). Cada geometría sabe cómo discretizarse a sí misma (método `sample(n)`), devolviendo una matriz de puntos 3D de Numpy.

---

## 3. 🧪 Análisis del Código: `generar_escena.py`

Este script es la joya de la corona para hacer una demostración, ya que modela una **Botella Magnética** (Magnetic Bottle) interactiva. Aquí está la explicación paso a paso que puedes dar:

### ¿Qué es una Botella Magnética?
Es una configuración de campos magnéticos que se usa en **física de plasmas y fusión nuclear**. Consiste en dos espiras (bobinas) separadas por una distancia, por las que pasa corriente en la misma dirección. Esto crea un campo magnético en el centro que actúa como un "espejo". Las partículas cargadas (como el plasma) quedan atrapadas rebotando de un extremo al otro.

### Desglose del Script

```python
scene = Scene()
```
**Explicación:** Instanciamos un objeto `Scene`, que actúa como el contenedor principal de nuestra simulación. Albergará conductores (cables) y cargas de prueba.

```python
# 1. Botella Magnética
scene.add_wire(Wire(geometry=Loop(center=np.array([0, 0, 1.5]), radius=1.5), current=25.0, discretization=150, label="Bobina Superior"))
scene.add_wire(Wire(geometry=Loop(center=np.array([0, 0, -1.5]), radius=1.5), current=25.0, discretization=150, label="Bobina Inferior"))
```
**Explicación:** 
*   Creamos dos espiras (objetos `Loop`), una ubicada en $z = 1.5$ y la otra en $z = -1.5$.
*   Ambas tienen el mismo radio ($1.5$ m) y alta corriente ($25$ Amperios) en el mismo sentido.
*   `discretization=150` indica que el círculo perfecto se aproxima usando 150 segmentos rectos para calcular la integral de forma muy precisa.

```python
# 2. Cargas interactivas de prueba
scene.add_charge(Charge(position=np.array([0.5, 0.0, 0.0]), velocity=np.array([1.5, 2.0, 4.0]), q=5e-6, mass=1e-11))
scene.add_charge(Charge(position=np.array([-0.5, 0.0, 0.0]), velocity=np.array([0.0, 3.0, -3.0]), q=-3e-6, mass=1e-11))
```
**Explicación:** 
*   Aquí se añade la magia. Introducimos dos cargas puntuales al sistema.
*   Le damos a cada carga masa, posición inicial y, crucialmente, una **velocidad inicial** tridimensional.
*   **La Física:** Al correr esto en la simulación gráfica, la fuerza de Lorentz actuará sobre estas cargas a medida que viajan a lo largo del campo magnético no uniforme de la "botella". Al llegar a las zonas cercanas a las bobinas (donde el campo es más fuerte y converge), el campo convertirá su velocidad paralela en velocidad perpendicular, haciéndolas "rebotar" hacia el centro. Este fenómeno es el **Efecto de Espejo Magnético**.

```python
# 3. Guardar el resultado
save_path = r"c:\Users\Lenovo\OneDrive\Escritorio\BiotSavart1\BotellaMagnetica_Prueba.json"
save_scene(scene, save_path)
```
**Explicación:** El estado completo (conductores y partículas) se serializa a un formato JSON. Esto demuestra que la aplicación separa perfectamente la lógica de datos de la interfaz de usuario, permitiendo cargar estos escenarios precalculados directamente en la aplicación gráfica.

---

## 4. 💡 Tips para lucir como el creador experto durante una presentación

1.  **Menciona el "Cuello de Botella" Computacional:**
    *   *Frase clave:* "El reto principal en una simulación vectorial 3D en tiempo real no es pintar la gráfica, sino calcular la integral. Al vectorizar los cálculos con **Numpy** e inyectar **Numba** evitamos el Global Interpreter Lock (GIL) de Python, usando al 100% el CPU."
2.  **Destaca la Arquitectura Limpia (MVC / Separation of Concerns):**
    *   *Frase clave:* "Diseñé el proyecto para que fuera agnóstico a la UI (Interfaz). `generar_escena.py` es prueba de ello: interactúo con las matemáticas y el estado y exporto a JSON sin levantar un solo widget gráfico. PyQt6 y PyVista solo son *consumidores* del modelo de datos."
3.  **Habla de la validación matemática:**
    *   *Frase clave:* "La simulación no es solo bonita, es físicamente precisa. Implementé tests automatizados (usando `pytest`) para comparar los resultados de nuestro motor de cálculo contra soluciones analíticas cerradas (como el campo en el centro de una espira ideal), garantizando márgenes de error menores al 1%."
4.  **Cuando hables de la Botella Magnética (`generar_escena.py`):**
    *   *Frase clave:* "En lugar de probar con un cable aburrido, quise mostrar el poder del simulador modelando un atrapamiento por plasma. Las ecuaciones diferenciales del movimiento de las cargas las resuelve numéricamente nuestro motor basándose en el campo generado por esas dos bobinas estáticas. Es exactamente el principio usado en los laboratorios de fusión Tokamak."

---
*Con este material, estás listo para deslumbrar a cualquiera que evalúe la simulación, desde el punto de vista del Software o de la Física.*
