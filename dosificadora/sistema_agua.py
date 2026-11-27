from collections.abc import Callable


class SistemaAgua:
    DURACION_S = 6

    def __init__(self, enviar: Callable[[str], None]):
        self._enviar = enviar

    def probar(self) -> None:
        """Solicita la prueba de bomba cuyo tiempo gestiona Arduino."""
        self._enviar("PUMP")

    @staticmethod
    def estado_bomba(linea: str) -> bool | None:
        if "Bomba de agua encendida" in linea or "Bomba encendida" in linea:
            return True
        if "Bomba apagada" in linea:
            return False
        return None
