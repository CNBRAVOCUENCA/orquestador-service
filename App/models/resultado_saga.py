"""Modelo de dominio para el resultado de ejecutar la Saga."""

from typing import List, Optional

from pydantic import BaseModel


class ResultadoSaga(BaseModel):
    document_id: int
    exito: bool
    estado_final: str          # "resumido" si todo ok, "error" si algo falló
    pasos_completados: List[str]
    resumen: Optional[str] = None
    error: Optional[str] = None
