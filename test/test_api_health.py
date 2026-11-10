"""Pruebas de liveness y readiness del orquestador."""

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

DOCUMENTOS = "http://doc.test"
EXTRACCION = "http://ext.test"
RESUMEN = "http://res.test"
NOTIFICACIONES = "http://not.test"
SERVICIOS = {
    "documentos": DOCUMENTOS,
    "extraccion": EXTRACCION,
    "resumen": RESUMEN,
    "notificaciones": NOTIFICACIONES,
}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("DOCUMENTOS_URL", DOCUMENTOS)
    monkeypatch.setenv("EXTRACCION_URL", EXTRACCION)
    monkeypatch.setenv("RESUMEN_URL", RESUMEN)
    monkeypatch.setenv("NOTIFICACIONES_URL", NOTIFICACIONES)
    monkeypatch.setenv("CACHE_ENABLED", "false")

    import importlib
    import App.config.settings as settings_module

    importlib.reload(settings_module)
    import App.main as main_module

    importlib.reload(main_module)
    return TestClient(main_module.app)


def _mock_services(status_code: int = 200) -> None:
    for url in SERVICIOS.values():
        respx.get(f"{url}/health").mock(return_value=httpx.Response(status_code))


@respx.mock
def test_readiness_todas_las_dependencias_disponibles(client):
    _mock_services()

    response = client.get("/ready")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert all(body["dependencies"][name]["status"] == "ok" for name in SERVICIOS)
    assert body["dependencies"]["redis"] == {"status": "disabled", "required": False}


@respx.mock
def test_readiness_falla_e_identifica_dependencia_no_disponible(client):
    _mock_services()
    respx.get(f"{EXTRACCION}/health").mock(return_value=httpx.Response(503))

    response = client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "error"
    assert body["dependencies"]["extraccion"] == {
        "status": "error",
        "detail": "http_503",
        "required": True,
    }


@respx.mock
def test_readiness_reporta_timeout(client):
    _mock_services()
    respx.get(f"{RESUMEN}/health").mock(
        side_effect=httpx.ReadTimeout("read timed out")
    )

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["dependencies"]["resumen"]["detail"] == "timeout"


def test_liveness_conserva_respuesta_documentada(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "orquestador-service"}


@respx.mock
def test_redis_no_bloquea_readiness_si_cache_esta_deshabilitado(client):
    _mock_services()

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json()["dependencies"]["redis"]["status"] == "disabled"


@respx.mock
def test_redis_requerido_falla_readiness_si_cache_esta_habilitado(client, monkeypatch):
    import App.main as main_module

    _mock_services()
    monkeypatch.setattr(main_module.settings, "cache_enabled", True)

    async def redis_caido():
        return {"status": "error", "detail": "connection_error", "required": True}

    monkeypatch.setattr(main_module, "_check_redis", redis_caido)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["dependencies"]["redis"]["status"] == "error"
