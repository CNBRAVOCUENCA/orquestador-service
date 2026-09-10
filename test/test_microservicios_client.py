"""Pruebas del cliente HTTP hacia los microservicios coordinados."""

import httpx
import pytest
import respx

from App.exceptions import PasoSagaError
from App.services.microservicios_client import MicroserviciosClient

EXT = "http://ext.test"
RES = "http://res.test"
NOT = "http://not.test"


def _client():
    return MicroserviciosClient(EXT, RES, NOT)


@respx.mock
async def test_extraer_devuelve_texto():
    respx.post(f"{EXT}/api/v1/extract").mock(
        return_value=httpx.Response(200, json={"extracted_text": "hola", "char_count": 4})
    )
    assert await _client().extraer(1) == "hola"


@respx.mock
async def test_extraer_falla_lanza_paso_saga_error():
    respx.post(f"{EXT}/api/v1/extract").mock(return_value=httpx.Response(404))
    with pytest.raises(PasoSagaError) as exc:
        await _client().extraer(1)
    assert exc.value.paso == "extraccion"


@respx.mock
async def test_resumir_devuelve_resumen():
    respx.post(f"{RES}/api/v1/summarize").mock(
        return_value=httpx.Response(200, json={"summary": "resumen", "input_char_count": 10, "summary_char_count": 7})
    )
    assert await _client().resumir("texto largo", 100) == "resumen"


@respx.mock
async def test_notificar_ok():
    respx.post(f"{NOT}/api/v1/estados").mock(return_value=httpx.Response(200, json={}))
    # No lanza nada
    await _client().notificar(1, "subido", "detalle")
