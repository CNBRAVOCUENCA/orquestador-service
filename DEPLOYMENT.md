# Despliegue y operación (12-Factor App)

Este documento describe cómo se cumplen los factores de build/release/run,
paridad dev/prod y procesos de administración.

## Build / Release / Run separados (Factor V)

- **Nombre de imagen**: `IMAGE_NAMESPACE/<servicio>:<commit-sha>`. Los cinco
  servicios usan `documentos`, `extraccion`, `resumen`, `notificaciones` y
  `orquestador` como nombres de imagen. `IMAGE_NAMESPACE=pdf-ms` es el namespace
  local predeterminado; para publicar, usa el namespace del registry, por ejemplo
  `ghcr.io/cnbravocuenca/pdf-ms`.
- **Versionado reproducible**: `DOCUMENTOS_VERSION`, `EXTRACCION_VERSION`,
  `RESUMEN_VERSION` y `NOTIFICACIONES_VERSION` son los SHA completos de los
  commits de los repositorios respectivos. Cada variable alimenta tanto el
  `SERVICE_REF` del build remoto como el tag de la imagen, evitando que el tag
  anuncie un commit distinto del que se construyó. `ORQUESTADOR_VERSION` es el
  SHA del commit de este repositorio que se construye. El tag local `dev` del
  ejemplo es solo para desarrollo, no para releases.
- **Build**: configura los cinco SHA en `.env` y construye exactamente esas
  imágenes con la verificación de que `ORQUESTADOR_VERSION` coincide con el
  commit actual:
  ```bash
  python3 z-scrips-automaticos/linux/iniciar.py --build-release
  ```
- **Release**: para publicar las imágenes, configura `IMAGE_NAMESPACE` con el
  namespace autenticado del registry y ejecuta:
  ```bash
  docker compose --env-file .env -f infra/docker-compose.yml \
    push documentos extraccion resumen notificaciones orquestador
  ```
  Configura el registry para rechazar la sobrescritura de tags y no vuelvas a
  publicar una versión existente. No se publica automáticamente. Sin registry,
  las imágenes quedan disponibles localmente con el namespace `pdf-ms`. Si el
  registry está disponible antes del build, configura su namespace desde el
  principio. Si ya construiste localmente, retaggea y publica esas mismas
  imágenes, sin reconstruirlas; por ejemplo:
  ```bash
  docker image tag pdf-ms/documentos:<DOCUMENTOS_VERSION> \
    ghcr.io/cnbravocuenca/pdf-ms/documentos:<DOCUMENTOS_VERSION>
  docker image push ghcr.io/cnbravocuenca/pdf-ms/documentos:<DOCUMENTOS_VERSION>
  ```
  Repite para los otros cuatro servicios con su imagen y variable `*_VERSION`.
  No uses `latest` ni `dev` en producción.
- **Run**: en el host de despliegue, configura `.env` con los SHA de la release,
  inicia sesión en el registry y ejecuta
  `python3 z-scrips-automaticos/linux/iniciar.py --release` (en Windows:
  `z-scrips-automaticos\windows\iniciar.bat --release`). El modo release exige
  SHA completos, hace `docker compose pull` y arranca con `--no-build`; por eso
  nunca reconstruye o reasigna silenciosamente una etiqueta.
  Si no hay registry, construye con `--build-release` y ejecuta las imágenes
  locales con `--local-release`, que también valida los SHA pero no intenta
  descargarlos.

### Qué queda fijado y qué no

| Imagen | Cómo se fija | Motivo |
|---|---|---|
| Las 5 aplicaciones (`pdf-ms/<servicio>`) | Tag = SHA completo del commit (`*_VERSION`), que también es el `SERVICE_REF` del build | Reproducible y trazable al código; rollback = volver a los SHA anteriores |
| Traefik, MongoDB, Redis, cloudflared | Digest `@sha256:` | Infraestructura inmutable |
| Consul, Prometheus, Grafana | `tag@sha256:` (versión legible + digest) | Inmutable; el tag queda solo como referencia para personas |
| `python:3.12-slim` / `python:3.12-alpine` (base de los Dockerfile) | Tag, sin digest, a propósito | Se reconstruye con `docker compose build --pull` para recibir parches de seguridad del sistema; Trivy en CI controla la imagen resultante. La imagen de aplicación construida sí queda fija por su SHA |

Para actualizar una imagen de infraestructura se cambia el digest en su
`compose.yaml` en un commit propio (nunca se usa `latest`). Los digests son los
del índice multi-arquitectura publicado en Docker Hub para ese tag.

### Rollback

Para volver a una release, restaura en `.env` los cinco SHA de imagen usados por
esa release anterior (y el mismo `IMAGE_NAMESPACE`). Para imágenes en el
registry ejecuta `iniciar.py --release`; para imágenes locales, ejecuta
`iniciar.py --local-release`. No reutilices un tag para contenido nuevo: un
cambio de código requiere un commit/tag SHA nuevo.

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
