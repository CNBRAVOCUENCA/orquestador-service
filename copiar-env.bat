@echo off
setlocal
cd /d "%~dp0"
if exist .env (
  echo Ya existe .env. Editalo para cambiar la clave de Gemini.
) else (
  copy .env.example .env >nul
  echo Se creo .env. Completa GEMINI_API_KEY.
)
pause