from .recetas import Estacion


class MaquinaSimulada:
    def __init__(
        self,
        recipiente_presente: bool = True,
        estacion_averiada: Estacion | None = None,
    ) -> None:
        self.recipiente_presente = recipiente_presente
        self.estacion_averiada = estacion_averiada
        self.estacion = Estacion.AGUA
        self.masa_g = 30.0 if recipiente_presente else 0.0

    def detectar(self, tiempo_max_s: float) -> bool:
        return self.recipiente_presente

    def posicion(self, tiempo_max_s: float) -> Estacion | None:
        if self.estacion == self.estacion_averiada:
            return None
        return self.estacion

    def confirmar(self, estacion: Estacion, tiempo_max_s: float) -> None:
        if self.posicion(tiempo_max_s) != estacion:
            raise TimeoutError(f"No se confirmó la estación {estacion.value}.")

    def mover_a(self, estacion: Estacion, tiempo_max_s: float) -> None:
        self.estacion = estacion
        self.confirmar(estacion, tiempo_max_s)

    def masa_estable_g(self, tiempo_max_s: float) -> float:
        return self.masa_g

    def pulso(self, estacion: Estacion, tiempo_max_s: float) -> None:
        self.confirmar(estacion, tiempo_max_s)
        if not self.recipiente_presente:
            raise RuntimeError("Falta el recipiente.")
        self.masa_g += 25.0 if estacion == Estacion.AGUA else 2.5

    def detener(self) -> None:
        """La simulación completa cada movimiento y pulso en la misma llamada."""
