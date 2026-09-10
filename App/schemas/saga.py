"""Schemas (DTOs) de la API del orquestador."""

from typing import List, Optional

from pydantic import BaseModel


class ProcesarResponse(BaseModel):
    document_id: int
    exito: bool
    estado_final: str
    pasos_completados: List[str]
    resumen: Optional[str] = None
    error: Optional[str] = None
