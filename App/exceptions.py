"""Excepciones de dominio del orquestador."""


class OrquestadorException(Exception):
    """Excepción base."""


class PasoSagaError(OrquestadorException):
    """Un paso de la Saga falló.

    Lleva el nombre del paso, el detalle y, si el servicio llegó a responder,
    el código HTTP (`status_code`). Si el servicio no respondió (caído,
    timeout), `status_code` es None.
    """

    def __init__(self, paso: str, detalle: str, status_code: int | None = None):
        self.paso = paso
        self.detalle = detalle
        self.status_code = status_code
        super().__init__(f"Falló el paso '{paso}': {detalle}")
