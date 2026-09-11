@echo off
setlocal
cd /d "%~dp0"

if not exist .env (
  copy .env.example .env >nul
  echo Se creo .env. Completa GEMINI_API_KEY antes de continuar.
  notepad .env
)

echo Iniciando microservicios...
docker compose -f infra\docker-compose.yml up -d --build --wait --wait-timeout 180
if errorlevel 1 (
  echo No se pudo iniciar el stack. Ejecuta:
  echo docker compose -f infra\docker-compose.yml ps
  pause
  exit /b 1
)

echo Stack saludable. URL publica:
docker compose -f infra\docker-compose.yml logs --tail=30 cloudflared
pause