"""Prueba de integración de la API del orquestador, mockeando los 3 servicios."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

EXT = "http://ext.test"
RES = "http://res.test"
NOT = "http://not.test"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("EXTRACCION_URL", EXT)
    monkeypatch.setenv("RESUMEN_URL", RES)
    monkeypatch.setenv("NOTIFICACIONES_URL", NOT)
    monkeypatch.setenv("CACHE_ENABLED", "false")
    import importlib
    import App.config.settings as s
    importlib.reload(s)
    import App.api.Routes.saga as r
    importlib.reload(r)
    r._get_cache.cache_clear()
    import App.main as m
    importlib.reload(m)
    return TestClient(m.app)


@respx.mock
def test_procesar_flujo_completo(client):
    respx.post(f"{EXT}/api/v1/extract").mock(return_value=httpx.Response(200, json={"extracted_text": "texto del pdf", "char_count": 13}))
    respx.post(f"{RES}/api/v1/summarize").mock(return_value=httpx.Response(200, json={"summary": "un resumen", "input_char_count": 13, "summary_char_count": 10}))
    respx.post(f"{NOT}/api/v1/estados").mock(return_value=httpx.Response(200, json={}))

    r = client.post("/api/v1/procesar/1")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["exito"] is True
    assert body["estado_final"] == "notificado"
    assert body["resumen"] == "un resumen"


@respx.mock
def test_procesar_con_fallo_devuelve_error(client):
    respx.post(f"{EXT}/api/v1/extract").mock(return_value=httpx.Response(404))
    respx.post(f"{NOT}/api/v1/estados").mock(return_value=httpx.Response(200, json={}))

    r = client.post("/api/v1/procesar/99")
    assert r.status_code == 200  # la saga devuelve 200 con exito=False
    body = r.json()
    assert body["exito"] is False
    assert body["estado_final"] == "error"


def test_health(client):
    assert client.get("/health").status_code == 200
