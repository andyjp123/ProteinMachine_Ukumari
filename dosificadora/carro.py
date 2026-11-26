from collections.abc import Callable
from typing import Protocol

from .recetas import Estacion


class CarroCiclo(Protocol):
    def confirmar(self, estacion: Estacion, tiempo_max_s: float) -> None:
        """Confirma mediante sensores que el carro está detenido en la estación."""

    def mover_a(self, estacion: Estacion, tiempo_max_s: float) -> None:
        """Mueve el carro y confirma la llegada con los sensores de estación.

        Ante un fallo o vencimiento del plazo, detiene el motor y lanza un error.
        """

    def detener(self) -> None:
        """Detiene el motor del carro. Puede ejecutarse más de una vez."""


class Carro:
    """Control serial del transporte y estado de los IR por estación."""

    def __init__(self, enviar: Callable[[str], None]):
        self._enviar = enviar
        self.sensores_ir: dict[int, bool] = {}

    def iniciar_pedido(self, estacion: int) -> None:
        if estacion not in (4, 3, 2):
            raise ValueError(f"Estación de proteína inválida: {estacion}")
        self._enviar(f"RUN {estacion}")

    def llevar_a_inicio(self) -> None:
        self._enviar("HOME")

    def avanzar(self) -> None:
        self._enviar("FORWARD")

    def regresar(self) -> None:
        self._enviar("REVERSE")

    def detener(self) -> None:
        self._enviar("STOP")

    def invertir(self) -> None:
        self._enviar("INVERT")

    def fijar_velocidad(self, pwm: int) -> None:
        self._enviar(f"SPEED {pwm}")

    def fijar_retorno(self, habilitado: bool) -> None:
        self._enviar("RETURN_ON" if habilitado else "RETURN_OFF")

    def actualizar_sensores(self, linea: str) -> bool:
        if not linea.startswith("SENS:"):
            return False
        valores = linea.removeprefix("SENS:").split(",")
        if len(valores) == 5 and all(valor in ("0", "1") for valor in valores):
            self.sensores_ir = {
                estacion: valor == "1"
                for estacion, valor in enumerate(valores, start=1)
            }
        return True
