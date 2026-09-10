"""Cache de resultados de la Saga, con Redis.

Se define una interfaz mínima (`Cache`) para poder inyectar un cache falso
(en memoria) en los tests, sin necesitar un Redis corriendo. `RedisCache`
es la implementación real.
"""

import json
from typing import Optional, Protocol

from App.models.resultado_saga import ResultadoSaga


class Cache(Protocol):
    async def get(self, document_id: int) -> Optional[ResultadoSaga]: ...
    async def set(self, resultado: ResultadoSaga) -> None: ...


class RedisCache:
    """Implementación real con Redis."""

    def __init__(self, redis_url: str, ttl_seconds: int = 3600):
        import redis.asyncio as redis
        self._redis = redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    def _key(self, document_id: int) -> str:
        return f"saga:resultado:{document_id}"

    async def get(self, document_id: int) -> Optional[ResultadoSaga]:
        raw = await self._redis.get(self._key(document_id))
        if raw is None:
            return None
        return ResultadoSaga(**json.loads(raw))

    async def set(self, resultado: ResultadoSaga) -> None:
        # Solo se cachean resultados exitosos (no tiene sentido cachear un error transitorio)
        if not resultado.exito:
            return
        await self._redis.set(
            self._key(resultado.document_id),
            json.dumps(resultado.model_dump()),
            ex=self.ttl_seconds,
        )


class InMemoryCache:
    """Cache en memoria, para tests y para cuando Redis está deshabilitado."""

    def __init__(self):
        self._store: dict[int, ResultadoSaga] = {}

    async def get(self, document_id: int) -> Optional[ResultadoSaga]:
        return self._store.get(document_id)

    async def set(self, resultado: ResultadoSaga) -> None:
        if resultado.exito:
            self._store[resultado.document_id] = resultado
