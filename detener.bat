@echo off
setlocal
cd /d "%~dp0"
docker compose -f infra\docker-compose.yml down
pause