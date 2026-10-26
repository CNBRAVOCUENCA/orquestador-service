"""Sube un PDF y guarda su ID para la prueba Vegeta en Linux/macOS."""

import json
import os
from pathlib import Path
import urllib.error
import urllib.request
import uuid

from comun import PROJECT_ROOT


VEGETA_DIR = PROJECT_ROOT / "infra" / "vegeta"
DEFAULT_UPLOAD_URL = "http://localhost/api/v1/documents"


def make_multipart(name: str, file_path: Path) -> tuple[str, bytes]:
    boundary = "----pdf-upload-" + uuid.uuid4().hex
    safe_filename = file_path.name.replace("\\", "_").replace('"', "_")
    safe_filename = safe_filename.replace("\r", "_").replace("\n", "_")
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="name"\r\n'
        "Content-Type: text/plain; charset=utf-8\r\n\r\n"
        f"{name}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'
        "Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8")
    body += file_path.read_bytes()
    body += f"\r\n--{boundary}--\r\n".encode("ascii")
    return boundary, body


def main() -> int:
    raw_path = input("Ruta del PDF: ").strip().strip('"')
    if not raw_path:
        print("No se indicó ningún archivo.")
        return 1

    file_path = Path(raw_path).expanduser()
    if not file_path.is_file() or file_path.suffix.lower() != ".pdf":
        print(f"No se encontró un archivo PDF válido: {file_path}")
        return 1

    name = input("Nombre para el documento: ").strip()
    if not name:
        print("Debes indicar un nombre para el documento.")
        return 1
    if "\r" in name or "\n" in name:
        print("El nombre del documento no puede contener saltos de línea.")
        return 1

    upload_url = os.environ.get("DOCUMENTOS_UPLOAD_URL", DEFAULT_UPLOAD_URL)
    host_header = os.environ.get("DOCUMENTOS_UPLOAD_HOST", "documentos.localhost")
    try:
        boundary, body = make_multipart(name, file_path)
    except OSError as exc:
        print(f"No se pudo leer el PDF: {exc}")
        return 1
    request = urllib.request.Request(
        upload_url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Host": host_header,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_body = response.read()
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if exc.code == 409:
            print("Ese PDF ya existe (HTTP 409). Usa otro PDF o conserva el ID existente.")
        else:
            print(f"La subida falló con HTTP {exc.code}: {detail}")
        return 1
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"No se pudo contactar documentos-service: {exc}")
        print("Comprueba que Docker y el stack estén activos.")
        return 1

    try:
        result = json.loads(response_body)
        document_id = int(result["id"])
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        print(f"documentos-service devolvió una respuesta inesperada: {exc}")
        return 1

    VEGETA_DIR.mkdir(parents=True, exist_ok=True)
    (VEGETA_DIR / "document-id.txt").write_text(f"{document_id}\n", encoding="ascii")
    (VEGETA_DIR / "extractor-body.json").write_text(
        json.dumps({"document_id": document_id}),
        encoding="ascii",
    )
    print(f"PDF subido correctamente. document_id={document_id}")
    print(f"ID y body guardados en {VEGETA_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
