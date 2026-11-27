import unittest

from dosificadora.control import Controlador, Estado, ParametrosCiclo, Resultado
from dosificadora.recetas import RECETAS, Estacion
from dosificadora.simulacion import MaquinaSimulada


class CicloTest(unittest.TestCase):
    def preparar(self, maquina, receta, estados):
        controlador = Controlador(maquina, maquina, maquina, maquina, ParametrosCiclo())
        return controlador.preparar(receta, estados.append)

    def test_entrega_para_cada_receta(self):
        for receta in RECETAS.values():
            with self.subTest(sabor=receta.sabor):
                maquina = MaquinaSimulada()
                estados = []
                self.assertEqual(self.preparar(maquina, receta, estados), Resultado(250, 25))
                self.assertEqual(estados, [
                    Estado.ESPERAR_RECIPIENTE,
                    Estado.DOSIFICAR_AGUA,
                    Estado.MOVER_A_POLVO,
                    Estado.DOSIFICAR_POLVO,
                    Estado.MOVER_A_ENTREGA,
                    Estado.ENTREGADO,
                ])
                self.assertEqual(maquina.estacion, Estacion.ENTREGA)

    def test_sin_recipiente_no_sirve_agua(self):
        maquina = MaquinaSimulada(recipiente_presente=False)
        estados = []
        with self.assertRaisesRegex(TimeoutError, "infrarrojo"):
            self.preparar(maquina, RECETAS["vainilla"], estados)
        self.assertEqual(estados, [Estado.ESPERAR_RECIPIENTE, Estado.FALLA])
        self.assertEqual(maquina.masa_g, 0)

    def test_sin_confirmar_estacion_no_dosifica_polvo(self):
        maquina = MaquinaSimulada(estacion_averiada=Estacion.CHOCOLATE)
        estados = []
        with self.assertRaisesRegex(TimeoutError, "polvo_chocolate"):
            self.preparar(maquina, RECETAS["chocolate"], estados)
        self.assertEqual(estados[-1], Estado.FALLA)
        self.assertNotIn(Estado.DOSIFICAR_POLVO, estados)
        self.assertEqual(maquina.masa_g, 280)

    def test_sobredosis_interrumpe_antes_de_entregar(self):
        class PulsoExcesivo(MaquinaSimulada):
            def pulso(self, estacion, tiempo_max_s):
                super().pulso(estacion, tiempo_max_s)
                if estacion != Estacion.AGUA:
                    self.masa_g += 40

        maquina = PulsoExcesivo()
        estados = []
        with self.assertRaisesRegex(ValueError, "Sobredosis"):
            self.preparar(maquina, RECETAS["vainilla"], estados)
        self.assertEqual(estados[-1], Estado.FALLA)
        self.assertNotIn(Estado.MOVER_A_ENTREGA, estados)
