"""Schemas (DTOs) de la API del orquestador."""

from pydantic import BaseModel


class ProcesarResponse(BaseModel):
    document_id: int
    exito: bool
    estado_final: str
    pasos_completados: list[str]
    resumen: str | None = None
    error: str | None = None
