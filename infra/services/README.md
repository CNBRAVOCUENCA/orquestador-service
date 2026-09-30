# Servicios del stack

Cada subcarpeta contiene un `compose.yaml` para un solo componente. El archivo
`../docker-compose.yml` los incorpora mediante Docker Compose `include`.

- `traefik/`: gateway y balanceo de entrada.
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
