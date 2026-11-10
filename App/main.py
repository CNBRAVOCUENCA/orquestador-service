"""Entrypoint del orquestador."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from App.api import saga_router
from App.config.settings import settings
from App.logging_config import configurar_logging
from App.services.consul_registration import ConsulRegistration
from App.services.microservicios_client import MicroserviciosClient
from App.telemetry import install_telemetry

# Disable API documentation in production (when debug=False)
docs_url = "/docs" if settings.debug else None
redoc_url = "/redoc" if settings.debug else None
openapi_url = "/openapi.json" if settings.debug else None

configurar_logging()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    registration = ConsulRegistration(settings)
    await registration.register()
    try:
        yield
    finally:
        await registration.deregister()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    docs_url=docs_url,
    redoc_url=redoc_url,
    openapi_url=openapi_url,
    lifespan=lifespan,
)

install_telemetry(app, settings.app_name)

# CORS: permite que el front (página web) llame a este servicio desde el navegador
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(saga_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    """Liveness: confirma que el proceso HTTP del orquestador está activo."""
    return {"status": "ok", "service": settings.app_name}


async def _check_redis() -> dict[str, str | bool]:
    """Comprueba Redis solo cuando el caché configurado lo requiere."""
    if not settings.cache_enabled:
        return {"status": "disabled", "required": False}

    import redis.asyncio as redis
    from redis.exceptions import RedisError

    try:
        async with redis.from_url(
            settings.redis_url,
            socket_connect_timeout=settings.readiness_timeout_seconds,
            socket_timeout=settings.readiness_timeout_seconds,
        ) as client:
            await asyncio.wait_for(client.ping(), timeout=settings.readiness_timeout_seconds)
    except TimeoutError:
        return {"status": "error", "detail": "timeout", "required": True}
    except (RedisError, ValueError):
        return {"status": "error", "detail": "connection_error", "required": True}
    return {"status": "ok", "required": True}


@app.get("/ready")
async def readiness(response: Response) -> dict:
    """Readiness: comprueba las dependencias necesarias antes de enrutar trabajo."""
    client = MicroserviciosClient(
        documentos_url=settings.documentos_url,
        extraccion_url=settings.extraccion_url,
        resumen_url=settings.resumen_url,
        notificaciones_url=settings.notificaciones_url,
        timeout=settings.readiness_timeout_seconds,
    )
    servicios = await client.verificar_salud()
    dependencias = {
        nombre: {**resultado, "required": True}
        for nombre, resultado in servicios.items()
    }
    dependencias["redis"] = await _check_redis()
    saludable = all(
        resultado["status"] in {"ok", "disabled"}
        for resultado in dependencias.values()
    )
    body = {
        "status": "ok" if saludable else "error",
        "dependencies": dependencias,
    }
    if not saludable:
        response.status_code = 503
    return body


# Servir el front-end si existe la carpeta static
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    @app.get("/")
    def home() -> FileResponse:
        return FileResponse(str(_static_dir / "index.html"))

    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
