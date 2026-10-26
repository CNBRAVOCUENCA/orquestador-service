@echo off
setlocal
if exist "%~dp0..\..\.venv\Scripts\python.exe" (
  "%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\linux\subir_pdf.py" %*
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 "%~dp0..\linux\subir_pdf.py" %*
  ) else (
    python "%~dp0..\linux\subir_pdf.py" %*
  )
)
exit /b %errorlevel%
