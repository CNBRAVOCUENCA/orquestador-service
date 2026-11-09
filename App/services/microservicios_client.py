"""Cliente HTTP que agrupa las llamadas a los microservicios coordinados.

Toda la comunicación saliente del orquestador pasa por acá — es el punto
donde se agregarían Retry y Circuit Breaker.
"""

from typing import Any, Protocol

import httpx

from App.exceptions import PasoSagaError


class ServiciosPort(Protocol):
    """Lo que la Saga necesita de los demás microservicios (DIP).

    SagaService depende de esta interfaz y no del cliente HTTP concreto, así
    se puede probar con un doble sin levantar ningún servicio.
    """

    async def subir_documento(self, nombre: str, filename: str, contenido: bytes) -> int: ...

    async def extraer(self, document_id: int) -> str: ...

    async def resumir(self, texto: str, max_words: int) -> str: ...

    async def notificar(self, document_id: int, estado: str, detalle: str = "") -> None: ...


class MicroserviciosClient:
    """Implementación HTTP de ServiciosPort."""

    def __init__(
        self,
        documentos_url: str,
        extraccion_url: str,
        resumen_url: str,
        notificaciones_url: str,
        timeout: float = 30.0,
    ):
        self.documentos_url = documentos_url.rstrip("/")
        self.extraccion_url = extraccion_url.rstrip("/")
        self.resumen_url = resumen_url.rstrip("/")
        self.notificaciones_url = notificaciones_url.rstrip("/")
        self.timeout = timeout

    async def _post(self, url: str, paso: str, **kwargs: Any) -> dict:
        """POST común: traduce fallos de red y respuestas >= 400 a PasoSagaError."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, **kwargs)
            except httpx.HTTPError as exc:
                raise PasoSagaError(paso, f"no se pudo contactar el servicio: {exc}") from exc
        if resp.status_code >= 400:
            raise PasoSagaError(
                paso, f"HTTP {resp.status_code}: {resp.text[:200]}", status_code=resp.status_code
            )
        return resp.json()

    async def subir_documento(self, nombre: str, filename: str, contenido: bytes) -> int:
        """Sube un PDF a documentos-service y devuelve el document_id."""
        data = await self._post(
            f"{self.documentos_url}/api/v1/documents",
            paso="subida",
            data={"name": nombre},
            files={"file": (filename, contenido, "application/pdf")},
        )
        return data["id"]

    async def extraer(self, document_id: int) -> str:
        """Llama a extraccion-service. Devuelve el texto extraído."""
        data = await self._post(
            f"{self.extraccion_url}/api/v1/extract",
            paso="extraccion",
            json={"document_id": document_id},
        )
        return data["extracted_text"]

    async def resumir(self, texto: str, max_words: int) -> str:
        """Llama a resumen-service. Devuelve el resumen."""
        data = await self._post(
            f"{self.resumen_url}/api/v1/summarize",
            paso="resumen",
            json={"text": texto, "max_words": max_words},
        )
        return data["summary"]

    async def notificar(self, document_id: int, estado: str, detalle: str = "") -> None:
        """Llama a notificaciones-service para registrar un estado."""
        await self._post(
            f"{self.notificaciones_url}/api/v1/estados",
            paso="notificacion",
            json={"document_id": document_id, "estado": estado, "detalle": detalle},
        )
