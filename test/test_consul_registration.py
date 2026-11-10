import json
import socket

import httpx
import pytest
import respx

from App.config.settings import Settings
from App.services.consul_registration import ConsulRegistration, _instance_address


@pytest.mark.asyncio
@respx.mock
async def test_registers_instance_with_consul_and_deregisters(monkeypatch):
    monkeypatch.setattr("App.services.consul_registration.socket.gethostname", lambda: "instance-123")
    monkeypatch.setattr("App.services.consul_registration._instance_address", lambda _: "172.20.0.5")
    register = respx.put("http://consul:8500/v1/agent/service/register").mock(
        return_value=httpx.Response(200)
    )
    deregister = respx.put(
        "http://consul:8500/v1/agent/service/deregister/orders-instance-123"
    ).mock(return_value=httpx.Response(200))
    settings = Settings(
        consul_http_addr="http://consul:8500",
        consul_http_token="local-test-token",
        consul_service_name="orders",
        consul_service_port=8000,
        consul_service_tags="traefik.enable=true,traefik.http.routers.orders.rule=PathPrefix(`/orders`)",
    )
    registration = ConsulRegistration(settings)

    await registration.register()
    await registration.deregister()

    payload = register.calls[0].request.content
    body = json.loads(payload)
    assert body["ID"] == "orders-instance-123"
    assert body["Address"] == "172.20.0.5"
    assert body["Port"] == 8000
    assert body["Tags"] == [
        "traefik.enable=true",
        "traefik.http.routers.orders.rule=PathPrefix(`/orders`)",
    ]
    assert body["Check"] == {
        "HTTP": "http://172.20.0.5:8000/health",
        "Interval": "10s",
        "Timeout": "2s",
        "DeregisterCriticalServiceAfter": "1m",
    }
    assert register.calls[0].request.headers["X-Consul-Token"] == "local-test-token"
    assert deregister.called


@pytest.mark.asyncio
@respx.mock
async def test_registration_failure_prevents_startup_and_does_not_expose_token(monkeypatch):
    monkeypatch.setattr("App.services.consul_registration.socket.gethostname", lambda: "instance-123")
    monkeypatch.setattr("App.services.consul_registration._instance_address", lambda _: "172.20.0.5")
    respx.put("http://consul:8500/v1/agent/service/register").mock(
        return_value=httpx.Response(403, text="local-test-token")
    )
    registration = ConsulRegistration(
        Settings(
            consul_http_addr="http://consul:8500",
            consul_http_token="local-test-token",
        )
    )

    with pytest.raises(RuntimeError, match="HTTP status 403") as error:
        await registration.register()
    assert "local-test-token" not in str(error.value)


@pytest.mark.asyncio
async def test_empty_consul_address_disables_registration():
    registration = ConsulRegistration(Settings(consul_http_addr=""))

    await registration.register()
    await registration.deregister()


def test_discovers_routable_container_ip_from_consul_route(monkeypatch):
    class RouteSocket:
        def __enter__(self):
            return self

        def __exit__(self, *_):
            return None

        def connect(self, address):
            assert address == ("192.0.2.10", 8500)

        def getsockname(self):
            return ("172.20.0.5", 45000)

    def getaddrinfo(host, port, **kwargs):
        assert host == "consul"
        assert port == 8500
        return [(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP, "", ("192.0.2.10", port))]

    monkeypatch.setattr("App.services.consul_registration.socket.getaddrinfo", getaddrinfo)
    monkeypatch.setattr("App.services.consul_registration.socket.socket", lambda *_: RouteSocket())

    assert _instance_address("http://consul:8500") == "172.20.0.5"
