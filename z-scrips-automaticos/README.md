# Scripts automáticos para Windows y Linux

Los scripts están separados por sistema operativo: `windows/` contiene
lanzadores `.bat` y `linux/` contiene los scripts portables de Python. Los
lanzadores de Windows ejecutan los scripts Python compartidos de `linux/`.

## Requisitos

- Python 3.11 o posterior.
- Docker con Docker Compose v2 y el daemon iniciado.
- `.env` configurado. `copiar_env.py` lo crea desde `.env.example`.
- `GEMINI_API_KEY` configurada para generar resúmenes reales.

Ejecuta los comandos desde la raíz de `orquestador-service`. Los scripts también
resuelven la raíz del proyecto por su ubicación, así que no dependen del
directorio actual.

## Linux / macOS

```bash
python3 z-scrips-automaticos/linux/copiar_env.py
python3 z-scrips-automaticos/linux/iniciar.py
python3 z-scrips-automaticos/linux/subir_pdf.py
python3 z-scrips-automaticos/linux/ejecutar_vegeta.py
python3 z-scrips-automaticos/linux/detener.py
```

`iniciar.py` construye las imágenes locales para desarrollo. Para construir las
imágenes de una release, configura en `.env` el namespace y los SHA de los cinco
servicios (el SHA del orquestador debe ser el commit actual) y ejecuta:

```bash
python3 z-scrips-automaticos/linux/iniciar.py --build-release
```

Publica luego las cinco imágenes con los comandos de
[DEPLOYMENT.md](../DEPLOYMENT.md). Para ejecutar una release publicada sin
reconstruirla, configura `.env` con el mismo namespace y SHA y usa
`python3 z-scrips-automaticos/linux/iniciar.py --release`. Ese modo valida los
SHA, descarga las imágenes y arranca con `--no-build`. Si no hay registry,
construye primero con `--build-release` y ejecuta con
`python3 z-scrips-automaticos/linux/iniciar.py --local-release`; este modo
valida los SHA y usa las imágenes locales sin intentar descargarlas.

`subir_pdf.py` pregunta la ruta del PDF y el nombre del documento. Después
guarda el `document_id` para Vegeta en `infra/vegeta/`.
`ejecutar_vegeta.py` pregunta tasa y duración; por defecto usa 2 solicitudes/s
durante 5 segundos.

Si el puerto 80 no está disponible, define `DOCUMENTOS_UPLOAD_URL` con la ruta
del gateway alternativo (por ejemplo `http://localhost:8081/api/v1/documents`).
`DOCUMENTOS_UPLOAD_HOST` permite indicar el host HTTP de Traefik; por defecto es
`documentos.localhost`.

## Windows

Desde la raíz del repositorio se pueden ejecutar los BAT con:

```powershell
.\z-scrips-automaticos\windows\copiar-env.bat
.\z-scrips-automaticos\windows\iniciar.bat
.\z-scrips-automaticos\windows\subir-pdf.bat
.\z-scrips-automaticos\windows\ejecutar-vegeta.bat
.\z-scrips-automaticos\windows\detener.bat
```

Para construir una release validada, ejecuta
`.\z-scrips-automaticos\windows\iniciar.bat --build-release`. Para desplegar
imágenes publicadas en lugar de reconstruirlas, ejecuta
`.\z-scrips-automaticos\windows\iniciar.bat --release` después de configurar
los SHA y el namespace del registry en `.env`. Sin registry, usa
`.\z-scrips-automaticos\windows\iniciar.bat --local-release` para arrancar las
imágenes ya construidas en el daemon local.

`windows/subir-documento.ps1` se conserva como herramienta PowerShell para subir
un PDF directamente; el flujo principal recomendado usa `subir-pdf.bat`.
