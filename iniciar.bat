@echo off
REM ============================================================
REM  Match Music - Abrir la aplicacion
REM  Requiere haber ejecutado instalar.bat al menos una vez.
REM ============================================================
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo  [ERROR] Todavia no esta instalado.
    echo  Primero hace doble clic en instalar.bat
    echo.
    pause
    exit /b 1
)

echo.
echo  === Match Music ===
echo  Se va a abrir el navegador en http://localhost:8501
echo  Para CERRAR la app: cerra esta ventana (o Ctrl + C).
echo.
REM Abre el navegador 4 segundos despues (cuando el servidor ya arranco).
start "" /min cmd /c "timeout /t 4 /nobreak >nul & start "" http://localhost:8501"

REM --server.headless true evita que Streamlit pida un email la primera vez.
".venv\Scripts\python.exe" -m streamlit run app.py --server.headless true --browser.gatherUsageStats false
pause
