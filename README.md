# Simulador Interactivo del Campo Magnético mediante la Ley de Biot-Savart

## Descripción General

Este proyecto consiste en el desarrollo de una herramienta gráfica e interactiva para la simulación y visualización tridimensional del campo magnético generado por conductores de geometría arbitraria utilizando la Ley de Biot-Savart.

La aplicación permite que el usuario diseñe libremente trayectorias tridimensionales de alambres conductores, asigne valores de corriente eléctrica y seleccione diferentes medios materiales con distintas permeabilidades magnéticas. A partir de estos parámetros, el sistema calcula numéricamente la distribución espacial del campo magnético y genera representaciones visuales avanzadas de líneas de campo, vectores y mapas de intensidad.

El objetivo principal es proporcionar una plataforma flexible para el estudio, análisis y comprensión del comportamiento de los campos magnéticos generados por corrientes eléctricas en configuraciones geométricas complejas.

---

## Objetivos

### Objetivo General

Desarrollar una herramienta computacional interactiva capaz de calcular y visualizar el campo magnético producido por conductores arbitrarios mediante la Ley de Biot-Savart.

### Objetivos Específicos

* Implementar la formulación numérica de la Ley de Biot-Savart para trayectorias tridimensionales arbitrarias.
* Permitir la construcción interactiva de conductores con formas definidas por el usuario.
* Incorporar la definición de corrientes eléctricas variables.
* Modelar distintos medios materiales mediante diferentes valores de permeabilidad magnética.
* Visualizar en tres dimensiones la distribución espacial del campo magnético.
* Facilitar la exploración y análisis de múltiples configuraciones físicas.

---

## Fundamento Teórico

La Ley de Biot-Savart describe el campo magnético diferencial generado por un elemento de corriente:

[
d\vec{B} = \frac{\mu}{4\pi}
\frac{I , d\vec{l} \times \vec{r}}
{|\vec{r}|^3}
]

donde:

* (d\vec{B}): campo magnético diferencial.
* (\mu): permeabilidad magnética del medio.
* (I): corriente eléctrica.
* (d\vec{l}): elemento diferencial del conductor.
* (\vec{r}): vector desde el elemento de corriente hasta el punto de observación.

El campo magnético total se obtiene integrando la expresión sobre toda la trayectoria del conductor:

[
\vec{B} =
\frac{\mu I}{4\pi}
\int
\frac{d\vec{l}\times \vec{r}}
{|\vec{r}|^3}
]

Debido a que las trayectorias pueden poseer geometrías arbitrarias, la integración se realiza mediante métodos numéricos.

---

## Características Principales

### Construcción de Conductores

* Creación de trayectorias 3D mediante puntos de control.
* Edición interactiva de geometrías.
* Soporte para:

  * Líneas rectas.
  * Espiras circulares.
  * Bobinas helicoidales.
  * Conductores cerrados.
  * Geometrías completamente personalizadas.

### Configuración Eléctrica

* Definición de corriente eléctrica.
* Cambio dinámico de magnitud y dirección de la corriente.
* Actualización automática de resultados.

### Medios Magnéticos

La simulación permite seleccionar distintos medios:

| Medio  | Permeabilidad Relativa ((\mu_r)) |
| ------ | -------------------------------- |
| Vacío  | 1                                |
| Aire   | 1.0006                           |
| Hierro | 200 - 5000 (según modelo)        |

La permeabilidad absoluta se calcula mediante:

[
\mu = \mu_r \mu_0
]

donde:

[
\mu_0 = 4\pi \times 10^{-7} , H/m
]

---

## Visualización

La aplicación ofrece visualizaciones tridimensionales de:

* Trayectoria del conductor.
* Campo magnético vectorial.
* Líneas de campo magnético.
* Mapas de intensidad.
* Superficies de igual magnitud.
* Escalas de color para magnitud del campo.

---

## Arquitectura del Sistema

### Módulo de Geometría

Responsable de:

* Crear conductores.
* Almacenar puntos de control.
* Generar segmentos discretizados.

### Módulo Numérico

Responsable de:

* Discretizar la trayectoria.
* Evaluar la integral de Biot-Savart.
* Calcular el campo en una malla tridimensional.

### Módulo de Materiales

Responsable de:

* Gestionar las propiedades magnéticas.
* Aplicar factores de permeabilidad.

### Módulo de Visualización

Responsable de:

* Renderizado 3D.
* Líneas de campo.
* Vectores y mapas de intensidad.

### Interfaz Gráfica

Responsable de:

* Interacción con el usuario.
* Edición de trayectorias.
* Configuración de parámetros.
* Visualización de resultados.

---

## Tecnologías Utilizadas

* Python 3.x
* NumPy
* SciPy
* PyVista
* VTK
* PyQt6 / PySide6
* Matplotlib

---

## Flujo de Funcionamiento

1. El usuario crea una trayectoria tridimensional.
2. Se define el valor de corriente.
3. Se selecciona el medio magnético.
4. La trayectoria se discretiza en segmentos.
5. Se evalúa la Ley de Biot-Savart numéricamente.
6. Se calcula el campo sobre una malla espacial.
7. Se generan las visualizaciones tridimensionales.
8. El usuario puede modificar parámetros y recalcular en tiempo real.

---

## Casos de Uso

### Caso 1: Alambre Recto

* Corriente constante.
* Visualización de líneas circulares de campo.

### Caso 2: Espira Circular

* Campo concentrado en el centro.
* Verificación con resultados teóricos.

### Caso 3: Bobina Helicoidal

* Generación de campo similar al de un solenoide.

### Caso 4: Geometría Arbitraria

* Trayectoria definida completamente por el usuario.
* Evaluación numérica general.

---

## Validación

La precisión del simulador se verificará comparando los resultados obtenidos con soluciones analíticas conocidas para:

* Conductor recto infinito.
* Espira circular.
* Solenoide ideal.

Se calculará el error relativo entre los resultados numéricos y teóricos.

---

## Posibles Extensiones Futuras

* Conductores múltiples.
* Corrientes variables en el tiempo.
* Materiales magnéticos complejos.
* Exportación de simulaciones.
* Animaciones temporales.
* Aceleración mediante GPU.
* Simulación magnetostática avanzada.

---

## Conclusiones

El proyecto proporciona una herramienta versátil para el estudio de campos magnéticos generados por corrientes eléctricas en conductores de geometría arbitraria. La combinación de cálculo numérico, visualización tridimensional e interacción gráfica permite explorar configuraciones físicas que normalmente resultan difíciles de analizar mediante métodos analíticos tradicionales.
