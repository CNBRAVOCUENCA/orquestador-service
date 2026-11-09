"""Rutas REST del orquestador.

Las rutas solo traducen HTTP <-> dominio: la lógica vive en SagaService.
"""

from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from App.config.settings import settings
from App.exceptions import PasoSagaError
from App.schemas.saga import ProcesarResponse
from App.services.cache import Cache, InMemoryCache, RedisCache
from App.services.microservicios_client import MicroserviciosClient
from App.services.saga_service import SagaService

router = APIRouter(tags=["orquestador"])


@lru_cache(maxsize=1)
def _get_cache() -> Cache:
    """Devuelve el cache real (Redis) o uno en memoria si está deshabilitado.

    RedisCache conecta de forma perezosa y tolera que Redis esté caído, así que
    no hace falta envolver la creación en try/except.
    """
    if not settings.cache_enabled:
        return InMemoryCache()
    return RedisCache(settings.redis_url, settings.cache_ttl_seconds)


def _get_saga() -> SagaService:
    client = MicroserviciosClient(
        documentos_url=settings.documentos_url,
        extraccion_url=settings.extraccion_url,
        resumen_url=settings.resumen_url,
        notificaciones_url=settings.notificaciones_url,
        timeout=settings.http_timeout_seconds,
    )
    return SagaService(client, cache=_get_cache(), max_words=settings.resumen_max_words)


@router.post("/procesar/{document_id}", response_model=ProcesarResponse)
async def procesar(
    document_id: int,
    forzar: bool = False,
    saga: SagaService = Depends(_get_saga),
) -> ProcesarResponse:
    """Ejecuta la Saga completa para un documento: extraer -> resumir -> notificar.

    Si el documento ya fue procesado con éxito, devuelve el resultado cacheado
    (salvo que se pase `?forzar=true`). Si la Saga falla, `exito` es False y
    `error` indica en qué paso se rompió.
    """
    resultado = await saga.procesar(document_id, forzar=forzar)
    return ProcesarResponse(**resultado.model_dump())


@router.post(
    "/procesar-completo",
    response_model=ProcesarResponse,
    responses={409: {"description": "El PDF ya existe"}, 502: {"description": "No se pudo subir"}},
)
async def procesar_completo(
    name: str = Form(...),
    file: UploadFile = File(...),
    saga: SagaService = Depends(_get_saga),
) -> ProcesarResponse:
    """Sube un PDF y ejecuta la Saga completa de una sola vez (lo usa el front)."""
    try:
        contenido = await file.read()
    finally:
        await file.close()
    try:
        document_id, resultado = await saga.subir_y_procesar(name, file.filename, contenido)
    except PasoSagaError as exc:
        # Duplicado -> 409 (lo informa documentos-service); cualquier otro fallo -> 502.
        status_code = 409 if exc.status_code == 409 else 502
        raise HTTPException(status_code=status_code, detail=exc.detalle) from exc
    return ProcesarResponse(**{**resultado.model_dump(), "document_id": document_id})
