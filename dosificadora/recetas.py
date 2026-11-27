from dataclasses import dataclass
from enum import Enum


class Estacion(str, Enum):
    AGUA = "agua"
    VAINILLA = "polvo_vainilla"
    CHOCOLATE = "polvo_chocolate"
    ENTREGA = "entrega"


@dataclass(frozen=True)
class Receta:
    sabor: str
    estacion_polvo: Estacion
    agua_g: float
    polvo_g: float


RECETAS = {
    "vainilla": Receta("Vainilla", Estacion.VAINILLA, 250.0, 25.0),
    "chocolate": Receta("Chocolate", Estacion.CHOCOLATE, 250.0, 25.0),
}
