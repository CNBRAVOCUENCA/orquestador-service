# Despliegue y operación (12-Factor App)

Este documento describe cómo se cumplen los factores de build/release/run,
paridad dev/prod y procesos de administración.

## Build / Release / Run separados (Factor V)

- **Build**: cada microservicio se construye a partir de su `Dockerfile`.
  El build produce una imagen inmutable con el código y sus dependencias
  (declaradas en `pyproject.toml` + `uv.lock`).
- **Release**: la release combina la imagen (build) con la configuración
  del entorno (variables de entorno del `docker-compose.yml` o del `.env`).
  Cada release queda identificada por el commit (`SERVICE_REF` en el
  compose) y la versión declarada en `pyproject.toml`.
- **Run**: `docker compose up -d` ejecuta la release. El código no se
  modifica en runtime; para cambiarlo se hace un nuevo build → release.

## Paridad dev / prod (Factor X)

El objetivo es que desarrollo y producción sean lo más parecidos posible:

- **Producción / integración**: MongoDB real (`DATABASE_URL=mongodb://mongo:27017`),
  Redis real, todos los servicios en contenedores.
- **Desarrollo con paridad alta**: usar también Mongo y Redis reales
  localmente (vía `docker compose up mongo redis` y apuntar los servicios
  a ellos). Es la forma recomendada para detectar bugs que solo aparecen
  con backing services reales.
- **Desarrollo rápido (menor paridad)**: para iterar sin levantar Mongo,
  se puede usar `DATABASE_URL=mongomock://localhost` (Mongo simulado en
  memoria). Cómodo para tests, pero NO idéntico a producción — usar solo
  para desarrollo veloz, no para validar comportamiento final.

## Procesos de administración (Factor XII)

Las tareas administrativas se ejecutan en el mismo entorno que la app,
como procesos puntuales:

- **Verificar salud del sistema**:
  ```
  docker compose exec orquestador python scripts/verificar_sistema.py
  ```
  Consulta el `/health` de cada microservicio y reporta el estado.

- **Vaciar la base de documentos** (útil en pruebas):
  ```
  docker compose exec mongo mongosh documentos_service \
    --eval "db.documents.deleteMany({}); db.counters.deleteMany({})"
  ```

## Logs (Factor XI)

Todos los servicios emiten logs por **stdout** (configurado en
`App/logging_config.py`), en formato consistente. Docker los captura; se
consultan con `docker compose logs <servicio>`. La app no escribe a
archivos ni rota logs — eso es responsabilidad del entorno.
