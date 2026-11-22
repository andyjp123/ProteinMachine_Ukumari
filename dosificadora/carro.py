from typing import Protocol

from .recetas import Estacion


class Carro(Protocol):
    def confirmar(self, estacion: Estacion, tiempo_max_s: float) -> None:
        """Confirma mediante sensores que el carro está detenido en la estación."""

    def mover_a(self, estacion: Estacion, tiempo_max_s: float) -> None:
        """Mueve el carro y confirma la llegada con los sensores de estación.

        Ante un fallo o vencimiento del plazo, detiene el motor y lanza un error.
        """

    def detener(self) -> None:
        """Detiene el motor del carro. Puede ejecutarse más de una vez."""
