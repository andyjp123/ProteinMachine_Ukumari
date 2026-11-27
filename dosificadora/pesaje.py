from math import isfinite
from typing import Protocol


class Balanza(Protocol):
    def masa_estable_g(self, tiempo_max_s: float) -> float:
        """Obtiene una lectura estable o lanza TimeoutError dentro del plazo."""


def leer_masa_g(balanza: Balanza, tiempo_max_s: float) -> float:
    masa_g = balanza.masa_estable_g(tiempo_max_s)
    if not isfinite(masa_g):
        raise ValueError("La lectura de masa no es válida.")
    return masa_g
