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


def test_compose_keeps_docker_routes_and_maps_equivalent_consul_tags():
    traefik = (ROOT / "infra" / "services" / "traefik" / "compose.yaml").read_text(
        encoding="utf-8"
    )
    assert "--providers.docker=true" in traefik
    assert "--providers.consulcatalog=true" in traefik
    assert "--providers.consulcatalog.strictchecks=passing" in traefik

    for service, routes in SERVICE_ROUTES.items():
        compose = (
            ROOT / "infra" / "services" / service / "compose.yaml"
        ).read_text(encoding="utf-8")
        assert "CONSUL_HTTP_ADDR: http://consul:8500" in compose
        assert f"CONSUL_SERVICE_NAME: {service}" in compose
        assert 'CONSUL_SERVICE_PORT: "8000"' in compose
        tags_line = next(line for line in compose.splitlines() if "CONSUL_SERVICE_TAGS:" in line)
        assert "traefik.enable=true" in tags_line

        for router, rule in routes:
            assert f"traefik.http.routers.{router}.rule={rule}" in compose
            assert f"traefik.http.routers.{router}-consul.rule={rule}" in tags_line
