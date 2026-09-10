# Infraestructura — El-Destripador-de-PDFs

Levanta el **sistema completo** de microservicios, orquestado con Traefik y con
Redis para cache.

## Qué levanta

| Servicio | Rol | URL (vía Traefik) |
|---|---|---|
| Traefik | Gateway / reverse proxy | dashboard en `localhost:8080` |
| documentos | Dueño del documento | `documentos.localhost` |
| extraccion | PDF → texto | `extraccion.localhost` |
| resumen | Texto → resumen IA | `resumen.localhost` |
| notificaciones | Estado del flujo | `notificaciones.localhost` |
| orquestador | Ejecuta la Saga | `orquestador.localhost` |
| redis | Cache de resultados | (interno) |
| mongo | Base de datos | (interno) |

## Levantar todo

Cloná los 5 microservicios como carpetas hermanas y desde `infra/`:

```bash
export GEMINI_API_KEY=tu_clave   # para que resumen funcione de verdad
docker compose up --build
```

En `/etc/hosts` agregá:
```
127.0.0.1 orquestador.localhost documentos.localhost extraccion.localhost resumen.localhost notificaciones.localhost
```

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
