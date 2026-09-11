"""Entrypoint del orquestador."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from App.api import saga_router
from App.config.settings import settings

app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug)

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
    return {"status": "ok", "service": settings.app_name}


# Servir el front-end si existe la carpeta static
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    @app.get("/")
    def home() -> FileResponse:
        return FileResponse(str(_static_dir / "index.html"))

    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
