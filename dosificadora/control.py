from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from .carro import CarroCiclo
from .dosificacion import Dispensador, dosificar
from .pesaje import Balanza
from .recetas import Estacion, Receta
from .sensores import SensorRecipiente


class Estado(str, Enum):
    ESPERAR_RECIPIENTE = "Esperando recipiente"
    DOSIFICAR_AGUA = "Dosificando agua"
    MOVER_A_POLVO = "Trasladando a la estación de polvo"
    DOSIFICAR_POLVO = "Dosificando polvo"
    MOVER_A_ENTREGA = "Trasladando a la entrega"
    ENTREGADO = "Bebida lista para retirar"
    FALLA = "Preparación interrumpida"


@dataclass(frozen=True)
class ParametrosCiclo:
    recipiente_s: float = 10.0
    recorrido_s: float = 8.0
    agua_s: float = 20.0
    polvo_s: float = 15.0
    tolerancia_agua_g: float = 2.0
    tolerancia_polvo_g: float = 0.5


@dataclass(frozen=True)
class Resultado:
    agua_g: float
    polvo_g: float


class Controlador:
    def __init__(
        self,
        recipiente: SensorRecipiente,
        carro: CarroCiclo,
        balanza: Balanza,
        dispensador: Dispensador,
        parametros: ParametrosCiclo,
    ) -> None:
        self.recipiente = recipiente
        self.carro = carro
        self.balanza = balanza
        self.dispensador = dispensador
        self.parametros = parametros

    def preparar(self, receta: Receta, informar: Callable[[Estado], None]) -> Resultado:
        p = self.parametros
        try:
            try:
                informar(Estado.ESPERAR_RECIPIENTE)
                self.carro.confirmar(Estacion.AGUA, p.recorrido_s)
                if not self.recipiente.detectar(p.recipiente_s):
                    raise TimeoutError("El sensor infrarrojo no detectó el recipiente.")

                informar(Estado.DOSIFICAR_AGUA)
                agua_g = dosificar(
                    self.dispensador, self.balanza, Estacion.AGUA,
                    receta.agua_g, p.tolerancia_agua_g, p.agua_s,
                )

                informar(Estado.MOVER_A_POLVO)
                self.carro.mover_a(receta.estacion_polvo, p.recorrido_s)
                informar(Estado.DOSIFICAR_POLVO)
                polvo_g = dosificar(
                    self.dispensador, self.balanza, receta.estacion_polvo,
                    receta.polvo_g, p.tolerancia_polvo_g, p.polvo_s,
                )

                informar(Estado.MOVER_A_ENTREGA)
                self.carro.mover_a(Estacion.ENTREGA, p.recorrido_s)
            finally:
                try:
                    self.dispensador.detener()
                finally:
                    self.carro.detener()
        except Exception:
            informar(Estado.FALLA)
            raise

        informar(Estado.ENTREGADO)
        return Resultado(agua_g, polvo_g)
