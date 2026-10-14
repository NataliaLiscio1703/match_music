@echo off
REM ============================================================
REM  Match Music - Instalacion (se ejecuta UNA sola vez)
REM  Crea el entorno virtual .venv e instala las librerias.
REM ============================================================
cd /d "%~dp0"
echo.
echo  === Match Music: instalacion ===
echo.

REM --- 1. Buscar Python (primero "python", si no "py") ---
set "PY="
python --version >nul 2>&1 && set "PY=python"
if not defined PY (py --version >nul 2>&1 && set "PY=py")
if not defined PY (
    echo  [ERROR] No se encontro Python.
    echo  Instalalo desde https://www.python.org/downloads/
    echo  y marca la casilla "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)
echo  Python encontrado:
%PY% --version
echo.

REM --- 2. Crear el entorno virtual (si no existe) ---
if not exist ".venv\Scripts\python.exe" (
    echo  Creando entorno virtual .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo  [ERROR] No se pudo crear el entorno virtual.
        pause
        exit /b 1
    )
)

REM --- 3. Instalar librerias (Experta primero y sin dependencias) ---
echo  Instalando librerias (puede tardar unos minutos) ...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install --no-deps experta==1.9.4
if errorlevel 1 goto error_pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error_pip

echo.
echo  NOTA: si arriba aparece en rojo "experta 1.9.4 requires schema==0.6.7",
echo  es normal y se puede ignorar.
echo.

REM --- 4. Verificar el motor con los casos de prueba ---
echo  === Verificando el motor (demo.py) ===
".venv\Scripts\python.exe" demo.py
echo.
echo  === Instalacion terminada ===
echo  Para abrir la app, hace doble clic en iniciar.bat
echo.
pause
exit /b 0

:error_pip
echo.
echo  [ERROR] Fallo la instalacion de librerias.
echo  Revisa tu conexion a internet y volve a ejecutar instalar.bat
echo.
pause
exit /b 1
