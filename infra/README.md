# Infraestructura — El-Destripador-de-PDFs

Levanta el **sistema completo** de microservicios, orquestado con Traefik y con
Redis para cache. ConsulCatalog está habilitado en paralelo con Docker, pero
la integración aún no está lista para un end-to-end rollout: los servicios
remotos fijados por `SERVICE_REF` todavía apuntan a commits sin el registro
Consul requerido y, por tanto, no aparecerán en Consul en esas imágenes.

**Bloqueo de despliegue:** no consideres activa la resolución dinámica para los
servicios remotos ni desactives Docker hasta que cada servicio publique o integre
su implementación de registro, se actualice aquí el `SERVICE_REF` a ese commit
publicado y se verifiquen en ejecución las rutas, checks de salud y recuperación
de ConsulCatalog. No cambies los pins por commits locales o inexistentes.

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
Cuando las imágenes implementen el registro y sus `SERVICE_REF` apunten a esos
commits, Consul descubrirá cada réplica por su dirección de contenedor y
Traefik consultará el catálogo cada 5 segundos. Hasta entonces, la migración es
solo configuración preparada: Docker provider y sus rutas continúan siendo la
ruta operativa. ConsulCatalog está configurado en paralelo y sus rutas usan
sufijo `-consul` para evitar colisiones. Ambos providers preservan las rutas
`Host`, `PathPrefix` y prioridades; ConsulCatalog solo enruta instancias con
check `passing`.

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

Después de publicar/actualizar todos los `SERVICE_REF` como se describe arriba,
la configuración usa Consul Catalog como único provider de descubrimiento.
Levanta un proyecto Compose aislado para validar fallos sin detener el stack
normal ni tocar sus volúmenes:

```powershell
docker compose -p prompt-final-check -f infra\docker-compose.yml `
  --env-file infra\.env up -d --build --wait --wait-timeout 300
python infra\tests\e2e\verificar_consul.py
docker compose -p prompt-final-check -f infra\docker-compose.yml `
  --env-file infra\.env down
```

La prueba comprueba que la ruta y el router de `resumen` están disponibles,
que Consul Catalog retira el router cuando se detiene el servicio, y que la
ruta se recupera al iniciarlo y sigue disponible después de reiniciar Consul.
También espera a que los cinco microservicios vuelvan a aparecer en el
catálogo. El script solo opera sobre `prompt-final-check`; no ejecutarlo con
el nombre del proyecto normal. `down` no elimina los volúmenes.

La prueba E2E del flujo incluye métricas Prometheus; espera hasta 45 segundos
para que el scrape publique métricas de los cinco servicios:

```powershell
python infra\tests\e2e\verificar_flujo.py
```

## Load testing

Ver [`vegeta/README.md`](vegeta/README.md) para medir peticiones por segundo/minuto
y el efecto del cache de Redis.
