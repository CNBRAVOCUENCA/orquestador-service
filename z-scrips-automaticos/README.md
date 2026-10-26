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

`windows/subir-documento.ps1` se conserva como herramienta PowerShell para subir
un PDF directamente; el flujo principal recomendado usa `subir-pdf.bat`.
