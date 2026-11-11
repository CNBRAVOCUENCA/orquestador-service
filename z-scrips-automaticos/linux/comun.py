"""Utilidades compartidas por los scripts de operación."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "infra" / "docker-compose.yml"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
RELEASE_VERSION_KEYS = (
    "DOCUMENTOS_VERSION",
    "EXTRACCION_VERSION",
    "RESUMEN_VERSION",
    "NOTIFICACIONES_VERSION",
    "ORQUESTADOR_VERSION",
)


def compose_command() -> list[str]:
    """Construye el comando Compose con rutas absolutas."""
    docker = shutil.which("docker")
    if docker is None:
        raise RuntimeError("No se encontró Docker. Instala Docker y verifica que esté en PATH.")
    if not COMPOSE_FILE.is_file():
        raise FileNotFoundError(f"No se encontró el archivo Compose: {COMPOSE_FILE}")
    return [
        docker,
        "compose",
        "--env-file",
        str(ENV_FILE),
        "-f",
        str(COMPOSE_FILE),
    ]


def ensure_env() -> bool:
    """Crea .env desde el ejemplo si falta; devuelve True si lo creó."""
    if ENV_FILE.exists():
        return False
    if not ENV_EXAMPLE.is_file():
        raise FileNotFoundError(f"No se encontró la plantilla: {ENV_EXAMPLE}")
    shutil.copyfile(ENV_EXAMPLE, ENV_FILE)
    return True


def validate_release_versions() -> None:
    """Rechaza tags mutables antes de desplegar una release."""
    if not ENV_FILE.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {ENV_FILE}")

    values = read_env_values()
    invalid = [
        key for key in RELEASE_VERSION_KEYS if not re.fullmatch(r"[0-9a-f]{40}", values.get(key, ""))
    ]
    if invalid:
        names = ", ".join(invalid)
        raise RuntimeError(
            "El modo release requiere un SHA Git completo (40 caracteres hexadecimales) "
            f"en estas variables de .env: {names}."
        )


def read_env_values() -> dict[str, str]:
    """Lee valores simples KEY=VALUE del .env del stack."""
    if not ENV_FILE.is_file():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {ENV_FILE}")

    values = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def validate_orchestrator_build_version() -> None:
    """Permite dev local o exige que el tag publicado coincida con HEAD."""
    version = read_env_values().get("ORQUESTADOR_VERSION", "")
    if version == "dev":
        return
    if not re.fullmatch(r"[0-9a-f]{40}", version):
        raise RuntimeError("ORQUESTADOR_VERSION debe ser 'dev' o el SHA Git completo del orquestador.")

    git = shutil.which("git")
    if git is None:
        raise RuntimeError("Se necesita Git para verificar ORQUESTADOR_VERSION.")
    result = subprocess.run(
        [git, "rev-parse", "HEAD"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"No se pudo resolver el commit actual de Git: {result.stderr.strip()}")
    if result.stdout.strip() != version:
        raise RuntimeError(
            "ORQUESTADOR_VERSION no coincide con el commit actual. "
            "Ajusta el SHA en .env o usa 'dev' para desarrollo local."
        )

    status = subprocess.run(
        [git, "status", "--porcelain"],
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0:
        raise RuntimeError(f"No se pudo comprobar el estado de Git: {status.stderr.strip()}")
    if status.stdout.strip():
        raise RuntimeError("El build versionado requiere un checkout limpio para que el tag identifique el código.")


def run_command(command: list[str], *, cwd: Path = PROJECT_ROOT) -> int:
    """Ejecuta un comando visible y devuelve su código de salida."""
    try:
        return subprocess.run(command, cwd=cwd, check=False).returncode
    except FileNotFoundError as exc:
        print(f"No se pudo ejecutar el comando: {exc}", file=sys.stderr)
        return 1
