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

## Instalación y tests

Con **uv** (recomendado):

```bash
uv sync --extra dev
uv run --extra dev pytest test/ -v
```

O con pip: `pip install -e ".[dev]" && pytest test/ -v`

**14/14 en verde**: flujo feliz, compensación en cada paso, cache hit/miss, `forzar`, y el cliente HTTP mockeado con `respx`. No requieren Redis ni los otros servicios corriendo.

## Pendiente futuro
Retry y Circuit Breaker en `MicroserviciosClient`.

## Stack
Python 3.12+ · FastAPI · httpx · redis · pytest + respx
