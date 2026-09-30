@echo off
setlocal
cd /d "%~dp0"

set "PDF_PATH="
set /p "PDF_PATH=Ruta completa del PDF (sin comillas): "
if not defined PDF_PATH (
  echo No se indico ningun archivo.
  pause
  exit /b 1
)
if not exist "%PDF_PATH%" (
  echo No se encontro el archivo: %PDF_PATH%
  pause
  exit /b 1
)

set "PDF_NAME="
set /p "PDF_NAME=Nombre para el documento: "
if not defined PDF_NAME (
  echo Debes indicar un nombre para el documento.
  pause
  exit /b 1
)

echo.
echo Subiendo PDF a documentos-service...
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0subir-documento.ps1" -PdfPath "%PDF_PATH%" -Name "%PDF_NAME%"
if errorlevel 1 (
  echo La subida fallo. Verifica que Docker y el stack esten activos.
  pause
  exit /b 1
)

echo El ID quedo guardado para ejecutar Vegeta.
pause
