"""Cliente HTTP que agrupa las llamadas a los 3 microservicios coordinados.

Toda la comunicación saliente del orquestador pasa por acá — es el punto
donde se agregarían Retry y Circuit Breaker.
"""

import httpx

from App.exceptions import PasoSagaError


class MicroserviciosClient:
    def __init__(self, documentos_url: str, extraccion_url: str, resumen_url: str, notificaciones_url: str, timeout: float = 30.0):
        self.documentos_url = documentos_url.rstrip("/")
        self.extraccion_url = extraccion_url.rstrip("/")
        self.resumen_url = resumen_url.rstrip("/")
        self.notificaciones_url = notificaciones_url.rstrip("/")
        self.timeout = timeout

    async def _post(self, url: str, json: dict, paso: str) -> dict:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                resp = await client.post(url, json=json)
            except httpx.HTTPError as exc:
                raise PasoSagaError(paso, f"no se pudo contactar el servicio: {exc}") from exc
        if resp.status_code >= 400:
            raise PasoSagaError(paso, f"HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    async def subir_documento(self, nombre: str, filename: str, contenido: bytes) -> int:
        """Sube un PDF a documentos-service y devuelve el document_id."""
        url = f"{self.documentos_url}/api/v1/documents"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                files = {"file": (filename, contenido, "application/pdf")}
                data = {"name": nombre}
                resp = await client.post(url, data=data, files=files)
            except httpx.HTTPError as exc:
                raise PasoSagaError("subida", f"no se pudo subir el documento: {exc}") from exc
        if resp.status_code >= 400:
            raise PasoSagaError("subida", f"HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.json()["id"]

    async def extraer(self, document_id: int) -> str:
        """Llama a extraccion-service. Devuelve el texto extraído."""
        data = await self._post(
            f"{self.extraccion_url}/api/v1/extract",
            {"document_id": document_id},
            paso="extraccion",
        )
        return data["extracted_text"]

    async def resumir(self, texto: str, max_words: int) -> str:
        """Llama a resumen-service. Devuelve el resumen."""
        data = await self._post(
            f"{self.resumen_url}/api/v1/summarize",
            {"text": texto, "max_words": max_words},
            paso="resumen",
        )
        return data["summary"]

    async def notificar(self, document_id: int, estado: str, detalle: str = "") -> None:
        """Llama a notificaciones-service para registrar un estado."""
        await self._post(
            f"{self.notificaciones_url}/api/v1/estados",
            {"document_id": document_id, "estado": estado, "detalle": detalle},
            paso="notificacion",
        )
