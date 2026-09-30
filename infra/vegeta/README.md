# Load testing con Vegeta

[Vegeta](https://github.com/tsenart/vegeta) mide cuántas peticiones por segundo
aguanta el sistema y con qué latencia. Corre **por fuera** de los microservicios:
les dispara tráfico y mide la respuesta.

## Requisitos

- El stack levantado con `iniciar.bat` desde Windows o `docker compose up --build`
  desde `infra/`.
- Docker Desktop activo. Vegeta corre dentro de Docker; no hace falta instalarlo
  en Windows.
- El PDF que se vaya a probar debe ser valido y no estar duplicado.

## Uso en Windows con los archivos BAT

Desde la raiz de `orquestador-service`, primero levanta el stack si todavia no
esta activo:

```powershell
.\iniciar.bat
```

Luego ejecuta los dos BAT desde la raiz, en este orden:

```powershell
.\subir-pdf.bat
.\ejecutar-vegeta.bat
```

`subir-pdf.bat` pide la ruta del PDF y un nombre, lo sube a documentos-service y
guarda el `document_id` en `infra/vegeta/document-id.txt` y
`infra/vegeta/extractor-body.json`. `ejecutar-vegeta.bat` usa ese ID, pregunta
la tasa y duracion (por defecto 2 solicitudes/s durante 5s), ejecuta Vegeta
contra el extractor pasando por Traefik y muestra el reporte. Ambos BAT y
`subir-documento.ps1` estan junto a `iniciar.bat`.

El ataque usa el endpoint del extractor directamente, no el orquestador. La
primera vez que se ejecute, Docker puede descargar `peterevans/vegeta:latest`;
si ya esta disponible localmente, no necesita descargarla de nuevo. Los
resultados quedan en archivos `extractor-results-<fecha>.bin` y
`extractor-report-<fecha>.txt` dentro de `infra/vegeta`.

Para probar otro PDF, vuelve a ejecutar `subir-pdf.bat` y luego
`ejecutar-vegeta.bat`. Si el servicio responde HTTP 409 porque el PDF ya
existe, usa un PDF diferente o conserva el ID original; no lo subas de nuevo.

## Correr un ataque

**5 peticiones por segundo durante 30 segundos**, contra el orquestador:

```bash
vegeta attack -targets=targets.txt -rate=5 -duration=30s | vegeta report
```

**Peticiones por minuto**: `-rate` es por segundo, así que para "N por minuto"
usá `-rate=N/60`. Por ejemplo, 300/min:

```bash
vegeta attack -targets=targets.txt -rate=300/1m -duration=1m | vegeta report
```

## Ver el efecto del cache de Redis

La primera petición a un documento ejecuta toda la Saga (lenta: extrae + resume
con IA). Las siguientes al mismo documento salen del cache de Redis (rápidas).
Vegeta lo va a mostrar como una latencia media mucho más baja al repetir el mismo
`document_id`. Para medir SIN cache, agregá `?forzar=true` en el target:

```
POST http://orquestador.localhost/api/v1/procesar/1?forzar=true
```

## Reporte gráfico (histograma de latencias)

```bash
vegeta attack -targets=targets.txt -rate=10 -duration=30s > results.bin
vegeta report -type=hist[0,10ms,50ms,100ms,500ms,1s] results.bin
```

## Interpretación

- **Requests/sec**: throughput real que soportó el sistema.
- **Latencies (mean, p95, p99)**: cuánto tardó cada petición. p95 = el 95% de las
  peticiones fueron más rápidas que ese valor.
- **Success ratio**: qué porcentaje respondió 200. Si baja al subir el `-rate`,
  encontraste el techo del sistema.
