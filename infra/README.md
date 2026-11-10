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

Las cinco imágenes de aplicación usan el nombre
`IMAGE_NAMESPACE/<servicio>:<commit-sha>`. Las variables `*_VERSION` de `.env`
fijan sus tags; para los cuatro servicios remotos, la misma variable determina
`SERVICE_REF` y el tag de imagen. El valor `ORQUESTADOR_VERSION=dev` es solo
para builds locales. Consulta [DEPLOYMENT.md](../DEPLOYMENT.md) para el flujo de
build/publicación, el modo de ejecución de una release y el rollback.

## Levantar todo

Desde la raiz de `orquestador-service`, inicia el stack con Python:

```bash
python3 z-scrips-automaticos/linux/copiar_env.py
python3 z-scrips-automaticos/linux/iniciar.py
```

El inicio normal construye las aplicaciones desde sus referencias fijadas.
Para construir una release, establece los SHA en `.env` (el del orquestador
debe coincidir con `git rev-parse HEAD`) y ejecuta
`python3 z-scrips-automaticos/linux/iniciar.py --build-release`. Para ejecutar
imágenes ya publicadas, establece los SHA y `IMAGE_NAMESPACE` de esa release en
`.env`, autentícate en el registry y usa
`python3 z-scrips-automaticos/linux/iniciar.py --release`; ese modo valida los
SHA, descarga las imágenes y no las reconstruye. El lanzador Windows acepta
los modos `z-scrips-automaticos\windows\iniciar.bat --build-release` y
`z-scrips-automaticos\windows\iniciar.bat --release`. Si no hay registry,
`--local-release` ejecuta las imágenes ya construidas en el daemon local sin
intentar descargarlas.

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

## Load testing

Ver [`vegeta/README.md`](vegeta/README.md) para medir peticiones por segundo/minuto
y el efecto del cache de Redis.
