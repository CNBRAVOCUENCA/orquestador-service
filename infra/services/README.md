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

Los servicios HTTP que ya incluyen la implementación de registro se registran
en Consul con `CONSUL_SERVICE_NAME`, `CONSUL_SERVICE_PORT` y tags Traefik en
`CONSUL_SERVICE_TAGS`; Traefik solo publica servicios saludables. Los
`SERVICE_REF` actuales de los servicios remotos aún fijan commits sin ese
registro, así que las imágenes remotas integradas no se registran y Consul no
está activo para ellas. El rollout end-to-end queda bloqueado hasta que cada
servicio publique/integre la implementación y se actualicen todos sus
`SERVICE_REF` a commits publicados. No apuntes a commits locales o inexistentes.
La migración está en estado dual temporal: Docker provider y etiquetas Docker
existentes siguen activos mientras ConsulCatalog usa nombres de router y
servicio con sufijo `-consul`. No se debe cortar el provider Docker hasta
verificar en ejecución rutas Consul, checks de salud y recuperación.
`CONSUL_HTTP_TOKEN` es opcional: configuralo
desde un gestor de secretos o un `.env` local ignorado por Git, nunca en un
archivo versionado. Los tokens no se escriben en logs.
