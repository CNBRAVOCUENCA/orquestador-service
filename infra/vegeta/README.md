# Load testing con Vegeta

[Vegeta](https://github.com/tsenart/vegeta) mide cuántas peticiones por segundo
aguanta el sistema y con qué latencia. Corre **por fuera** de los microservicios:
les dispara tráfico y mide la respuesta.

## Requisitos

- El sistema completo levantado: `docker compose up --build` (desde `infra/`)
- Vegeta instalado: `go install github.com/tsenart/vegeta@latest`
  (o `brew install vegeta` en Mac)
- En `/etc/hosts` agregar: `127.0.0.1 orquestador.localhost documentos.localhost`

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
