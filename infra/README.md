# Infraestructura — El-Destripador-de-PDFs

Levanta el **sistema completo** de microservicios, orquestado con Traefik y con
Redis para cache.

## Qué levanta

| Servicio | Rol | URL (vía Traefik) |
|---|---|---|
| Traefik | Gateway / reverse proxy (Consul Catalog) | dashboard en `http://localhost:8080` |
| Consul | Catálogo de servicios y health checks | (interno, `consul:8500`) |
| documentos | Dueño del documento | `http://documentos.localhost` |
| extraccion | PDF → texto | `http://extraccion.localhost` |
| resumen | Texto → resumen IA | `http://resumen.localhost` |
| notificaciones | Estado del flujo | `http://notificaciones.localhost` |
| orquestador | Ejecuta la Saga | `http://orquestador.localhost` |
| redis | Cache de resultados | (interno) |
| mongo | Base de datos | (interno) |

El host de entrada del orquestador se configura con `ORQUESTADOR_HOST` en el
archivo `.env`. Su valor predeterminado es `orquestador.localhost`; si se cambia,
usa ese mismo nombre en el navegador y actualiza la entrada correspondiente
del archivo `hosts` de Windows.

## Archivos por servicio

`docker-compose.yml` es el punto de entrada y agrega las definiciones de
`services/<nombre>/compose.yaml`. Cada carpeta contiene la configuracion de un
componente; la red `web` y el volumen `mongo_data` se definen una sola vez en el
Compose principal. `App/services/` es codigo Python del orquestador y no contiene
archivos de despliegue.

Se requiere Docker Compose v2.20 o posterior por la directiva `include`.
Consul descubre cada réplica por su dirección de contenedor y Traefik consulta
el catálogo cada 5 segundos. La migración mantiene temporalmente activos el
provider Docker y sus rutas y prueba ConsulCatalog en paralelo; las rutas nuevas
usan sufijo `-consul` para evitar colisiones. No desactives Docker ni retires
sus etiquetas hasta verificar end-to-end las rutas Consul, los checks de salud
y la recuperación. Ambos providers preservan las rutas `Host`, `PathPrefix` y
prioridades existentes; ConsulCatalog solo enruta instancias con check
`passing`.

`CONSUL_HTTP_TOKEN` es opcional. Proporciónalo mediante un gestor de secretos
externo o un archivo `.env` local excluido de Git; no lo guardes en el
repositorio. El token no se incluye en logs. Si Consul está configurado en la
app, el arranque falla si no puede registrar el servicio; al apagarla se
desregistra del agente.

Los cuerpos de solicitud de ejemplo están en `infra/examples/`; resultados de
Vegeta y sus configuraciones están en `infra/vegeta/`.

## Dependencias reproducibles

Todas las imagenes instalan con `uv sync --locked --no-dev` a partir del `uv.lock`
del servicio. `Dockerfile.remote` clona cada servicio en el commit fijado por
`SERVICE_REF` y copia su `pyproject.toml` y su `uv.lock`: al subir un servicio a
un commit nuevo, ese commit debe incluir su `uv.lock` actualizado (`uv lock`),
o el build falla a proposito en lugar de instalar versiones distintas. Los
Dockerfiles usan etapas separadas para instalar dependencias; las imagenes
finales contienen el entorno virtual y el codigo de la aplicacion, no las
herramientas de construccion (`git` ni `uv`). Las dependencias se instalan antes
de copiar el codigo para reutilizar la capa cuando solo cambia la aplicacion.

## Levantar todo

Desde la raiz de `orquestador-service`, inicia el stack con Python:

```bash
python3 z-scrips-automaticos/linux/copiar_env.py
python3 z-scrips-automaticos/linux/iniciar.py
```

En Windows están disponibles los lanzadores
`z-scrips-automaticos\windows\copiar-env.bat` y
`z-scrips-automaticos\windows\iniciar.bat`. Los scripts Python están en
`z-scrips-automaticos/linux/`; `z-scrips-automaticos/README.md` documenta todos
los comandos.

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

### Verificación reproducible de descubrimiento y recuperación

Desde la raíz del repositorio, crea un `.env` local (no versionado) con la
configuración de la sección `.env.example`. Para validar la interpolación de
Compose sin usar un secreto real:

```powershell
$env:CONSUL_HTTP_TOKEN = "compose-validation-only"
docker compose -f infra\docker-compose.yml config --quiet
Remove-Item Env:\CONSUL_HTTP_TOKEN
```

Inicia el stack y espera servicios saludables:

```powershell
docker compose -f infra\docker-compose.yml up -d --build --wait --wait-timeout 300
```

Confirma que los servicios estén en el catálogo, sus checks pasen y que los
routers y servicios `-consul@consulcatalog` aparezcan en la API de Traefik:

```powershell
docker compose -f infra\docker-compose.yml exec consul consul catalog services
docker compose -f infra\docker-compose.yml exec consul consul health checks
curl.exe http://localhost:8080/api/http/routers/documentos-consul@consulcatalog
curl.exe http://localhost:8080/api/http/services/documentos-consul@consulcatalog
curl.exe -H "Host: documentos.localhost" http://localhost/api/v1/documents
curl.exe -H "Host: orquestador.localhost" http://localhost/health
```

Como Docker y ConsulCatalog están activos simultáneamente, un smoke test de URL
puede ser atendido por cualquiera de los providers. Verifica específicamente el
`*-consul@consulcatalog` en la API de Traefik y su lista de servidores para
probar la ruta Consul. Para verificar recuperación, detén una instancia,
confirma que su check pasa a crítico y que su IP desaparece de los servidores
Consul de Traefik; vuelve a iniciarla y confirma que el check vuelve a `passing`
y la IP reaparece. Esto verifica ConsulCatalog sin desactivar las rutas Docker.
Al terminar, limpia el stack con
`docker compose -f infra\docker-compose.yml down`.

## Load testing

Ver [`vegeta/README.md`](vegeta/README.md) para medir peticiones por segundo/minuto
y el efecto del cache de Redis.
