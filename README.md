# Match Music — Sistema experto recomendador de música

Sistema basado en conocimiento que recomienda **canciones, artistas y estilos musicales** según las preferencias del usuario (estilo, época, país, música local, idioma, o un artista o canción de referencia) y **explica cada recomendación** mostrando la cadena de reglas que la justifica. Es un recomendador, no un reproductor: no reproduce, descarga ni distribuye música.

| | |
|---|---|
| **Materia** | Análisis de Datos II: Sistemas Expertos y Redes de Conocimiento (UNICABA, 2026.2) |
| **Grupo autor (proveedor)** | Grupo A — Facundo Joaquín Olcese, Natalia Liscio, Andrés Carrión, Alan Uriel Bronsztein, Sebastián Flehr, Facundo Aranda |
| **Grupo cliente** | Grupo B |
| **App publicada** | https://match-music.streamlit.app/ |
| **Repositorio** | https://github.com/NataliaLiscio1703/match_music |
| **Motor de inferencia** | Experta 1.9.4 (encadenamiento hacia adelante), incluida en `experta/` |
| **Interfaz** | Streamlit 1.65.0 |
| **Versión de Python** | 3.13 (probado). Requiere 3.10 o superior |
| **Sistemas probados** | Windows 10/11 (local) · Linux (local y Streamlit Community Cloud) |

---

## Inicio rápido (cualquier sistema operativo)

Requiere Python 3.10 o superior y Git.

```bash
git clone https://github.com/NataliaLiscio1703/match_music.git
cd match_music
python -m venv .venv
```

Instalar y ejecutar usando el Python del entorno virtual (no hace falta activarlo):

| Paso | Windows (PowerShell) | macOS / Linux |
|---|---|---|
| Instalar librerías | `.venv\Scripts\python.exe -m pip install -r requirements.txt` | `.venv/bin/python -m pip install -r requirements.txt` |
| Casos de prueba por consola | `.venv\Scripts\python.exe demo.py` | `.venv/bin/python demo.py` |
| Notebook de casos de prueba (opcional) | `.venv\Scripts\python.exe -m pip install notebook` y luego `.venv\Scripts\python.exe -m jupyter notebook casos_cliente.ipynb` | `.venv/bin/python -m pip install notebook` y luego `.venv/bin/python -m jupyter notebook casos_cliente.ipynb` |
| Abrir la app | `.venv\Scripts\python.exe -m streamlit run app.py` | `.venv/bin/python -m streamlit run app.py` |

La app se abre en http://localhost:8501. La primera vez, Streamlit puede pedir un email en la terminal: apretá **Enter** sin escribir nada. Para cerrarla, `Ctrl + C`.

> **No instales Experta con pip.** Ya viene incluida en la carpeta `experta/` (ver [por qué](#por-qué-experta-viene-incluida-en-el-repositorio)).

---

## Guía paso a paso para Windows (sin comandos)

Tiempo estimado: 10 minutos. Se instala **una sola vez**.

### Paso 1. Instalar Python (si no lo tenés)

1. Abrí **PowerShell**: tecla Windows, escribí `PowerShell` y Enter.
2. Escribí `python --version` y Enter.
   - Si aparece `Python 3.10` o mayor (por ejemplo `Python 3.13.1`), ya está: seguí al paso 2.
   - Si da error, si abre la Microsoft Store o si la versión es menor, instalalo desde [python.org/downloads](https://www.python.org/downloads/).

> ⚠ **En la primera pantalla del instalador marcá la casilla «Add python.exe to PATH».** Si no la marcás, Windows no va a encontrar Python. Después de instalar, cerrá PowerShell y abrilo de nuevo.

### Paso 2. Descargar el proyecto

En la página del repositorio hacé clic en **Code → Download ZIP** (o usá el `.zip` de la entrega) y descomprimilo en una carpeta **fuera de OneDrive**, por ejemplo `C:\proyectos\match_music`.

> **¿Por qué fuera de OneDrive?** El Escritorio y Documentos muchas veces están sincronizados con OneDrive. Durante la instalación se crean miles de archivos chicos, OneDrive intenta subirlos y a veces los bloquea y la instalación falla.

Adentro tenés que ver esto:

```
match_music\
├── .streamlit\config.toml
├── assets\logo.png
├── data\catalog.json
├── experta\            (motor de inferencia incluido)
├── src\
│   ├── __init__.py
│   ├── engine.py
│   ├── facts.py
│   └── tracer.py
├── app.py
├── casos_cliente.ipynb
├── casos_prueba.py
├── demo.py
├── iniciar.bat
├── instalar.bat
├── README.md
└── requirements.txt
```

### Paso 3. Instalar (doble clic)

Hacé **doble clic en `instalar.bat`**. Se abre una ventana negra que:

1. Busca Python.
2. Crea el entorno virtual `.venv` (una "caja" con las librerías del proyecto, sin tocar el resto de tu computadora).
3. Instala las librerías.
4. Ejecuta los casos de prueba para verificar el motor.

Al terminar tienen que aparecer los ocho casos de prueba del cliente, la línea **`Casos aprobados: 8 de 8`** y al final **`=== Instalacion terminada ===`**. Apretá cualquier tecla para cerrar.

> **Si Windows muestra «Windows protegió su PC»:** hacé clic en **«Más información»** y después en **«Ejecutar de todas formas»**. Aparece porque el archivo vino de internet. Si querés ver qué hace antes de ejecutarlo, abrilo con el Bloc de notas: son unas pocas líneas comentadas.

### Paso 4. Abrir la aplicación (doble clic)

Hacé **doble clic en `iniciar.bat`**. A los pocos segundos se abre el navegador con la app en **http://localhost:8501**. Si no se abre solo, copiá esa dirección en el navegador.

**Dejá abierta la ventana negra mientras uses la app**: es el servidor. Para cerrar la app, cerrá esa ventana.

**Los días siguientes**, solo el paso 4: doble clic en `iniciar.bat`.

**Desde VS Code:** *Archivo → Abrir carpeta…* → `match_music`, después *Terminal → Nuevo terminal* y los comandos del [inicio rápido](#inicio-rápido-cualquier-sistema-operativo).

---

## Si algo falla

| Mensaje o síntoma | Causa | Solución |
|---|---|---|
| `[ERROR] No se encontro Python` o `python` no se reconoce | Python no está instalado o no está en el PATH | Reinstalá Python marcando **«Add python.exe to PATH»** y volvé a ejecutar `instalar.bat`. |
| Escribir `python` abre la Microsoft Store | Windows tiene un acceso directo falso a Python | Instalá Python desde python.org (paso 1). |
| La ventana negra se abre y se cierra enseguida | Un error antes de la pausa | Abrí PowerShell en la carpeta y ejecutá `.\instalar.bat` para ver el mensaje. |
| `[ERROR] Fallo la instalacion de librerias` | Sin internet, o carpeta dentro de OneDrive | Revisá la conexión, mové la carpeta fuera de OneDrive, borrá la carpeta `.venv` y ejecutá `instalar.bat` otra vez. |
| `No module named 'experta'` | Falta la carpeta `experta` del proyecto | Verificá que `experta` esté junto a `app.py` (paso 2). No instales Experta con pip. |
| Error que menciona `frozendict` o `schema==0.6.7` | Se instaló Experta desde pip | Desinstalala (`pip uninstall experta`), o borrá `.venv` y volvé a instalar. |
| `[ERROR] Todavia no esta instalado` al abrir `iniciar.bat` | No se ejecutó la instalación | Doble clic en `instalar.bat` primero. |
| `ModuleNotFoundError: No module named 'src'` | Se ejecutó desde otra carpeta | Usá los `.bat`, o abrí la terminal dentro de `match_music`. |
| `Port 8501 is already in use` | La app ya está abierta en otra ventana | Cerrá la otra ventana, o entrá directo a http://localhost:8501. |
| La app se ve sin colores ni logo | Falta la carpeta `.streamlit` o `assets` | En el Explorador: *Vista → Mostrar → Elementos ocultos*, y verificá la estructura del paso 2. |
| Las letras se ven comunes, no las del diseño | Sin internet (las fuentes vienen de Google Fonts) | No afecta el funcionamiento. Con conexión se ven bien. |

**Para empezar de cero:** borrá la carpeta `.venv` y volvé a instalar.

---

## Publicación en Streamlit Community Cloud

1. Entrar a [share.streamlit.io](https://share.streamlit.io) con la cuenta de GitHub dueña del repositorio.
2. **Create app → Deploy a public app from GitHub** y completar:
   - **Repository:** `NataliaLiscio1703/match_music`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** el subdominio elegido (por ejemplo `match-music`).
3. En **Advanced settings → Python version** elegir **3.13** (la versión probada).
4. **Deploy.** La primera instalación tarda unos minutos. Cada `git push` a `main` vuelve a publicar la app.

No hace falta configurar *secrets*: la app no usa claves ni servicios externos. El tema visual se toma de `.streamlit/config.toml`.

---

## Por qué Experta viene incluida en el repositorio

Experta es la librería del motor de inferencia. Su última versión (1.9.4) es de 2019 y declara como dependencias `frozendict==1.2` y `schema==0.6.7`, que **no se instalan en Python 3.10 o superior**. El código de Experta en sí funciona con las versiones actuales de esas librerías.

Por eso la carpeta `experta/` contiene el código fuente original de Experta 1.9.4, **sin modificaciones** y con su licencia (LGPL v3), y `requirements.txt` fija versiones modernas de `frozendict` y `schema`. Así la instalación es un único `pip install -r requirements.txt`, que es lo único que ejecuta Streamlit Community Cloud. Detalle en [`experta/VENDORED.md`](experta/VENDORED.md).

Verificado en un entorno virtual limpio con Python 3.13: el motor ejecuta los 8 casos del cliente de `demo.py` con los resultados esperados y la app levanta sin errores.

---

## Cómo está organizado el código

| Archivo | Qué hace |
|---|---|
| `src/facts.py` | Define los tipos de hechos: preferencias, canciones, hechos derivados, coincidencias, recomendaciones. |
| `src/engine.py` | **Base de reglas (41 reglas) y motor de inferencia.** No depende de la interfaz. |
| `src/tracer.py` | Convierte la traza del motor en texto legible. No contiene reglas. |
| `app.py` | Interfaz Streamlit: recoge preferencias, llama al motor y muestra resultados y explicación. |
| `casos_prueba.py` | Casos de prueba CA-01 a CA-08 del Grupo B, con su resultado esperado y una verificación automática. No contiene reglas. |
| `demo.py` | Ejecuta los casos de prueba del cliente por consola, sin interfaz. |
| `casos_cliente.ipynb` | Notebook ya ejecutado con los casos del cliente: entrada, esperado, resultado, traza y verificación de cada uno. |
| `data/catalog.json` | Catálogo de canciones (base de hechos). |
| `experta/` | Código de Experta 1.9.4 incluido (ver arriba). No contiene reglas del sistema. |
| `instalar.bat` / `iniciar.bat` | Instalación y apertura con doble clic en Windows. |

La base de reglas está separada de la interfaz: `app.py` solo usa la función `recomendar()` de `engine.py`.

### Niveles de encadenamiento

| Nivel | Reglas | Qué hace |
|---|---|---|
| 0 | R00 | Si la consulta no trae ningún criterio, detiene el motor antes de evaluar el catálogo. |
| 1A | R01–R06, R28–R29 | Lee las preferencias del usuario (y el artista o la canción de referencia) y las convierte en hechos derivados. |
| 1B | R07–R10, R30–R34 | Deduce contexto musical: géneros afines, género que contiene al subgénero pedido, subgéneros vecinos, música latina, rock de los 80 y rasgos de la referencia. |
| 2 | R11–R21, R35–R40 | Compara cada canción con lo deducido: coincidencias, similitud con la referencia y descartes. |
| 3 | R22–R24 | Calcula el puntaje y decide si recomendar. |
| 4 | R25–R26 | Deriva artistas y estilos a partir de las canciones recomendadas. |
| Cierre | R27 | Si nada alcanzó el umbral, informa que no hay coincidencia suficiente. |

R01–R27 son las reglas presentadas en la reunión 2 (22/10). R00 y R28–R40 se agregaron para resolver las observaciones del cliente en esa reunión (CA-02 artista base, CA-05 combinación sin resultados, CA-07 entrada vacía); se numeraron a continuación para no cambiar las referencias anteriores.

Cadena más larga: `UserPreferences → R28 → R32 → R34 → R37 → R22 → R23 → R25` (artista de referencia → rasgos → estilos vecinos → coincidencia → puntaje → recomendación → artista recomendado).

### Trazabilidad

Cada recomendación muestra los motivos de coincidencia y la cadena de reglas que la produjo. La traza completa (todas las reglas disparadas, agrupadas por nivel) se ve en la app y también la devuelve `recomendar()` en la clave `traza`. Cuando ninguna canción alcanza el umbral, la regla R27 informa: *«No se encontraron recomendaciones con coincidencia suficiente para los criterios seleccionados. Modifique o amplíe los criterios de búsqueda.»* Cuando la consulta no trae criterios, la regla R00 informa: *«Sin conclusión posible: Ingrese al menos un criterio (estilo, artista, década o país) para ejecutar la recomendación.»*

---

## Casos de prueba

`casos_prueba.py` contiene los 8 casos de prueba del Grupo B (documento de la reunión 2, 22/10/2026), con la entrada y el resultado esperado de cada ficha y una verificación automática del criterio de aceptación del cliente. Se ejecutan de dos formas:

- `demo.py`: por consola, con el resultado OK / NO OK de cada caso.
- `casos_cliente.ipynb`: notebook ya ejecutado (se puede leer directamente en GitHub) con las recomendaciones, la cadena de reglas de cada una, la traza por nivel y la cobertura de reglas.

| Caso | Objetivo | Requisitos | Resultado |
|---|---|---|---|
| CA-01 | Rock nacional + Argentina | RF-01 / RF-03 | OK |
| CA-02 | Artistas similares a Soda Stereo | RF-02 / RF-08 | OK |
| CA-03 | Pop / synth-pop de los 80 en inglés | RF-04 | OK |
| CA-04 | Indie / folk local en español | RF-06 / RF-07 | OK |
| CA-05 | Hard rock británico de los 70 en inglés | RF-01 / RF-03 / RF-05 | OK |
| CA-06 | Heavy metal de Japón de los años 20 (sin coincidencias) | RF-01 / RF-07 | OK |
| CA-07 | Entrada vacía | RF-01 | OK |
| CA-08 | Traza de inferencia completa | RF-08 | OK |

## Limitaciones conocidas

- `data/catalog.json` es un **catálogo de prueba de 34 canciones** cargado manualmente (las canciones C19–C34 se agregaron el 29/10 para cubrir los casos del cliente). Géneros, subgéneros y relaciones entre estilos están pendientes de verificación contra las fuentes del Brief §9 (Spotify Global Music Dataset, Worldwide Music Artists Dataset, Music Genre Dataset).
- Las tablas de conocimiento de `src/engine.py` (eras, géneros afines, subgéneros vecinos, país local, pesos y umbral) son valores preliminares a validar con el cliente.
- La búsqueda por artista o canción de referencia solo funciona con artistas y canciones del catálogo (se eligen de una lista en la interfaz).
- Las recomendaciones solo pueden salir de canciones presentes en el catálogo.
