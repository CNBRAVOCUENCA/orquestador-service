"""Pruebas unitarias del SagaService: flujo feliz y compensación ante fallos."""

from unittest.mock import AsyncMock

import pytest

from App.exceptions import PasoSagaError
from App.services.saga_service import SagaService


def _client_ok():
    """Cliente falso donde todos los pasos funcionan."""
    client = AsyncMock()
    client.extraer.return_value = "texto extraído del pdf"
    client.resumir.return_value = "este es el resumen"
    client.notificar.return_value = None
    return client


async def test_saga_flujo_feliz_completo():
    client = _client_ok()
    saga = SagaService(client, max_words=100)

    resultado = await saga.procesar(document_id=1)

    assert resultado.exito is True
    assert resultado.estado_final == "notificado"
    assert resultado.pasos_completados == ["subido", "extraido", "resumido", "notificado"]
    assert resultado.resumen == "este es el resumen"
    # Se llamó a extraer y resumir exactamente una vez
    client.extraer.assert_awaited_once_with(1)
    client.resumir.assert_awaited_once_with("texto extraído del pdf", 100)


async def test_saga_falla_en_extraccion_ejecuta_compensacion():
    client = _client_ok()
    client.extraer.side_effect = PasoSagaError("extraccion", "documento no encontrado")
    saga = SagaService(client, max_words=100)

    resultado = await saga.procesar(document_id=2)

    assert resultado.exito is False
    assert resultado.estado_final == "error"
    assert "extraccion" in resultado.error
    # Completó "subido" pero no "extraido"
    assert resultado.pasos_completados == ["subido"]
    # No se intentó resumir, porque la extracción falló antes
    client.resumir.assert_not_awaited()
    # Compensación: se llamó a notificar con estado "error"
    llamadas_error = [c for c in client.notificar.await_args_list if c.args[1] == "error"]
    assert len(llamadas_error) == 1


async def test_saga_falla_en_resumen_no_marca_resumido():
    client = _client_ok()
    client.resumir.side_effect = PasoSagaError("resumen", "falta API key")
    saga = SagaService(client, max_words=100)

    resultado = await saga.procesar(document_id=3)

    assert resultado.exito is False
    assert resultado.estado_final == "error"
    assert "resumen" in resultado.error
    # Alcanzó a extraer pero no a resumir
    assert resultado.pasos_completados == ["subido", "extraido"]


async def test_compensacion_no_explota_si_notificaciones_tambien_falla():
    """Si el propio servicio de notificaciones falla, la compensación no debe
    tirar una excepción que oculte el error original."""
    client = _client_ok()
    client.extraer.side_effect = PasoSagaError("extraccion", "boom")
    client.notificar.side_effect = PasoSagaError("notificacion", "notificaciones caído")
    saga = SagaService(client, max_words=100)

    # No debe lanzar excepción
    resultado = await saga.procesar(document_id=4)
    assert resultado.exito is False
    assert resultado.estado_final == "error"


async def test_cache_hit_no_llama_a_los_microservicios():
    from App.services.cache import InMemoryCache
    from App.models.resultado_saga import ResultadoSaga

    cache = InMemoryCache()
    # Pre-cargar un resultado exitoso
    await cache.set(ResultadoSaga(
        document_id=5, exito=True, estado_final="notificado",
        pasos_completados=["subido", "extraido", "resumido", "notificado"], resumen="cacheado",
    ))
    client = _client_ok()
    saga = SagaService(client, cache=cache, max_words=100)

    resultado = await saga.procesar(document_id=5)

    assert resultado.resumen == "cacheado"
    # No se llamó a ningún microservicio, porque salió del cache
    client.extraer.assert_not_awaited()
    client.resumir.assert_not_awaited()


async def test_cache_se_guarda_tras_exito():
    from App.services.cache import InMemoryCache

    cache = InMemoryCache()
    client = _client_ok()
    saga = SagaService(client, cache=cache, max_words=100)

    await saga.procesar(document_id=7)

    # El resultado quedó en cache
    guardado = await cache.get(7)
    assert guardado is not None
    assert guardado.exito is True


async def test_forzar_ignora_el_cache():
    from App.services.cache import InMemoryCache
    from App.models.resultado_saga import ResultadoSaga

    cache = InMemoryCache()
    await cache.set(ResultadoSaga(
        document_id=9, exito=True, estado_final="notificado",
        pasos_completados=["subido", "extraido", "resumido", "notificado"], resumen="viejo",
    ))
    client = _client_ok()
    saga = SagaService(client, cache=cache, max_words=100)

    resultado = await saga.procesar(document_id=9, forzar=True)

    # Con forzar=True, reprocesa: se llamó a extraer de verdad
    client.extraer.assert_awaited_once()
    assert resultado.resumen == "este es el resumen"
