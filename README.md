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
   ├─ extraccion-service   → texto     → notificar "extraido"
   ├─ resumen-service      → resumen   → notificar "resumido"
   ├─ notificar "notificado"  ✓ éxito → guardar en cache (Redis)
   │
   └─ si algún paso falla → COMPENSACIÓN: notificar "error" y cortar
```

Es una **Saga orquestada**: un coordinador central (este servicio) dirige los pasos
y decide la compensación si algo sale mal — porque al estar cada microservicio en su
propia base de datos, no existe una transacción única que los abarque a todos.

## Cache con Redis

Antes de procesar, consulta Redis: si el documento ya se procesó con éxito, devuelve
el resultado cacheado sin volver a llamar a extracción + resumen (ahorra la llamada
cara a la IA). Se puede saltear el cache con `?forzar=true`. Si Redis no está
disponible, el servicio degrada a un cache en memoria automáticamente.

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
| GET | `/health` | Health check |

La respuesta siempre es 200 con el resultado: `{document_id, exito, estado_final, pasos_completados, resumen, error}`. Si la Saga falló, `exito=false` y `error` dice en qué paso.

## Ejecución con Docker

1. Instala Docker Desktop y Docker Compose v2.20 o posterior (se usa `include`).
2. Copia `.env.example` como `.env` y completa `GEMINI_API_KEY`.
3. Ejecuta `iniciar.bat` en Windows o el siguiente comando en cualquier sistema:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up -d --build --wait --wait-timeout 180
```

`infra/docker-compose.yml` es el punto de entrada e incluye una definicion por
componente desde `infra/services/<servicio>/compose.yaml`. Los servicios
dependientes se construyen desde sus repositorios GitHub, por lo que no es
necesario clonar carpetas hermanas. Las referencias remotas estan fijadas para
que el build sea reproducible. Para detener el sistema:

```bash
docker compose --env-file .env -f infra/docker-compose.yml down
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

Con **uv** (recomendado):

```bash
uv sync --extra dev
uv run --extra dev pytest test/ -v
```

O con pip: `pip install -e ".[dev]" && pytest test/ -v`

**14/14 en verde**: flujo feliz, compensación en cada paso, cache hit/miss, `forzar`, y el cliente HTTP mockeado con `respx`. No requieren Redis ni los otros servicios corriendo.

El workflow de GitHub Actions ejecuta automáticamente esta suite en cada push y
pull request.

## Pendiente futuro
Retry y Circuit Breaker en `MicroserviciosClient`.

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
Si el paquete es del sistema (Debian), conviene actualizar la imagen base o reconstruir.
Si es de Python, se actualiza igual que con pip-audit.
Si Fixed Version está vacío, todavía no hay parche: se registra en un issue y se revisa en la corrida semanal.
Exit code 0 = sin hallazgos que bloqueen. Exit code 1 = hay que corregir antes de mergear.
