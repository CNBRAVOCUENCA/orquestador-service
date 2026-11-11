from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICE_ROUTES = {
    "documentos": (
        ("documentos", "Host(`documentos.localhost`)"),
        ("documentos-public", "PathPrefix(`/api/v1/documents`)"),
        ("documentos-docs", "PathPrefix(`/docs`) || Path(`/openapi.json`)"),
    ),
    "extraccion": (
        ("extraccion", "Host(`extraccion.localhost`)"),
        ("extraccion-public", "PathPrefix(`/api/v1/extract`)"),
        ("extraccion-sync", "Path(`/extract`)"),
    ),
    "resumen": (
        ("resumen", "Host(`resumen.localhost`)"),
        ("resumen-public", "PathPrefix(`/api/v1/summarize`)"),
    ),
    "notificaciones": (
        ("notificaciones", "Host(`notificaciones.localhost`)"),
        ("notificaciones-public", "PathPrefix(`/api/v1/estados`)"),
    ),
    "orquestador": (
        ("orquestador", "Host(`${ORQUESTADOR_HOST:-orquestador.localhost}`)"),
        ("orquestador-public", "PathPrefix(`/api/v1/procesar`)"),
    ),
}
PUBLIC_ROUTERS = {
    "documentos": ("documentos-public", "documentos-docs"),
    "extraccion": ("extraccion-public", "extraccion-sync"),
    "resumen": ("resumen-public",),
    "notificaciones": ("notificaciones-public",),
    "orquestador": ("orquestador-public",),
}


INTERNAL_ROUTERS = {
    "documentos": (("documentos-internal", "PathPrefix(`/api/v1/documents`)"),),
    "extraccion": (
        ("extraccion-internal", "PathPrefix(`/api/v1/extract`)"),
        ("extraccion-sync-internal", "Path(`/extract`)"),
    ),
    "resumen": (("resumen-internal", "PathPrefix(`/api/v1/summarize`)"),),
    "notificaciones": (("notificaciones-internal", "PathPrefix(`/api/v1/estados`)"),),
}
PROTEGIDOS = {**PUBLIC_ROUTERS, "documentos": ("documentos-public",)}


def _compose(service: str) -> str:
    return (ROOT / "infra" / "services" / service / "compose.yaml").read_text(encoding="utf-8")


def _tags(service: str) -> str:
    return next(line for line in _compose(service).splitlines() if "CONSUL_SERVICE_TAGS:" in line)


def test_consul_es_el_unico_proveedor_de_rutas():
    """Un solo proveedor por ruta (prompt 8): Traefik descubre los servicios solo por Consul."""
    traefik = (ROOT / "infra" / "services" / "traefik" / "compose.yaml").read_text(encoding="utf-8")
    assert "--providers.consulcatalog=true" in traefik
    assert "--providers.consulcatalog.strictchecks=passing" in traefik
    assert "--providers.docker" not in traefik
    assert "docker.sock" not in traefik  # sin acceso al socket de Docker

    for service in SERVICE_ROUTES:
        compose = _compose(service)
        assert "labels:" not in compose
        assert "CONSUL_HTTP_ADDR: http://consul:8500" in compose
        assert f"CONSUL_SERVICE_NAME: {service}" in compose
        assert 'CONSUL_SERVICE_PORT: "8000"' in compose


def test_tags_de_consul_definen_todas_las_rutas():
    for service, routes in SERVICE_ROUTES.items():
        tags = _tags(service)
        assert "traefik.enable=true" in tags
        for router, rule in routes:
            assert f"traefik.http.routers.{router}-consul.rule={rule}" in tags
    for service, routes in INTERNAL_ROUTERS.items():
        tags = _tags(service)
        for router, rule in routes:
            assert f"traefik.http.routers.{router}-consul.rule={rule}" in tags
            assert f"traefik.http.routers.{router}-consul.entrypoints=web-internal" in tags
            assert f"traefik.http.routers.{router}-consul.middlewares=api-circuitbreaker@file" in tags


def test_public_routes_are_limited_to_the_web_entrypoint():
    for service, routers in PUBLIC_ROUTERS.items():
        tags = _tags(service)
        for router in routers:
            assert f"traefik.http.routers.{router}-consul.entrypoints=web" in tags


def test_rutas_publicas_aplican_rate_limit_y_circuit_breaker():
    resilience = (
        ROOT / "infra" / "services" / "traefik" / "dynamic" / "resilience.yml"
    ).read_text(encoding="utf-8")
    assert "api-publico:" in resilience
    assert "- api-ratelimit" in resilience
    assert "- api-circuitbreaker" in resilience
    for service, routers in PROTEGIDOS.items():
        tags = _tags(service)
        for router in routers:
            assert f"traefik.http.routers.{router}-consul.middlewares=api-publico@file" in tags


def test_las_etiquetas_de_consul_no_llevan_comas_dentro_de_un_valor():
    """CONSUL_SERVICE_TAGS se separa por coma: cada etiqueta debe ser clave=valor completo."""
    for service in SERVICE_ROUTES:
        valor = _tags(service).split('"')[1]
        for tag in valor.split(","):
            assert tag.startswith("traefik."), (service, tag)
            assert "=" in tag, (service, tag)
