"""Registro opcional del orquestador en el agente local de Consul."""

import logging
import socket
from urllib.parse import quote, urlsplit

import httpx

from App.config.settings import Settings

logger = logging.getLogger(__name__)


def _instance_address(consul_http_addr: str) -> str:
    consul_url = urlsplit(consul_http_addr)
    if not consul_url.hostname:
        raise RuntimeError("Could not discover this instance's IPv4 address")

    port = consul_url.port or (443 if consul_url.scheme == "https" else 8500)
    try:
        addresses = socket.getaddrinfo(
            consul_url.hostname,
            port,
            family=socket.AF_INET,
            type=socket.SOCK_DGRAM,
        )
        for family, socket_type, protocol, _, address in addresses:
            with socket.socket(family, socket_type, protocol) as route_socket:
                route_socket.connect(address)
                ip_address = route_socket.getsockname()[0]
                if not ip_address.startswith("127."):
                    return ip_address
    except OSError:
        pass
    raise RuntimeError("Could not discover this instance's IPv4 address")


class ConsulRegistration:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._service_id: str | None = None

    async def register(self) -> None:
        if not self._settings.consul_http_addr:
            return

        service_name = self._settings.consul_service_name or self._settings.app_name
        hostname = socket.gethostname()
        service_address = self._settings.consul_service_address or _instance_address(
            self._settings.consul_http_addr
        )
        service_id = f"{service_name}-{hostname}"
        payload = {
            "Name": service_name,
            "ID": service_id,
            "Address": service_address,
            "Port": self._settings.consul_service_port,
            "Tags": [tag.strip() for tag in self._settings.consul_service_tags.split(",") if tag.strip()],
            "Check": {
                "HTTP": f"http://{service_address}:{self._settings.consul_service_port}/health",
                "Interval": "10s",
                "Timeout": "2s",
                "DeregisterCriticalServiceAfter": "1m",
            },
        }
        try:
            async with httpx.AsyncClient(
                headers=self._headers(),
                timeout=2.0,
            ) as client:
                response = await client.put(
                    f"{self._settings.consul_http_addr.rstrip('/')}/v1/agent/service/register",
                    json=payload,
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            response = getattr(error, "response", None)
            status_code = response.status_code if response else "unavailable"
            raise RuntimeError(f"Consul service registration failed (HTTP status {status_code})") from None
        self._service_id = service_id
        logger.info("Registered service %s with Consul", service_name)

    async def deregister(self) -> None:
        if self._service_id is None:
            return

        try:
            async with httpx.AsyncClient(headers=self._headers(), timeout=2.0) as client:
                response = await client.put(
                    f"{self._settings.consul_http_addr.rstrip('/')}/v1/agent/service/deregister/"
                    f"{quote(self._service_id, safe='')}"
                )
                response.raise_for_status()
        except httpx.HTTPError as error:
            status_code = getattr(error, "response", None)
            logger.warning(
                "Consul service deregistration failed (HTTP status %s)",
                status_code.status_code if status_code else "unavailable",
            )
        else:
            logger.info("Deregistered service %s from Consul", self._service_id)
        finally:
            self._service_id = None

    def _headers(self) -> dict[str, str]:
        if self._settings.consul_http_token:
            return {"X-Consul-Token": self._settings.consul_http_token}
        return {}
