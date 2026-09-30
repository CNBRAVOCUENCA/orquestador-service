# Infraestructura — El-Destripador-de-PDFs

Levanta el **sistema completo** de microservicios, orquestado con Traefik y con
Redis para cache.

## Qué levanta

| Servicio | Rol | URL (vía Traefik) |
|---|---|---|
| Traefik | Gateway / reverse proxy | dashboard en `http://localhost:8080` |
| documentos | Dueño del documento | `http://documentos.localhost` |
| extraccion | PDF → texto | `http://extraccion.localhost` |
| resumen | Texto → resumen IA | `http://resumen.localhost` |
| notificaciones | Estado del flujo | `http://notificaciones.localhost` |
| orquestador | Ejecuta la Saga | `http://orquestador.localhost` |
| redis | Cache de resultados | (interno) |
| mongo | Base de datos | (interno) |

## Archivos por servicio

`docker-compose.yml` es el punto de entrada y agrega las definiciones de
`services/<nombre>/compose.yaml`. Cada carpeta contiene la configuracion de un
componente; la red `web` y el volumen `mongo_data` se definen una sola vez en el
Compose principal. `App/services/` es codigo Python del orquestador y no contiene
archivos de despliegue.

Se requiere Docker Compose v2.20 o posterior por la directiva `include`.

## Levantar todo

Desde la raiz de `orquestador-service`, inicia el stack con:

```bash
docker compose --env-file .env -f infra/docker-compose.yml up -d --build
```

En `/etc/hosts` agregá:
```
127.0.0.1 orquestador.localhost documentos.localhost extraccion.localhost resumen.localhost notificaciones.localhost
```

En Windows, el archivo equivalente es `C:\Windows\System32\drivers\etc\hosts`.

Si `80` o `8080` ya están ocupados, desde la raíz del workspace usa
`docker-compose.local.yml`:

```powershell
$env:GEMINI_API_KEY = "tu_clave"
docker compose -p ms -f orquestador-service/infra/docker-compose.yml -f docker-compose.local.yml up -d --wait --wait-timeout 180
```

Con ese override, las URLs locales son:

| Recurso | URL |
|---|---|
| Gateway | `http://localhost:8081` |
| Dashboard Traefik | `http://localhost:8088` |
| Documentos | `http://documentos.localhost:8081` |
| Extracción | `http://extraccion.localhost:8081` |
| Resumen | `http://resumen.localhost:8081` |
| Notificaciones | `http://notificaciones.localhost:8081` |
| Orquestador | `http://orquestador.localhost:8081` |

## Probar el flujo completo

```bash
# 1. Subir un PDF a documentos
curl -X POST http://documentos.localhost/api/v1/documents \
  -F "name=Contrato" -F "file=@archivo.pdf;type=application/pdf"

# 2. Procesar ese documento con la Saga (extraer → resumir → notificar)
curl -X POST http://orquestador.localhost/api/v1/procesar/1

# 3. Ver el estado registrado
curl http://notificaciones.localhost/api/v1/estados/1
```

## Load testing

Ver [`vegeta/README.md`](vegeta/README.md) para medir peticiones por segundo/minuto
y el efecto del cache de Redis.
