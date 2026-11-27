from typing import Protocol

from .recetas import Estacion


class SensorRecipiente(Protocol):
    def detectar(self, tiempo_max_s: float) -> bool:
        """Espera una detección válida del sensor infrarrojo dentro del plazo."""


class SensoresEstacion(Protocol):
    def posicion(self, tiempo_max_s: float) -> Estacion | None:
        """Lee la estación detectada o devuelve None entre estaciones."""
