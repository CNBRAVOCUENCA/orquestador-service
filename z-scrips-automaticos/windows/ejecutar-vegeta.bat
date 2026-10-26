@echo off
setlocal
if exist "%~dp0..\..\.venv\Scripts\python.exe" (
  "%~dp0..\..\.venv\Scripts\python.exe" "%~dp0..\linux\ejecutar_vegeta.py" %*
) else (
  where py >nul 2>&1
  if not errorlevel 1 (
    py -3 "%~dp0..\linux\ejecutar_vegeta.py" %*
  ) else (
    python "%~dp0..\linux\ejecutar_vegeta.py" %*
  )
)
exit /b %errorlevel%
