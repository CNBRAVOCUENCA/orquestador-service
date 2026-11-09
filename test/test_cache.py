"""Pruebas del caché de la Saga: en memoria y tolerancia a fallos de Redis."""

from App.models.resultado_saga import ResultadoSaga
from App.services.cache import InMemoryCache, RedisCache


def _ok(document_id: int = 1) -> ResultadoSaga:
    return ResultadoSaga(
        document_id=document_id, exito=True, estado_final="notificado",
        pasos_completados=["subido"], resumen="r",
    )


class _RedisCaido:
    """Simula un Redis que no responde."""

    async def get(self, *_args, **_kwargs):
        raise ConnectionError("redis caido")

    async def set(self, *_args, **_kwargs):
        raise ConnectionError("redis caido")


class _RedisFalso:
    def __init__(self):
        self.store: dict[str, str] = {}

    async def get(self, key):
        return self.store.get(key)

    async def set(self, key, value, ex=None):
        self.store[key] = value


async def test_memoria_guarda_solo_resultados_exitosos():
    cache = InMemoryCache()
    await cache.set(_ok(1))
    await cache.set(ResultadoSaga(document_id=2, exito=False, estado_final="error", pasos_completados=[]))
    assert (await cache.get(1)).resumen == "r"
    assert await cache.get(2) is None


async def test_redis_guarda_y_recupera():
    cache = RedisCache.from_client(_RedisFalso(), ttl_seconds=60)
    await cache.set(_ok(3))
    assert (await cache.get(3)).document_id == 3


async def test_redis_caido_no_rompe_la_saga():
    cache = RedisCache.from_client(_RedisCaido(), ttl_seconds=60)
    # Si Redis no responde, el caché se comporta como vacío en vez de lanzar error.
    assert await cache.get(1) is None
    await cache.set(_ok(1))
