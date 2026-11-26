from collections.abc import Callable
from enum import Enum
from time import monotonic

BAUDRATE = 115200
PUERTO_PREDETERMINADO = "/dev/ttyACM0"
ESPERA_ARDUINO_S = 2
REINTENTO_S = 2


class EstadoConexion(Enum):
    DESCONECTADO = "Desconectado"
    CONECTANDO = "Conectando"
    CONECTADO = "Conectado"
    RECONECTANDO = "Reconectando"
    ERROR = "Error"


class ConexionSerial:
    """Intercambia líneas con Arduino mediante sondeos periódicos del llamador."""

    def __init__(
        self,
        recibir: Callable[[str], None],
        informar: Callable[[EstadoConexion, str], None],
        registrar: Callable[[str], None],
    ):
        self.recibir = recibir
        self.informar = informar
        self.registrar = registrar
        self.estado = EstadoConexion.DESCONECTADO
        self.puerto = ""
        self._serial = None
        self._proximo_paso = 0.0
        self._entrada = bytearray()

    @staticmethod
    def listar_puertos() -> list[str]:
        from serial.tools.list_ports import comports

        return [puerto.device for puerto in comports()]

    @staticmethod
    def _abrir(puerto):
        from serial import Serial

        return Serial(puerto, BAUDRATE, timeout=0, write_timeout=0.2)

    def _cambiar_estado(self, estado, detalle=""):
        self.estado = estado
        self.informar(estado, detalle)

    def conectar(self, puerto: str) -> None:
        if not puerto:
            return
        self._cerrar_puerto()
        self.puerto = puerto
        self._conectar(reintento=False)

    def _conectar(self, reintento: bool) -> None:
        try:
            self._serial = self._abrir(self.puerto)
        except OSError as error:
            if reintento:
                self._proximo_paso = monotonic() + REINTENTO_S
            else:
                self._cambiar_estado(EstadoConexion.ERROR, str(error))
            return

        self._proximo_paso = monotonic() + ESPERA_ARDUINO_S
        self._cambiar_estado(EstadoConexion.CONECTANDO, self.puerto)

    def _cerrar_puerto(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except OSError:
                pass
            self._serial = None
        self._entrada.clear()

    def desconectar(self) -> None:
        self._cerrar_puerto()
        self._cambiar_estado(EstadoConexion.DESCONECTADO)

    def _perder_conexion(self) -> None:
        self._cerrar_puerto()
        self.registrar("Conexión USB perdida. Intentando reconectar...")
        self._proximo_paso = monotonic() + REINTENTO_S
        self._cambiar_estado(EstadoConexion.RECONECTANDO, self.puerto)

    def _escribir(self, comando: str) -> None:
        datos = f"{comando}\n".encode("utf-8")
        if self._serial.write(datos) != len(datos):
            raise OSError("Escritura serial incompleta.")

    def enviar(self, comando: str) -> None:
        if self.estado is not EstadoConexion.CONECTADO:
            return
        try:
            self._escribir(comando)
        except OSError:
            self._perder_conexion()
        else:
            self.registrar(f"> {comando}")

    def sondear(self) -> None:
        if self.estado is EstadoConexion.RECONECTANDO:
            if monotonic() >= self._proximo_paso:
                self._conectar(reintento=True)
            return

        if self.estado is EstadoConexion.CONECTANDO:
            if monotonic() < self._proximo_paso:
                return
            try:
                self._escribir("INVERT")
            except OSError:
                self._perder_conexion()
                return
            self.registrar(f"Conectado a {self.puerto}")
            self.registrar("> INVERT (Automático)")
            self._cambiar_estado(EstadoConexion.CONECTADO, self.puerto)

        if self.estado is not EstadoConexion.CONECTADO:
            return
        try:
            disponibles = self._serial.in_waiting
            if not disponibles:
                return
            self._entrada.extend(self._serial.read(min(disponibles, 4096)))
        except OSError:
            self._perder_conexion()
            return

        lineas = self._entrada.split(b"\n")
        self._entrada = lineas.pop()
        for datos in lineas:
            linea = datos.decode("utf-8", errors="ignore").strip()
            if linea:
                self.recibir(linea)
