from time import monotonic
from typing import Protocol

from .pesaje import Balanza, leer_masa_g
from .recetas import Estacion


class Dispensador(Protocol):
    def pulso(self, estacion: Estacion, tiempo_max_s: float) -> None:
        """Dispensa un pulso y termina con las salidas de dosificación apagadas."""

    def detener(self) -> None:
        """Desactiva agua, tornillo y agitador. Puede ejecutarse más de una vez."""


def dosificar(
    dispensador: Dispensador,
    balanza: Balanza,
    estacion: Estacion,
    objetivo_g: float,
    tolerancia_g: float,
    tiempo_max_s: float,
) -> float:
    limite = monotonic() + tiempo_max_s

    def tiempo_restante() -> float:
        restante = limite - monotonic()
        if restante <= 0:
            raise TimeoutError(f"No se completó la dosis en {estacion.value}.")
        return restante

    referencia_g = leer_masa_g(balanza, tiempo_restante())
    while True:
        dispensador.pulso(estacion, tiempo_restante())
        masa_g = leer_masa_g(balanza, tiempo_restante()) - referencia_g
        tiempo_restante()
        if masa_g > objetivo_g + tolerancia_g:
            raise ValueError(f"Sobredosis en {estacion.value}: {masa_g:.1f} g.")
        if masa_g >= objetivo_g - tolerancia_g:
            return masa_g
