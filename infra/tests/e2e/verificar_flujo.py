"""Prueba end-to-end reproducible del flujo completo (prompt 7).

Requiere el stack levantado (`docker compose up -d` en `infra/`). Solo usa la
biblioteca estándar de Python, así se corre sin instalar nada:

    python infra/tests/e2e/verificar_flujo.py
    python infra/tests/e2e/verificar_flujo.py --base http://localhost

Qué comprueba:
1. `/ready` del orquestador responde 200 con todas las dependencias en "ok".
2. Se sube un PDF nuevo (contenido único, para no chocar con el 409 por duplicado)
   y la Saga recorre subido -> extraido -> resumido -> notificado.
3. Documentos persistió el texto extraído y marcó `is_processed=true`
   (Documentos es el dueño de `extracted_text` e `is_processed`).
4. Notificaciones registró el historial completo y termina en "notificado".
5. Un documento inexistente responde 404 (no se inventa un resultado).
6. (prompt 9) La traza de esa petición está en Jaeger con spans de los 5
   servicios, y Prometheus tiene métricas http_requests_total de los 5.

No imprime claves ni el contenido completo del documento.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid


def _pdf(texto: str) -> bytes:
    """PDF mínimo válido de una página con `texto` (sin dependencias)."""
    contenido = f"BT /F1 12 Tf 50 740 Td ({texto}) Tj ET".encode("latin-1")
    objetos = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length " + str(len(contenido)).encode() + b" >>\nstream\n" + contenido + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    salida = b"%PDF-1.4\n"
    offsets = []
    for i, obj in enumerate(objetos, start=1):
        offsets.append(len(salida))
        salida += f"{i} 0 obj\n".encode() + obj + b"\nendobj\n"
    xref = len(salida)
    salida += f"xref\n0 {len(objetos) + 1}\n0000000000 65535 f \n".encode()
    salida += b"".join(f"{o:010d} 00000 n \n".encode() for o in offsets)
    salida += f"trailer\n<< /Size {len(objetos) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode()
    return salida


def _pedir(metodo: str, url: str, host: str | None, cuerpo: bytes | None = None, tipo: str | None = None):
    req = urllib.request.Request(url, data=cuerpo, method=metodo)
    if host:
        req.add_header("Host", host)
    if tipo:
        req.add_header("Content-Type", tipo)
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            return resp.status, json.loads(resp.read() or b"null"), dict(resp.headers)
    except urllib.error.HTTPError as err:
        return err.code, None, dict(err.headers)


def _check(condicion: bool, mensaje: str) -> None:
    print(("OK   " if condicion else "FALLA") + " " + mensaje)
    if not condicion:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", default="http://localhost", help="URL de Traefik (entrada pública)")
    parser.add_argument("--host-orquestador", default="orquestador.localhost")
    parser.add_argument("--jaeger", default="http://localhost:16686", help="API de Jaeger (trazas)")
    parser.add_argument("--prometheus", default="http://localhost:9090", help="API de Prometheus")
    parser.add_argument("--sin-observabilidad", action="store_true", help="no verificar trazas ni métricas")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    estado, ready, _ = _pedir("GET", f"{base}/ready", args.host_orquestador)
    _check(estado == 200 and ready["status"] == "ok", f"/ready responde 200 ({ready and ready['dependencies']})")

    marca = uuid.uuid4().hex[:12]
    texto = f"Prueba e2e {marca}: microservicios, patron Saga, Circuit Breaker y Rate Limit."
    limite = f"----e2e{marca}"
    cuerpo = (
        f"--{limite}\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\ne2e-{marca}\r\n"
        f"--{limite}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"e2e-{marca}.pdf\"\r\n"
        "Content-Type: application/pdf\r\n\r\n"
    ).encode() + _pdf(texto) + f"\r\n--{limite}--\r\n".encode()

    inicio = time.monotonic()
    estado, saga, cabeceras = _pedir(
        "POST", f"{base}/api/v1/procesar-completo", args.host_orquestador, cuerpo,
        f"multipart/form-data; boundary={limite}",
    )
    _check(estado == 200 and saga and saga["exito"], f"Saga exitosa en {time.monotonic() - inicio:.1f} s")
    _check(
        saga["pasos_completados"] == ["subido", "extraido", "resumido", "notificado"],
        f"pasos {saga['pasos_completados']}",
    )
    doc_id = saga["document_id"]

    estado, doc, _ = _pedir("GET", f"{base}/api/v1/documents/{doc_id}", None)
    _check(estado == 200, f"documento {doc_id} existe en Documentos")
    _check(doc["is_processed"] is True, "Documentos marcó is_processed=true")
    _check(marca in (doc["extracted_text"] or ""), "Documentos persistió el texto extraído")

    estado, hist, _ = _pedir("GET", f"{base}/api/v1/estados/{doc_id}", None)
    estados = [h["estado"] for h in hist["historial"]] if hist else []
    _check(estado == 200 and hist["estado_actual"] == "notificado", f"historial en Notificaciones: {estados}")

    estado, _, _ = _pedir("GET", f"{base}/api/v1/documents/999999999", None)
    _check(estado == 404, "documento inexistente responde 404")

    if not args.sin_observabilidad:
        _verificar_observabilidad(args, cabeceras)

    print("\nFlujo end-to-end verificado.")


def _verificar_observabilidad(args, cabeceras: dict) -> None:
    """Prompt 9: la misma petición deja una traza correlacionada y métricas de los 5 servicios."""
    trace_id = {k.lower(): v for k, v in cabeceras.items()}.get("x-trace-id", "")
    _check(len(trace_id) == 32, f"el orquestador devolvió x-trace-id {trace_id}")
    servicios: set[str] = set()
    for _ in range(15):  # los spans se exportan en lote: puede tardar unos segundos
        time.sleep(1)
        estado, traza, _ = _pedir("GET", f"{args.jaeger.rstrip('/')}/api/traces/{trace_id}", None)
        if estado == 200 and traza and traza.get("data"):
            procesos = traza["data"][0]["processes"].values()
            servicios = {p["serviceName"] for p in procesos}
            if len(servicios) >= 5:
                break
    esperados = {"orquestador", "documentos", "extraccion", "resumen", "notificaciones"}
    _check(esperados <= servicios, f"traza {trace_id} en Jaeger con spans de {sorted(servicios)}")

    consulta = urllib.parse.quote('sum by (service) (http_requests_total)')
    estado, metricas, _ = _pedir("GET", f"{args.prometheus.rstrip('/')}/api/v1/query?query={consulta}", None)
    con_metricas = {r["metric"].get("service") for r in (metricas or {}).get("data", {}).get("result", [])}
    _check(estado == 200 and len(con_metricas) >= 5, f"Prometheus tiene métricas de {sorted(con_metricas)}")


if __name__ == "__main__":
    main()
