@echo off
setlocal
cd /d "%~dp0"
docker compose --env-file .env -f infra\docker-compose.yml down
if errorlevel 1 (
	echo No se pudo detener el stack. Verifica que Docker Desktop este activo.
	pause
	exit /b 1
)
echo Stack detenido.
pause