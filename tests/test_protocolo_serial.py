import unittest
from unittest.mock import Mock, patch

from dosificadora.carro import Carro
from dosificadora.conexion_serial import ConexionSerial, EstadoConexion
from dosificadora.sistema_agua import SistemaAgua


class ProtocoloSerialTest(unittest.TestCase):
    def setUp(self):
        self.puerto = Mock()
        self.puerto.in_waiting = 0
        self.puerto.write.side_effect = len
        self.recibir = Mock()
        self.conexion = ConexionSerial(self.recibir, Mock(), Mock())
        self.reloj = patch("dosificadora.conexion_serial.monotonic", return_value=0).start()
        self.abrir = patch.object(self.conexion, "_abrir", return_value=self.puerto).start()
        self.addCleanup(patch.stopall)

    def conectar(self):
        self.conexion.conectar("PUERTO-FALSO")
        self.conexion.enviar("RUN 4")
        self.conexion.sondear()
        self.puerto.write.assert_not_called()
        self.reloj.return_value = 2
        self.conexion.sondear()
        self.puerto.write.assert_called_once_with(b"INVERT\n")

    def test_comandos_exactos_sin_secuencia_adicional(self):
        self.conectar()
        carro = Carro(self.conexion.enviar)
        agua = SistemaAgua(self.conexion.enviar)
        for estacion in (4, 3, 2):
            carro.iniciar_pedido(estacion)
        carro.llevar_a_inicio()
        carro.avanzar()
        carro.regresar()
        agua.probar()
        carro.invertir()
        carro.fijar_velocidad(135)
        carro.fijar_retorno(False)
        carro.fijar_retorno(True)
        carro.detener()

        self.assertEqual([args.args[0] for args in self.puerto.write.call_args_list], [
            b"INVERT\n", b"RUN 4\n", b"RUN 3\n", b"RUN 2\n", b"HOME\n",
            b"FORWARD\n", b"REVERSE\n", b"PUMP\n", b"INVERT\n", b"SPEED 135\n",
            b"RETURN_OFF\n", b"RETURN_ON\n", b"STOP\n",
        ])

    def test_lineas_fragmentadas_y_estaciones(self):
        self.conectar()
        self.puerto.in_waiting = 30
        self.puerto.read.side_effect = [b"SENS:1,0,", b"0,0,1\r\nBomba apagada\n"]
        self.conexion.sondear()
        self.recibir.assert_not_called()
        self.conexion.sondear()

        sensores, bomba = (llamada.args[0] for llamada in self.recibir.call_args_list)
        carro = Carro(self.conexion.enviar)
        self.assertTrue(carro.actualizar_sensores(sensores))
        self.assertEqual(carro.sensores_ir, {1: True, 2: False, 3: False, 4: False, 5: True})
        self.assertTrue(carro.actualizar_sensores("SENS:0,0,asd,0,0"))
        self.assertTrue(carro.sensores_ir[5])
        self.assertIs(SistemaAgua.estado_bomba(bomba), False)
        self.assertIs(SistemaAgua.estado_bomba("Bomba de agua encendida"), True)

    def test_reconexion_sin_reenviar_pedido(self):
        self.conectar()
        self.puerto.write.side_effect = OSError("USB desconectado")
        self.conexion.enviar("RUN 3")
        self.assertIs(self.conexion.estado, EstadoConexion.RECONECTANDO)
        self.puerto.close.assert_called_once()

        nuevo_puerto = Mock()
        nuevo_puerto.in_waiting = 0
        nuevo_puerto.write.side_effect = len
        self.abrir.side_effect = [OSError("Puerto ausente"), nuevo_puerto]
        for segundo in (4, 6, 8):
            self.reloj.return_value = segundo
            self.conexion.sondear()
        self.assertIs(self.conexion.estado, EstadoConexion.CONECTADO)
        self.abrir.assert_called_with("PUERTO-FALSO")
        nuevo_puerto.write.assert_called_once_with(b"INVERT\n")

    def test_desconexion_manual_cancela_reintento_pendiente(self):
        self.conectar()
        self.puerto.in_waiting = 1
        self.puerto.read.side_effect = OSError("USB desconectado")
        self.conexion.sondear()
        self.assertIs(self.conexion.estado, EstadoConexion.RECONECTANDO)
        self.conexion.desconectar()
        self.reloj.return_value = 10
        self.conexion.sondear()
        self.assertIs(self.conexion.estado, EstadoConexion.DESCONECTADO)
        self.abrir.assert_called_once()
