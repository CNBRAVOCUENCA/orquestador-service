"""Proceso de administración (12-factor XII): verifica la salud del sistema.

Consulta el /health de cada microservicio y reporta el estado general.
Se ejecuta como una tarea admin puntual, en el mismo entorno que la app:

    python scripts/verificar_sistema.py

Devuelve código de salida 0 si todos los servicios responden, 1 si alguno falla.
"""

import asyncio
import os
import sys

import httpx

SERVICIOS = {
    "documentos": os.getenv("DOCUMENTOS_URL", "http://localhost:8001"),
    "extraccion": os.getenv("EXTRACCION_URL", "http://localhost:8002"),
    "resumen": os.getenv("RESUMEN_URL", "http://localhost:8003"),
    "notificaciones": os.getenv("NOTIFICACIONES_URL", "http://localhost:8004"),
}


async def verificar() -> bool:
    todos_ok = True
    async with httpx.AsyncClient(timeout=5.0) as client:
        for nombre, url in SERVICIOS.items():
            try:
                r = await client.get(f"{url}/health")
                estado = "OK" if r.status_code == 200 else f"FALLO ({r.status_code})"
                if r.status_code != 200:
                    todos_ok = False
            except Exception as exc:
                estado = f"SIN RESPUESTA ({exc})"
                todos_ok = False
            print(f"  {nombre:<16} {url:<30} {estado}")
    return todos_ok


def main() -> None:
    print("Verificando salud del sistema El-Destripador-de-PDFs...\n")
    ok = asyncio.run(verificar())
    print("\n" + ("Todos los servicios responden." if ok else "Hay servicios que no responden."))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
