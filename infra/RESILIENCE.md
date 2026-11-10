# Políticas de resiliencia

## Alcance y capa

Traefik está fijado por digest en `services/traefik/compose.yaml`; esa imagen
reporta la versión 3.6.25. Esta versión incluye los middlewares `rateLimit` y
`circuitBreaker`, por lo que no se instala ningún plugin ni proveedor externo.

El entrypoint público `web` publica las rutas de API con Rate Limit y Circuit
Breaker. El entrypoint `web-internal` escucha en el puerto 8081 dentro de la red
de Compose, sin publicarlo en el host. El Orquestador llama a los otros servicios
por ese entrypoint: así sus solicitudes también pasan por el Circuit Breaker,
pero no consumen el cupo público de Rate Limit. Los routers internos solo
aceptan las rutas API necesarias y aplican Circuit Breaker.

Rate Limit usa un token bucket local por router: 10 solicitudes por segundo en
promedio y una ráfaga de 20. Si se ejecutan varias réplicas de Traefik, cada una
tendrá su propio cupo; este límite no es global/distribuido. El Circuit Breaker
se abre cuando más del 50% de las respuestas son 5xx o cuando la proporción de
errores de red supera el 20%. Comprueba cada segundo, devuelve 503 mientras
está abierto, espera 5 segundos antes de probar recuperación y usa una ventana
de recuperación de 10 segundos. Traefik mantiene estado independiente por
router.

## Política de Retry

El cliente del Orquestador y Gemini envían `POST`. No se reintentan
automáticamente: las operaciones no tienen una clave/contrato de idempotencia
que permita descartar duplicados, y repetir generación en Gemini puede duplicar
costos. El Circuit Breaker devuelve 503 cuando está abierto; el Rate Limit
devuelve 429. Ambos errores se entregan al flujo existente como fallos, sin
bucle de reintentos.

| Operación | Reintentos automáticos | Intentos máximos | Espera/backoff | Presupuesto |
|---|---:|---:|---|---|
| Orquestador → Documentos, Extracción, Resumen y Notificaciones (`POST`) | No | 1 | Ninguno | Una llamada; timeout HTTP configurado en 120 s |
| Resumen → Gemini (`POST generateContent`) | No | 1 | Ninguno | Una llamada; timeout HTTP de 120 s |
| Rechazo 429, respuesta 5xx o error de transporte | No | 1 en total | Ninguno | Se propaga el error; no se repite la operación |

Si en el futuro se agrega una operación idempotente o una clave de idempotencia,
su política de retry deberá definirse por separado con máximo de intentos,
backoff con jitter y plazo total antes de habilitar repeticiones.

## Pruebas

La prueba de integración ejecuta la imagen real de Traefik fijada por digest y
usa el mismo archivo de middlewares que el stack:

```powershell
docker compose -p prompt12-resilience -f infra/tests/resilience/compose.yaml up --build --abort-on-container-exit --exit-code-from test
docker compose -p prompt12-resilience -f infra/tests/resilience/compose.yaml down --remove-orphans
```

La prueba comprueba una respuesta normal, que el Rate Limit público produzca
429, que el Circuit Breaker abra ante errores 5xx, y que permita tráfico otra
vez al recuperarse el backend. También verifica que el entrypoint interno no
aplique el Rate Limit público.
