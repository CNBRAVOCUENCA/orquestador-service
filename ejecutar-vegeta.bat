@echo off
setlocal
cd /d "%~dp0"

set "VEGETA_DIR=%~dp0infra\vegeta"
set "ID_FILE=%VEGETA_DIR%\document-id.txt"
if not exist "%ID_FILE%" (
  echo Primero ejecuta subir-pdf.bat para subir un PDF y guardar su ID.
  pause
  exit /b 1
)
if not exist "%VEGETA_DIR%\targets-extractor.txt" (
  echo No se encontro infra\vegeta\targets-extractor.txt.
  pause
  exit /b 1
)

set "DOCUMENT_ID="
set /p "DOCUMENT_ID=" < "%ID_FILE%"
if not defined DOCUMENT_ID (
  echo document-id.txt esta vacio. Vuelve a subir el PDF.
  pause
  exit /b 1
)

set "RATE="
set /p "RATE=Solicitudes por segundo [2]: "
if not defined RATE set "RATE=2"

set "DURATION="
set /p "DURATION=Duracion, por ejemplo 5s [5s]: "
if not defined DURATION set "DURATION=5s"

for /f %%I in ('powershell.exe -NoLogo -NoProfile -Command "Get-Date -Format yyyyMMdd-HHmmss"') do set "STAMP=%%I"
if not defined STAMP set "STAMP=prueba"
set "RESULTS=extractor-results-%STAMP%.bin"
set "REPORT=extractor-report-%STAMP%.txt"
set "VEGETA_IMAGE=extractor-vegeta:local"

docker image inspect %VEGETA_IMAGE% >nul 2>&1
if errorlevel 1 (
  set "VEGETA_IMAGE=peterevans/vegeta:latest"
)

echo.
echo Ejecutando Vegeta con document_id=%DOCUMENT_ID%...
echo Tasa: %RATE% solicitudes/s; duracion: %DURATION%
echo.
docker run --rm -v "%VEGETA_DIR%:/work" -w /work --entrypoint sh %VEGETA_IMAGE% -c "vegeta attack -targets=targets-extractor.txt -rate=%RATE% -duration=%DURATION% > %RESULTS%"
if errorlevel 1 (
  echo La prueba fallo. Verifica Docker, la tasa, la duracion y que el extractor este activo.
  pause
  exit /b 1
)

docker run --rm -v "%VEGETA_DIR%:/work" -w /work --entrypoint sh %VEGETA_IMAGE% -c "vegeta report -type=text %RESULTS%" > "%VEGETA_DIR%\%REPORT%"
if errorlevel 1 (
  echo No se pudo generar el reporte.
  pause
  exit /b 1
)

echo Reporte:
type "%VEGETA_DIR%\%REPORT%"
echo.
echo Resultados: infra\vegeta\%RESULTS%
echo Reporte guardado: infra\vegeta\%REPORT%
pause
