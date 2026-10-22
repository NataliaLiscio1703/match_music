# Match Music — Sistema experto recomendador de música

Sistema basado en conocimiento que recomienda **canciones, artistas y estilos musicales** según las preferencias del usuario (estilo, época, país, música local, idioma) y **explica cada recomendación** mostrando la cadena de reglas que la justifica. Es un recomendador, no un reproductor: no reproduce, descarga ni distribuye música.

| | |
|---|---|
| **Materia** | Análisis de Datos II: Sistemas Expertos y Redes de Conocimiento (UNICABA, 2026.2) |
| **Grupo autor (proveedor)** | Grupo A |
| **Grupo cliente** | Grupo B |
| **Motor de inferencia** | Experta 1.9.4 (encadenamiento hacia adelante) |
| **Interfaz** | Streamlit 1.65.0 |
| **Versión de Python** | 3.13 (requiere 3.10 o superior) |
| **Sistema operativo** | Windows 10/11 (local) · Linux (Streamlit Community Cloud) |
| **App publicada** | _completar con la URL de Streamlit Cloud_ |

---

## Guía de instalación en Windows

Tiempo estimado: 10 minutos. Se instala **una sola vez**.

### Paso 1. Instalar Python (si no lo tenés)

1. Abrí **PowerShell**: tecla Windows, escribí `PowerShell` y Enter.
2. Escribí `python --version` y Enter.
   - Si aparece `Python 3.10` o mayor (por ejemplo `Python 3.13.1`), ya está: seguí al paso 2.
   - Si da error, si abre la Microsoft Store o si la versión es menor, instalalo desde [python.org/downloads](https://www.python.org/downloads/).

> ⚠ **En la primera pantalla del instalador marcá la casilla «Add python.exe to PATH».** Si no la marcás, Windows no va a encontrar Python. Después de instalar, cerrá PowerShell y abrilo de nuevo.

### Paso 2. Ubicar la carpeta del proyecto

Descomprimí `match_music.zip` en una carpeta **fuera de OneDrive**, por ejemplo `C:\proyectos\match_music` o `C:\Users\TuUsuario\Documents\match_music`.

> **¿Por qué fuera de OneDrive?** El Escritorio y Documentos muchas veces están sincronizados con OneDrive. Durante la instalación se crean miles de archivos chicos, OneDrive intenta subirlos y a veces los bloquea y la instalación falla.

Adentro tenés que ver esto:

```
match_music\
├── .streamlit\config.toml
├── assets\logo.png
├── data\catalog.json
├── experta\          (motor de inferencia incluido)
├── src\
│   ├── __init__.py
│   ├── engine.py
│   ├── facts.py
│   └── tracer.py
├── app.py
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

Al terminar tiene que aparecer, entre otras cosas, el caso **«Rock de los 80»** con 7 canciones (Bon Jovi, Soda Stereo, Guns N' Roses…) y al final **`=== Instalacion terminada ===`**. Apretá cualquier tecla para cerrar.

> **Si Windows muestra «Windows protegió su PC»:** hacé clic en **«Más información»** y después en **«Ejecutar de todas formas»**. Aparece porque el archivo vino de internet. Si querés ver qué hace antes de ejecutarlo, abrilo con el Bloc de notas: son unas pocas líneas comentadas.

### Paso 4. Abrir la aplicación (doble clic)

Hacé **doble clic en `iniciar.bat`**. A los pocos segundos se abre el navegador con la app en **http://localhost:8501**. Si no se abre solo, copiá esa dirección en el navegador.

**Dejá abierta la ventana negra mientras uses la app**: es el servidor. Para cerrar la app, cerrá esa ventana.

**Los días siguientes**, solo el paso 4: doble clic en `iniciar.bat`.

---

## Alternativa: instalar con comandos

Si preferís no usar los `.bat`, o si fallan, abrí PowerShell **en la carpeta del proyecto**. En el Explorador, entrá a `match_music`, hacé clic en la barra de dirección, escribí `powershell` y Enter. Después ejecutá:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe demo.py
.venv\Scripts\python.exe -m streamlit run app.py
```

La primera vez, Streamlit puede pedir un email en la ventana: apretá **Enter** sin escribir nada. Para cerrar la app, `Ctrl + C`.

> Estos comandos usan directamente el Python del entorno virtual (`.venv\Scripts\python.exe`), así que **no hace falta "activarlo"** y se evita el error de PowerShell «la ejecución de scripts está deshabilitada en este sistema».

**Desde VS Code:** *Archivo → Abrir carpeta…* → `match_music`, después *Terminal → Nuevo terminal* y los mismos comandos.

---

## Si algo falla

| Mensaje o síntoma | Causa | Solución |
|---|---|---|
| `[ERROR] No se encontro Python` o `python` no se reconoce | Python no está instalado o no está en el PATH | Reinstalá Python marcando **«Add python.exe to PATH»** y volvé a ejecutar `instalar.bat`. |
| Escribir `python` abre la Microsoft Store | Windows tiene un acceso directo falso a Python | Instalá Python desde python.org (paso 1). |
| La ventana negra se abre y se cierra enseguida | Un error antes de la pausa | Abrí PowerShell en la carpeta y ejecutá `.\instalar.bat` para ver el mensaje. |
| `[ERROR] Fallo la instalacion de librerias` | Sin internet, o carpeta dentro de OneDrive | Revisá la conexión, mové la carpeta fuera de OneDrive, borrá la carpeta `.venv` y ejecutá `instalar.bat` otra vez. |
| `No module named 'experta'` | Falta la carpeta `experta` del proyecto | Verificá que `experta\` esté junto a `app.py` (paso 2). No instales Experta con pip. |
| `[ERROR] Todavia no esta instalado` al abrir `iniciar.bat` | No se ejecutó la instalación | Doble clic en `instalar.bat` primero. |
| `ModuleNotFoundError: No module named 'src'` | Se ejecutó desde otra carpeta | Usá los `.bat`, o abrí PowerShell dentro de `match_music`. |
| `Port 8501 is already in use` | La app ya está abierta en otra ventana | Cerrá la otra ventana negra, o entrá directo a http://localhost:8501. |
| La app se ve sin colores ni logo | Falta la carpeta `.streamlit` o `assets` | En el Explorador: *Vista → Mostrar → Elementos ocultos*, y verificá la estructura del paso 2. |
| Las letras se ven comunes, no las del diseño | Sin internet (las fuentes vienen de Google Fonts) | No afecta el funcionamiento. Con conexión se ven bien. |

**Para empezar de cero:** borrá la carpeta `.venv` y ejecutá `instalar.bat` de nuevo.

---

## Por qué Experta viene incluida en el repositorio

Experta es la librería del motor de inferencia. Su última versión (1.9.4) es de 2019 y declara como dependencias `frozendict==1.2` y `schema==0.6.7`, que **no se instalan en Python 3.10 o superior**. El código de Experta en sí funciona con las versiones actuales de esas librerías.

Por eso la carpeta `experta/` contiene el código fuente original de Experta 1.9.4, **sin modificaciones** y con su licencia (LGPL v3), y `requirements.txt` fija versiones modernas de `frozendict` y `schema`. Así la instalación es un único `pip install -r requirements.txt`, que es lo único que ejecuta Streamlit Community Cloud. Detalle en [`experta/VENDORED.md`](experta/VENDORED.md).

Verificado en un entorno virtual limpio con Python 3.13: el motor ejecuta los 6 casos de `demo.py` con los resultados esperados y la app levanta sin errores.

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

## Cómo está organizado el código

| Archivo | Qué hace |
|---|---|
| `src/facts.py` | Define los tipos de hechos: preferencias, canciones, hechos derivados, coincidencias, recomendaciones. |
| `src/engine.py` | **Base de reglas (27 reglas) y motor de inferencia.** No depende de la interfaz. |
| `src/tracer.py` | Convierte la traza del motor en texto legible. No contiene reglas. |
| `app.py` | Interfaz Streamlit: recoge preferencias, llama al motor y muestra resultados y explicación. |
| `demo.py` | Ejecuta casos de prueba por consola, sin interfaz. |
| `data/catalog.json` | Catálogo de canciones de prueba. |
| `experta/` | Código de Experta 1.9.4 incluido (ver arriba). No contiene reglas del sistema. |
| `instalar.bat` / `iniciar.bat` | Instalación y apertura con doble clic en Windows. |

La base de reglas está separada de la interfaz: `app.py` solo usa la función `recomendar()` de `engine.py`.

### Niveles de encadenamiento

| Nivel | Reglas | Qué hace |
|---|---|---|
| 1A | R01–R06 | Lee las preferencias del usuario y las convierte en hechos derivados. |
| 1B | R07–R10 | Deduce contexto musical (géneros afines, música latina, rock de los 80). |
| 2 | R11–R21 | Compara cada canción con lo deducido: coincidencias y descartes. |
| 3 | R22–R24 | Calcula el puntaje y decide si recomendar. |
| 4 | R25–R26 | Deriva artistas y estilos a partir de las canciones recomendadas. |
| Cierre | R27 | Si nada alcanzó el umbral, informa que no hay coincidencia suficiente. |

Cadena más larga: `UserPreferences → R01 → R07 → R13 → R22 → R23 → R25`.