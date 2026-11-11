# orquestador-service

**Orquestador de la Saga** del sistema `El-Destripador-de-PDFs`. Coordina el flujo
completo de procesamiento de un documento llamando a los otros microservicios por
HTTP, en orden, con compensación ante fallos.

## El flujo (Saga orquestada)

```
POST /procesar/{document_id}
   │
   ├─(cache hit? → devuelve resultado guardado)
   │
   ├─ notificar "subido"
   ├─ extraccion-service   → extrae y persiste el texto en documentos-service
   │                         → notificar "extraido" solo tras confirmar
   ├─ resumen-service      → resumen   → notificar "resumido"
   ├─ notificar "notificado"  ✓ éxito → guardar en cache (Redis)
   │
   └─ si algún paso falla → COMPENSACIÓN: notificar "error" y cortar
```

Es una **Saga orquestada**: un coordinador central (este servicio) dirige los pasos
y decide la compensación si algo sale mal — porque al estar cada microservicio en su
propia base de datos, no existe una transacción única que los abarque a todos.
Extracción devuelve éxito únicamente después de que Documentos confirme la
persistencia de `extracted_text` y `is_processed=true`. Si falla esa escritura,
la Saga no continúa al resumen ni informa éxito; ejecuta la compensación habitual.

## Cache con Redis

Antes de procesar, consulta Redis: si el documento ya se procesó con éxito, devuelve
el resultado cacheado sin volver a llamar a extracción + resumen (ahorra la llamada
cara a la IA). Se puede saltear el cache con `?forzar=true`. Si `CACHE_ENABLED=true`,
Redis es una dependencia requerida para readiness. Para operar sin Redis, configura
`CACHE_ENABLED=false`; el orquestador usará un cache en memoria.

## Arquitectura (capas)

```
App/
├── api/Routes/saga.py            # POST /procesar/{id}
├── services/saga_service.py      # la Saga: pasos + compensación + cache
├── services/microservicios_client.py  # cliente HTTP hacia los 3 servicios
├── services/cache.py             # Cache (interfaz) + RedisCache + InMemoryCache
├── models/ · schemas/            # dominio y DTOs
└── config/settings.py            # URLs de los servicios, Redis, timeouts
test/                              # 14 tests (saga, compensación, cache, cliente, API)
```

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/api/v1/procesar/{document_id}` | Ejecuta la Saga. `?forzar=true` ignora el cache |
| GET | `/health` | Liveness: confirma que el proceso está activo; no comprueba dependencias |
| GET | `/ready` | Readiness: verifica dependencias y devuelve 503 si alguna requerida falla |

La respuesta siempre es 200 con el resultado: `{document_id, exito, estado_final, pasos_completados, resumen, error}`. Si la Saga falló, `exito=false` y `error` dice en qué paso.

El proxy y el healthcheck de Docker Compose deben usar `/ready` antes de enviar
trabajo. Una respuesta 200 con `status: "ok"` significa que Documentos,
Extracción, Resumen y Notificaciones respondieron correctamente; si el caché
está habilitado, también debe responder Redis. Una respuesta 503 con
`status: "error"` incluye en `dependencies` qué servicio falló y si fue un
timeout, un error de conexión o una respuesta HTTP no exitosa. Con
`CACHE_ENABLED=false`, Redis figura como `disabled` y no afecta la readiness.
`/health` permanece como liveness y seguirá respondiendo 200 mientras el
proceso pueda atender HTTP, aunque haya dependencias caídas.

## Ejecución con Docker

1. Instala Docker Desktop y Docker Compose v2.20 o posterior (se usa `include`).
2. Copia `.env.example` como `.env` y completa `GEMINI_API_KEY`.
   Configura también `INTERNAL_SERVICE_API_KEY` con un secreto aleatorio largo;
   se comparte únicamente entre `documentos-service` y `extraccion-service`.
3. Ejecuta el script multiplataforma:

```bash
python3 z-scrips-automaticos/linux/copiar_env.py
python3 z-scrips-automaticos/linux/iniciar.py
```

En Windows, ejecuta `z-scrips-automaticos\windows\copiar-env.bat` y
`z-scrips-automaticos\windows\iniciar.bat`. Los scripts Python para Linux están
en `z-scrips-automaticos/linux/`; consulta
`z-scrips-automaticos/README.md` para subir un PDF, ejecutar Vegeta y detener
el stack.

`infra/docker-compose.yml` es el punto de entrada e incluye una definicion por
componente desde `infra/services/<servicio>/compose.yaml`. Los servicios
dependientes se construyen desde sus repositorios GitHub, por lo que no es
necesario clonar carpetas hermanas. Las referencias remotas estan fijadas para
que el build sea reproducible. Para detener el sistema:

```bash
python3 z-scrips-automaticos/linux/detener.py
```

Cuando `cloudflared` inicie, muestra en sus logs la URL pública temporal. El
Swagger para cargar un documento está disponible en `/docs`; también se puede
usar `POST /api/v1/documents` con form-data `name` y `file`.

### Ejecución local con puertos alternativos

Si los puertos `80` o `8080` están ocupados, desde la raíz del workspace usa el
override local:

```powershell
docker compose -p ms -f orquestador-service/infra/docker-compose.yml -f docker-compose.local.yml up -d --wait --wait-timeout 180
```

En ese caso, la API queda publicada en `http://localhost:8081` y el dashboard de
Traefik en `http://localhost:8088`.

## Instalación y tests

El gestor de dependencias del proyecto es **uv** (version fijada: `0.11.32`).
`pyproject.toml` declara las dependencias y `uv.lock` fija las versiones exactas;
el mismo `uv.lock` se usa en desarrollo, Docker y CI.

```bash
uv sync --locked --extra dev
uv run --locked --extra dev pytest test/ -v
```

`--locked` falla si `uv.lock` no coincide con `pyproject.toml`, en vez de resolver
versiones nuevas en silencio. Si cambias una dependencia en `pyproject.toml`, corre
`uv lock` y commitea tambien `uv.lock`. Para comprobarlo: `uv lock --check`.

Ya no se documenta `pip install -e .`: instala versiones sin fijar y no es
reproducible. El `Dockerfile` y `infra/Dockerfile.remote` usan `uv sync --locked --no-dev`.

**14/14 en verde**: flujo feliz, compensación en cada paso, cache hit/miss, `forzar`, y el cliente HTTP mockeado con `respx`. No requieren Redis ni los otros servicios corriendo.

El workflow de GitHub Actions ejecuta automáticamente esta suite en cada push y
pull request.

## Resiliencia

Las políticas de retry, Circuit Breaker y Rate Limit, junto con su alcance y
pruebas reproducibles, están documentadas en
[`infra/RESILIENCE.md`](infra/RESILIENCE.md).

## Stack
Python 3.12+ · FastAPI · httpx · redis · pytest + respx

Escaneo de vulnerabilidades

El workflow .github/workflows/security-scan.yml corre en cada push a main, en cada pull request, una vez por semana (lunes) y a mano desde la pestaña Actions.

Qué se analiza
Job	Herramienta	Qué revisa	Cuándo falla
dependency-audit	pip-audit	Dependencias de runtime exportadas desde uv.lock (sin las de desarrollo)	Si alguna versión fijada tiene una vulnerabilidad conocida
image-scan	Trivy	La imagen Docker construida (paquetes del sistema y de Python)	Si hay vulnerabilidades de severidad HIGH o CRITICAL

No se usan .trivyignore ni --ignore-unfixed. Cualquier excepción futura debe agregarse con justificación escrita en el pull request.

Cómo correrlo localmente
bash
# Dependencias
uv export --frozen --no-dev --no-hashes --no-emit-project -o requirements-audit.txt
pip install pip-audit
pip-audit -r requirements-audit.txt --no-deps --strict --desc on

# Imagen
docker build -t pdf-service:scan .
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image --severity HIGH,CRITICAL --exit-code 1 pdf-service:scan
Cómo interpretar la salida
pip-audit lista paquete, versión instalada, ID de la vulnerabilidad (PYSEC o CVE) y versión que la corrige (Fix Versions). Solución: subir esa dependencia en pyproject.toml, regenerar con uv lock y volver a correr.
Trivy muestra una tabla con Library, Vulnerability (CVE), Severity, Installed Version y Fixed Version.
Si el paquete es del sistema (Alpine), revisa `Fixed Version` y actualiza el paquete
con `apk` o renueva la imagen base.
Si es de Python, se actualiza igual que con pip-audit.
Si Fixed Version está vacío, todavía no hay parche: se registra en un issue y se revisa en la corrida semanal.
Exit code 0 = sin hallazgos que bloqueen. Exit code 1 = hay que corregir antes de mergear.

## Observabilidad del flujo completo

El stack incluye Prometheus + Grafana para las métricas HTTP de baja cardinalidad y **Jaeger** como backend de trazas distribuidas con OpenTelemetry.

### Qué se mide

- `http_requests_total`: tráfico por servicio, método, ruta y estado HTTP.
- `http_request_duration_seconds`: latencia de respuesta por servicio.
- **Trazas OpenTelemetry**: cada petición entrante crea un span (FastAPI) y cada llamada saliente con httpx crea un span hijo e inyecta el header W3C `traceparent`, así una subida recorre en una sola traza orquestador → documentos → extracción → resumen → notificaciones. Los spans se exportan por OTLP/HTTP a Jaeger (`OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4318`); sin esa variable las trazas quedan desactivadas. Código: `App/tracing.py` en cada servicio.
- `x-trace-id`: cada respuesta devuelve el trace id de OpenTelemetry, para buscar la traza en Jaeger.
- La etiqueta `route` de las métricas es la plantilla de la ruta (`/api/v1/documents/{doc_id}`), no la URL concreta; lo que no coincide con ninguna ruta va a `sin_ruta`.
- Los logs incluyen `trace_id` en stdout para correlacionar eventos del mismo flujo.

No se registran documentos, textos completos, prompts, headers ni API keys: los spans solo llevan método, ruta, estado y duración, y `/health`, `/ready` y `/metrics` no generan spans. Las métricas usan solo etiquetas de baja cardinalidad: servicio, método, ruta y estado.

### Levantar el stack de observabilidad

```bash
docker compose -f orquestador-service/infra/docker-compose.yml up -d --wait
```

Luego puede abrirse:

- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000` (usuario `admin`, clave `admin`), con Prometheus y Jaeger como fuentes de datos
- Jaeger (trazas): `http://localhost:16686` (buscar por servicio o pegar el `x-trace-id` de una respuesta)

La vista predefinida `Microservicios - Flujo y errores` ya queda conectada a Prometheus.

### Consultas útiles

```bash
# tráfico por servicio
curl 'http://localhost:9090/api/v1/query?query=sum%20by%20(service)%20(rate(http_requests_total%5B5m%5D))'

# errores 5xx
curl 'http://localhost:9090/api/v1/query?query=sum%20by%20(service)%20(rate(http_requests_total%7Bstatus=~"5.."%7D%5B5m%5D))'

# p95 de latencia
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.95,%20sum%20by%20(le,service)%20(rate(http_request_duration_seconds_bucket%5B5m%5D)))'
```

### Apagar

```bash
docker compose -f orquestador-service/infra/docker-compose.yml down
```

### Prueba reproducible end-to-end

`python infra/tests/e2e/verificar_flujo.py` sube un PDF, sigue la Saga y comprueba que su traza está en Jaeger con spans de los 5 servicios y que Prometheus tiene métricas de los 5.

### Si se cae la observabilidad

El flujo de negocio no se interrumpe: los servicios no dependen de Jaeger ni de Prometheus. Los spans se exportan en segundo plano con timeout de 2 s y, si Jaeger no responde, se descartan; las métricas se vuelven a recolectar en el siguiente scrape.
