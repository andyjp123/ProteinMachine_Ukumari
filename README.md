# ProteinMachine_Ukumari

Proyecto de graduación para el título de Ingeniero Generalista.

Prototipo en Python para programar y probar el ciclo de la máquina expendedora de bebidas proteicas. Requiere Python 3.10 o posterior y usa la biblioteca estándar.

## Ejecutar el simulador

Desde la carpeta del repositorio (en Windows también se puede usar `py` en lugar de `python`):

```sh
python -m dosificadora
python -m dosificadora --sabor chocolate
python -m dosificadora --sabor chocolate --sin-recipiente
python -m dosificadora --sabor chocolate --fallo-estacion
python -m unittest discover -s tests -v
```

## Flujo del primer ciclo

[Consultar el diagrama original](docs/Diagrama_flujo.png).

1. El usuario selecciona un sabor. El sistema confirma que el carro está en la estación de agua y espera la detección del recipiente con el sensor infrarrojo.
2. Sirve el agua y comprueba por ganancia de masa que se alcanzó la dosis.
3. Mueve el carro con el motor DC hacia la estación de polvo elegida. El carro debe estar detenido y su posición confirmada para habilitar la dosificación.
4. Dosifica polvo por pulsos, con una referencia de masa tomada en la estación de polvo. Cada pulso termina con las salidas apagadas y se comprueba la ganancia de masa antes de continuar.
5. Mueve el carro a entrega, confirma su llegada y muestra el resultado. Ante un error, el controlador solicita desactivar la dosificación y detener el carro.

La simulación empieza con el carro en agua y termina tras un pedido. Vainilla, chocolate, 250 g de agua y 25 g de polvo son valores de prueba. Los plazos, tolerancias y tamaños de pulso del simulador requieren validación en banco. El programa usa una interfaz de terminal y un dispositivo simulado. Para la máquina física quedan pendientes la pantalla, el botón de encendido y apagado, los adaptadores de hardware y la secuencia de retirar el recipiente y devolver el carro para el siguiente pedido.

## División del código

| Responsable propuesto | Archivos | Función |
|---|---|---|
| Interfaz e integración | `interfaz.py`, `control.py`, `recetas.py` | Selección de sabor, estados del ciclo y objetivos de masa. |
| Carro y sensores | `carro.py`, `sensores.py` | Entrada infrarroja del recipiente, sensores de estación y accionamiento del motor DC. |
| Dosificación | `dosificacion.py` | Pulsos del sistema de agua, tornillo y agitador, con corte por masa y tiempo máximo. |
| Pesaje | `pesaje.py` | Interfaz para lecturas estables en gramos. El adaptador real se encargará de calibración, estabilidad y lectura del HX711. |
| Pruebas compartidas | `simulacion.py`, `tests/` | Simulación de los equipos, pedido completo y fallas reproducibles. |

Los contratos de hardware reciben plazos en segundos. Cada adaptador real debe respetarlos y confirmar la finalización de sus operaciones. Antes de conectarlos, acuerden la posición inicial y de entrega, el mapa de entradas y salidas, los actuadores a cargo de cada placa y la reacción ante una pérdida de comunicación. Al incorporar una interfaz gráfica, el ciclo debe ejecutarse fuera del hilo de la pantalla.

## Colaboración

Para cada cambio, creen una rama a partir de `main`, por ejemplo `feat/carro`. Ejecuten las pruebas locales y abran un pull request para que otro integrante revise el código y los cambios en los contratos compartidos.
