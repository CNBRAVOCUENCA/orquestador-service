"""Pruebas del cliente HTTP hacia los microservicios coordinados."""

import httpx
import pytest
import respx
from App.exceptions import PasoSagaError
from App.services.microservicios_client import MicroserviciosClient

DOC = "http://doc.test"
EXT = "http://ext.test"
RES = "http://res.test"
NOT = "http://not.test"


def _client():
    return MicroserviciosClient(DOC, EXT, RES, NOT)


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


@respx.mock
async def test_subir_documento_devuelve_id():
    respx.post(f"{DOC}/api/v1/documents").mock(return_value=httpx.Response(201, json={"id": 5}))
    assert await _client().subir_documento("Doc", "a.pdf", b"%PDF-1") == 5


@respx.mock
async def test_error_http_conserva_el_codigo_de_estado():
    respx.post(f"{DOC}/api/v1/documents").mock(return_value=httpx.Response(409, json={"detail": "dup"}))
    with pytest.raises(PasoSagaError) as exc_info:
        await _client().subir_documento("Doc", "a.pdf", b"%PDF-1")
    assert exc_info.value.paso == "subida"
    assert exc_info.value.status_code == 409


@respx.mock
async def test_servicio_caido_no_tiene_codigo_de_estado():
    respx.post(f"{EXT}/api/v1/extract").mock(side_effect=httpx.ConnectError("caido"))
    with pytest.raises(PasoSagaError) as exc_info:
        await _client().extraer(1)
    assert exc_info.value.status_code is None
