"""Ejecuta Vegeta contra el endpoint del extractor desde Linux/macOS."""

from datetime import datetime
import re
import shutil
import subprocess

from comun import PROJECT_ROOT, run_command


VEGETA_DIR = PROJECT_ROOT / "infra" / "vegeta"
ID_FILE = VEGETA_DIR / "document-id.txt"
TARGETS_FILE = VEGETA_DIR / "targets-extractor.txt"
BODY_FILE = VEGETA_DIR / "extractor-body.json"
LOCAL_IMAGE = "extractor-vegeta:local"
FALLBACK_IMAGE = "peterevans/vegeta:latest"
RATE_PATTERN = re.compile(r"\d+(?:/\d+(?:ns|us|µs|ms|s|m|h)+)?\Z")
DURATION_PATTERN = re.compile(r"(?:\d+(?:ns|us|µs|ms|s|m|h))+\Z")


def select_image(docker: str) -> str:
    result = subprocess.run(
        [docker, "image", "inspect", LOCAL_IMAGE],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return LOCAL_IMAGE if result.returncode == 0 else FALLBACK_IMAGE


def main() -> int:
    if not ID_FILE.is_file():
        print("Primero ejecuta subir_pdf.py para subir un PDF y guardar su ID.")
        return 1
    if not TARGETS_FILE.is_file():
        print(f"No se encontró el archivo de targets: {TARGETS_FILE}")
        return 1
    if not BODY_FILE.is_file():
        print("No se encontró extractor-body.json. Vuelve a subir el PDF con subir_pdf.py.")
        return 1
    docker = shutil.which("docker")
    if docker is None:
        print("No se encontró Docker. Instala Docker y verifica que esté en PATH.")
        return 1

    try:
        document_id = ID_FILE.read_text(encoding="ascii").strip()
    except OSError as exc:
        print(f"No se pudo leer {ID_FILE}: {exc}")
        return 1
    if not document_id.isdigit():
        print("document-id.txt está vacío o no contiene un ID válido.")
        return 1

    rate = input("Solicitudes por segundo [2]: ").strip() or "2"
    if not RATE_PATTERN.fullmatch(rate) or int(rate.split("/", 1)[0]) < 1:
        print("La tasa debe ser positiva, por ejemplo 2 o 5/1s.")
        return 1

    duration = input("Duración [5s]: ").strip() or "5s"
    if duration.isdigit():
        duration += "s"
    if not DURATION_PATTERN.fullmatch(duration):
        print("Duración no válida. Usa, por ejemplo, 10s, 1m o 1m30s.")
        return 1

    image = select_image(docker)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    results_path = f"extractor-results-{stamp}.bin"
    report_path = VEGETA_DIR / f"extractor-report-{stamp}.txt"

    print(f"Ejecutando Vegeta con document_id={document_id}")
    print(f"Tasa: {rate} solicitudes/s; duración: {duration}")
    attack = [
        docker,
        "run",
        "--rm",
        "--add-host=host.docker.internal:host-gateway",
        "-v",
        f"{VEGETA_DIR.resolve()}:/work",
        "-w",
        "/work",
        "--entrypoint",
        "sh",
        image,
        "-c",
        'vegeta attack -targets=targets-extractor.txt -rate="$1" -duration="$2" > "$3"',
        "sh",
        rate,
        duration,
        results_path,
    ]
    result = run_command(attack, cwd=VEGETA_DIR)
    if result != 0:
        print("La prueba falló. Verifica Docker, la tasa, la duración y que el extractor esté activo.")
        return result

    report = [
        docker,
        "run",
        "--rm",
        "-v",
        f"{VEGETA_DIR.resolve()}:/work",
        "-w",
        "/work",
        "--entrypoint",
        "sh",
        image,
        "-c",
        'vegeta report -type=text "$1"',
        "sh",
        results_path,
    ]
    try:
        with report_path.open("w", encoding="utf-8") as output:
            result = subprocess.run(
                report,
                cwd=VEGETA_DIR,
                stdout=output,
                check=False,
            ).returncode
    except OSError as exc:
        print(f"No se pudo guardar el reporte: {exc}")
        return 1

    if result != 0:
        print("No se pudo generar el reporte.")
        return result

    print(report_path.read_text(encoding="utf-8"))
    print(f"Resultados: {VEGETA_DIR / results_path}")
    print(f"Reporte guardado: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
