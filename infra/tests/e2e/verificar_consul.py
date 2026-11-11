"""Prueba acotada de fallo y recuperación de Consul en el stack aislado.

El proyecto Compose está fijado a `prompt-final-check`; nunca detiene servicios
del proyecto normal `infra`. Requiere que el stack aislado ya esté levantado.

    python infra/tests/e2e/verificar_consul.py
"""

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

INFRA_DIR = Path(__file__).resolve().parents[2]
PROJECT = "prompt-final-check"
SERVICES = {"documentos", "extraccion", "resumen", "notificaciones", "orquestador"}
BASE_URL = "http://localhost"
HOST = "resumen.localhost"
ROUTER_URL = "http://localhost:8080/api/http/routers/resumen-consul@consulcatalog"
TIMEOUT = 90


def _compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["docker", "compose", "-p", PROJECT, *args],
        cwd=INFRA_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(detail or f"docker compose falló con código {result.returncode}")
    return result


def _route_status() -> int:
    request = urllib.request.Request(f"{BASE_URL}/health", headers={"Host": HOST})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def _router_status() -> int:
    try:
        with urllib.request.urlopen(ROUTER_URL, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def _wait_for_route(expected: bool, description: str) -> None:
    deadline = time.monotonic() + TIMEOUT
    last_status = None
    while time.monotonic() < deadline:
        try:
            last_status = _route_status()
            if (last_status == 200) is expected:
                print(f"OK   {description} (HTTP {last_status})")
                return
        except (urllib.error.URLError, TimeoutError) as error:
            last_status = str(error)
        time.sleep(2)
    raise RuntimeError(f"Timeout: {description}; último resultado: {last_status}")


def _wait_for_router(expected: bool, description: str) -> None:
    deadline = time.monotonic() + TIMEOUT
    last_status = None
    while time.monotonic() < deadline:
        try:
            last_status = _router_status()
            if (last_status == 200) is expected:
                print(f"OK   {description} (HTTP {last_status})")
                return
        except (urllib.error.URLError, TimeoutError) as error:
            last_status = str(error)
        time.sleep(2)
    raise RuntimeError(f"Timeout: {description}; último resultado: {last_status}")


def _wait_for_catalog() -> None:
    deadline = time.monotonic() + TIMEOUT
    last_result = "catálogo aún no disponible"
    while time.monotonic() < deadline:
        result = _compose(
            "exec",
            "-T",
            "consul",
            "consul",
            "catalog",
            "services",
            check=False,
        )
        if result.returncode == 0:
            services = {line.strip() for line in result.stdout.splitlines() if line.strip()}
            missing = SERVICES - services
            if not missing:
                print(f"OK   catálogo Consul recuperado: {sorted(SERVICES)}")
                return
            last_result = f"servicios ausentes: {sorted(missing)}"
        else:
            last_result = result.stderr.strip() or f"docker compose exit code {result.returncode}"
        time.sleep(2)
    raise RuntimeError(f"Consul no recuperó el catálogo en {TIMEOUT} s; {last_result}")


def _require_running_stack() -> None:
    result = _compose("ps", "--status", "running", "--services", check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "No se pudo consultar Docker Compose")
    running = set(result.stdout.splitlines())
    required = SERVICES | {"consul", "traefik"}
    if not required <= running:
        raise RuntimeError(
            f"Falta iniciar el stack aislado {PROJECT}; servicios requeridos: {sorted(required)}"
        )


def main() -> int:
    _require_running_stack()
    _wait_for_route(True, "ruta de resumen disponible inicialmente")
    _wait_for_router(True, "router de resumen publicado por Consul Catalog")

    _compose("stop", "resumen")
    try:
        _wait_for_router(False, "Traefik retira el router cuando falla resumen")
    finally:
        _compose("start", "resumen")
    _wait_for_router(True, "router de resumen recuperado al iniciar el servicio")
    _wait_for_route(True, "ruta de resumen recuperada al iniciar el servicio")

    _compose("restart", "consul")
    _wait_for_catalog()
    _wait_for_router(True, "router de resumen recuperado tras reiniciar Consul")
    _wait_for_route(True, "ruta de resumen sigue disponible tras reiniciar Consul")
    print("\nRecuperación de Consul verificada.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (RuntimeError, OSError) as error:
        print(f"FALLA {error}", file=sys.stderr)
        sys.exit(1)
