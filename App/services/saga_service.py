"""SagaService: orquesta el flujo completo con compensación y cache.

Flujo feliz:
    (cache hit?) -> subido -> extraer -> resumir -> notificado -> (guardar en cache)

Si cualquier paso falla, se ejecuta la COMPENSACIÓN: se marca el documento
como "error" en notificaciones (con el detalle) y se corta el flujo. Esto es
el patrón Saga orquestado: un coordinador central dirige los pasos y decide
qué hacer si algo sale mal, ya que no hay una transacción única que abarque
a todos los microservicios.

Cache: antes de procesar, se consulta si ya hay un resultado exitoso para ese
documento; si lo hay, se devuelve sin volver a llamar a los microservicios
(ahorra la llamada cara a la IA). Al terminar con éxito, se guarda el
resultado en cache.
"""

from typing import Optional

from App.exceptions import PasoSagaError
from App.models.resultado_saga import ResultadoSaga
from App.services.cache import Cache
from App.services.microservicios_client import MicroserviciosClient


class SagaService:
    def __init__(self, client: MicroserviciosClient, cache: Optional[Cache] = None, max_words: int = 150):
        self.client = client
        self.cache = cache
        self.max_words = max_words

    async def procesar(self, document_id: int, forzar: bool = False) -> ResultadoSaga:
        # Cache: si ya se procesó con éxito, devolver sin rehacer el trabajo
        if self.cache and not forzar:
            cacheado = await self.cache.get(document_id)
            if cacheado is not None:
                return cacheado

        resultado = await self._ejecutar_saga(document_id)

        if self.cache and resultado.exito:
            await self.cache.set(resultado)

        return resultado

    async def _ejecutar_saga(self, document_id: int) -> ResultadoSaga:
        pasos_completados: list[str] = []
        try:
            await self.client.notificar(document_id, "subido", "inicio del procesamiento")
            pasos_completados.append("subido")

            texto = await self.client.extraer(document_id)
            await self.client.notificar(document_id, "extraido", f"{len(texto)} caracteres")
            pasos_completados.append("extraido")

            resumen = await self.client.resumir(texto, self.max_words)
            await self.client.notificar(document_id, "resumido", f"{len(resumen)} caracteres")
            pasos_completados.append("resumido")

            await self.client.notificar(document_id, "notificado", "procesamiento completo")
            pasos_completados.append("notificado")

            return ResultadoSaga(
                document_id=document_id, exito=True, estado_final="notificado",
                pasos_completados=pasos_completados, resumen=resumen,
            )
        except PasoSagaError as exc:
            await self._compensar(document_id, exc)
            return ResultadoSaga(
                document_id=document_id, exito=False, estado_final="error",
                pasos_completados=pasos_completados, error=f"[{exc.paso}] {exc.detalle}",
            )

    async def _compensar(self, document_id: int, exc: PasoSagaError) -> None:
        """Compensación best-effort: marcar el estado como error sin que un
        fallo del propio notificaciones oculte el error original."""
        try:
            await self.client.notificar(document_id, "error", f"falló en {exc.paso}: {exc.detalle}")
        except PasoSagaError:
            pass
