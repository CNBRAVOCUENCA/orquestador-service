"""Utilidades compartidas por los scripts de operación."""

from pathlib import Path
import shutil
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
COMPOSE_FILE = PROJECT_ROOT / "infra" / "docker-compose.yml"
ENV_FILE = PROJECT_ROOT / ".env"
ENV_EXAMPLE = PROJECT_ROOT / ".env.example"


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


def run_command(command: list[str], *, cwd: Path = PROJECT_ROOT) -> int:
    """Ejecuta un comando visible y devuelve su código de salida."""
    try:
        return subprocess.run(command, cwd=cwd, check=False).returncode
    except FileNotFoundError as exc:
        print(f"No se pudo ejecutar el comando: {exc}", file=sys.stderr)
        return 1
