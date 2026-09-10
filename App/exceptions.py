"""Excepciones de dominio del orquestador."""


class OrquestadorException(Exception):
    """Excepción base."""


class PasoSagaError(OrquestadorException):
    """Un paso de la Saga falló. Lleva el nombre del paso y el detalle."""

    def __init__(self, paso: str, detalle: str):
        self.paso = paso
        self.detalle = detalle
        super().__init__(f"Falló el paso '{paso}': {detalle}")
