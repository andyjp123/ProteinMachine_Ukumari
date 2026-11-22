import argparse
import sys

from .control import Controlador, ParametrosCiclo
from .recetas import RECETAS, Estacion
from .simulacion import MaquinaSimulada


def main() -> int:
    parser = argparse.ArgumentParser(description="Simulador de la dosificadora")
    parser.add_argument("--sabor", choices=RECETAS)
    fallas = parser.add_mutually_exclusive_group()
    fallas.add_argument("--sin-recipiente", action="store_true")
    fallas.add_argument("--fallo-estacion", action="store_true")
    args = parser.parse_args()

    sabor = args.sabor
    while sabor not in RECETAS:
        try:
            sabor = input("Selecciona un sabor (vainilla/chocolate): ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            return 1
        if sabor not in RECETAS:
            print("Selecciona uno de los sabores disponibles.")

    receta = RECETAS[sabor]
    estacion_averiada: Estacion | None = (
        receta.estacion_polvo if args.fallo_estacion else None
    )
    maquina = MaquinaSimulada(not args.sin_recipiente, estacion_averiada)
    controlador = Controlador(maquina, maquina, maquina, maquina, ParametrosCiclo())
    try:
        resultado = controlador.preparar(receta, lambda estado: print(estado.value))
    except (TimeoutError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"{receta.sabor} · Agua {resultado.agua_g:.1f} g · Polvo {resultado.polvo_g:.1f} g")
    return 0
