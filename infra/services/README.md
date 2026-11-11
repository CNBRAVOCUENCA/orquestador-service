# Servicios del stack

Cada subcarpeta contiene un `compose.yaml` para un solo componente. El archivo
`../docker-compose.yml` los incorpora mediante Docker Compose `include`.

- `traefik/`: gateway y balanceo de entrada.
- `consul/`: catálogo de servicios y health checks.
- `cloudflared/`: tunel publico opcional del gateway.
- `mongo/`: almacenamiento de documentos y notificaciones.
- `redis/`: cache de resultados de la Saga.
- `documentos/`: servicio de documentos.
- `extraccion/`: servicio de extraccion de PDF.
- `resumen/`: servicio de resumen.
- `notificaciones/`: registro de estados.
- `orquestador/`: aplicacion de este repositorio.

Para agregar un componente, crea `services/<nombre>/compose.yaml` con su entrada
de `services:` y agrega su ruta a `include` en `infra/docker-compose.yml`.
Los nombres `web` y `mongo_data` son recursos compartidos definidos en el
Compose principal. Las rutas de `build.context` se resuelven relativas al
`compose.yaml` de cada componente.

Descubrimiento de servicios: **Consul es el único proveedor de rutas de Traefik**
(el provider Docker está desactivado y Traefik ya no monta el socket de Docker).

- Cada servicio se registra al arrancar en Consul con `CONSUL_SERVICE_NAME`,
  `CONSUL_SERVICE_PORT` y sus rutas en `CONSUL_SERVICE_TAGS` (routers públicos en
  `web`, internos en `web-internal`, y el `Host(...)` de cada servicio). Los
  `SERVICE_REF` de `.env.example` apuntan a commits publicados que incluyen ese
  registro.
- ID de instancia: `<servicio>-<hostname>`; cada réplica tiene un ID único.
- Health check HTTP a `/health` cada 10 s; con `strictchecks=passing` Traefik solo
  envía tráfico a instancias sanas. Si una instancia falla deja de recibir tráfico
  y, tras 1 minuto en estado crítico, Consul la da de baja.
- Al apagarse, cada servicio se da de baja. Al arrancar, borra registros viejos que
  apunten a su misma IP:puerto (Docker reutiliza IP y un registro huérfano pasaría
  el health check contra el contenedor nuevo).
- Reinicio de Consul: corre como servidor con datos en el volumen `consul_data`,
  así que conserva el catálogo al reiniciarse. Mientras Consul está caído, Traefik
  mantiene la última configuración conocida; las rutas nuevas se publican cuando
  Consul vuelve.
- Rutas públicas protegidas con la cadena `api-publico@file` (Rate Limit + Circuit
  Breaker, ver `infra/RESILIENCE.md`); las internas, con `api-circuitbreaker@file`.
  Como `CONSUL_SERVICE_TAGS` se separa por comas, ningún valor de etiqueta lleva comas.

`CONSUL_HTTP_TOKEN` es opcional: configuralo
desde un gestor de secretos o un `.env` local ignorado por Git, nunca en un
archivo versionado. Los tokens no se escriben en logs.
