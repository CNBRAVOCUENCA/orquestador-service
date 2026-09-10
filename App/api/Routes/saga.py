"""Rutas REST del orquestador."""

from functools import lru_cache

from fastapi import APIRouter, Depends

from App.config.settings import settings
from App.schemas.saga import ProcesarResponse
from App.services.cache import Cache, InMemoryCache, RedisCache
from App.services.microservicios_client import MicroserviciosClient
from App.services.saga_service import SagaService


@lru_cache(maxsize=1)
def _get_cache() -> Cache:
    """Devuelve el cache real (Redis) o uno en memoria si está deshabilitado."""
    if not settings.cache_enabled:
        return InMemoryCache()
    try:
        return RedisCache(settings.redis_url, settings.cache_ttl_seconds)
    except Exception:
        # Si Redis no está disponible al arrancar, degradar a cache en memoria
        return InMemoryCache()


router = APIRouter(tags=["orquestador"])


def _get_saga() -> SagaService:
    client = MicroserviciosClient(
        extraccion_url=settings.extraccion_url,
        resumen_url=settings.resumen_url,
        notificaciones_url=settings.notificaciones_url,
        timeout=settings.http_timeout_seconds,
    )
    return SagaService(client, cache=_get_cache(), max_words=settings.resumen_max_words)


@router.post("/procesar/{document_id}", response_model=ProcesarResponse)
async def procesar(document_id: int, forzar: bool = False, saga: SagaService = Depends(_get_saga)) -> ProcesarResponse:
    """Ejecuta la Saga completa para un documento: extraer -> resumir -> notificar.

    Si el documento ya fue procesado con éxito, devuelve el resultado cacheado
    (salvo que se pase `?forzar=true`). Si la Saga falla, `exito` es False y
    `error` indica en qué paso se rompió.
    """
    resultado = await saga.procesar(document_id, forzar=forzar)
    return ProcesarResponse(**resultado.model_dump())
