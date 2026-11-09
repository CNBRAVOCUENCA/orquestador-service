"""Cache de resultados de la Saga, con Redis.

Se define una interfaz mínima (`Cache`) para poder inyectar un cache falso
(en memoria) en los tests, sin necesitar un Redis corriendo. `RedisCache`
es la implementación real.

Redis es solo una optimización: si no responde, el caché se comporta como
vacío (se registra un aviso) y la Saga sigue funcionando normalmente.
"""

import json
import logging
from typing import Any, Protocol

from App.models.resultado_saga import ResultadoSaga

logger = logging.getLogger(__name__)


class Cache(Protocol):
    async def get(self, document_id: int) -> ResultadoSaga | None: ...
    async def set(self, resultado: ResultadoSaga) -> None: ...


class RedisCache:
    """Implementación real con Redis, tolerante a fallos."""

    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        import redis.asyncio as redis

        self._redis: Any = redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    @classmethod
    def from_client(cls, client: Any, ttl_seconds: int = 3600) -> "RedisCache":
        """Crea el caché sobre un cliente ya construido (útil en tests)."""
        cache = cls.__new__(cls)
        cache._redis = client
        cache.ttl_seconds = ttl_seconds
        return cache

    def _key(self, document_id: int) -> str:
        return f"saga:resultado:{document_id}"

    async def get(self, document_id: int) -> ResultadoSaga | None:
        try:
            raw = await self._redis.get(self._key(document_id))
        except Exception as exc:  # Redis caído: seguir sin caché
            logger.warning("Caché no disponible al leer: %s", exc)
            return None
        if raw is None:
            return None
        return ResultadoSaga(**json.loads(raw))

    async def set(self, resultado: ResultadoSaga) -> None:
        # Solo se cachean resultados exitosos (no tiene sentido cachear un error transitorio)
        if not resultado.exito:
            return
        try:
            await self._redis.set(
                self._key(resultado.document_id),
                json.dumps(resultado.model_dump()),
                ex=self.ttl_seconds,
            )
        except Exception as exc:  # Redis caído: el resultado igual se devuelve
            logger.warning("Caché no disponible al guardar: %s", exc)


class InMemoryCache:
    """Cache en memoria, para tests y para cuando Redis está deshabilitado."""

    def __init__(self):
        self._store: dict[int, ResultadoSaga] = {}

    async def get(self, document_id: int) -> ResultadoSaga | None:
        return self._store.get(document_id)

    async def set(self, resultado: ResultadoSaga) -> None:
        if resultado.exito:
            self._store[resultado.document_id] = resultado
