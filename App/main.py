"""Entrypoint del orquestador."""

from fastapi import FastAPI

from App.api import saga_router
from App.config.settings import settings

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

app.include_router(saga_router, prefix=settings.api_v1_prefix)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name}
