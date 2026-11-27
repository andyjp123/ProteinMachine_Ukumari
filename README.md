# ProteinMachine_Ukumari

Proyecto de graduación para el título de Ingeniero Generalista. Requiere Python 3.10 o posterior.

## Abrir la interfaz UKUMARI

Desde la carpeta del repositorio, instala pyserial y ejecuta el panel:

```sh
python -m pip install pyserial
python -m dosificadora --gui
```

En Raspberry Pi OS, instala Tkinter con `sudo apt install python3-tk` si tu instalación de Python no lo incluye. Usa un entorno virtual para instalar pyserial. En Windows puedes usar `py` en lugar de `python`. Si colocas el archivo `logo.png` en tu carpeta de usuario, el panel lo muestra en el encabezado.

La ventana de 800×480 abre en la vista Usuario sin conectarse al Arduino. Para operar la máquina, entra en **Admin** (PIN original `123`), selecciona el puerto y pulsa **Conectar**. La comunicación usa 115200 baudios y envía `INVERT` después de la espera de arranque del Arduino. Si la conexión se pierde, el panel reintenta en el puerto seleccionado. **Desconectar** cancela los reintentos.

Los botones de proteína envían `RUN 4`, `RUN 3` o `RUN 2`. El firmware ejecuta la secuencia con agua en la estación 5, entrega en la 1 y retorno configurable a la 5. En Admin, **Probar Agua (6s)** envía `PUMP` una vez. El intervalo es responsabilidad del firmware. El panel refleja los mensajes recibidos y las lecturas IR de `SENS:` (estaciones 1 a 5 en el mensaje, 5 a 1 en pantalla).

## Ejecutar el simulador

El simulador de terminal utiliza solo la biblioteca estándar. Ambos modos también se pueden iniciar desde el editor ejecutando directamente `dosificadora/__main__.py` con los argumentos correspondientes.

```sh
python -m dosificadora
python -m dosificadora --sabor chocolate
python dosificadora/__main__.py --sabor chocolate
python -m dosificadora --sabor chocolate --sin-recipiente
python -m dosificadora --sabor chocolate --fallo-estacion
python -m unittest discover -s tests -v
```

El ciclo simulado se basa en el [diagrama de flujo](docs/Diagrama_flujo.png). Empieza con el carro en la estación de agua y termina tras un pedido. Vainilla, chocolate, 250 g de agua y 25 g de polvo son valores de prueba. El simulador incluye detección de recipiente y dosificación por ganancia de masa. La interfaz Tkinter delega la operación al Arduino mediante el protocolo de la máquina.

## División del código

| Responsable propuesto | Archivos en `dosificadora/` | Función |
|---|---|---|
| Interfaz e integración | `interfaz_tk.py`, `interfaz.py` | Panel de Usuario y Admin, estados en pantalla y selección del modo al iniciar. |
| Comunicación Arduino | `conexion_serial.py` | Puertos, conexión, reconexión e intercambio de líneas. |
| Carro y sensores IR | `carro.py`, `sensores.py` | Comandos del carro, sensores IR de las estaciones y contratos de la simulación. |
| Bomba | `sistema_agua.py` | Prueba manual e interpretación de los mensajes de la bomba. |
| Ciclo simulado | `control.py`, `recetas.py`, `dosificacion.py`, `pesaje.py`, `simulacion.py` | Secuencia simulada, recetas, dosificación por pulsos, pesaje y fallas reproducibles. |

## Colaboración

Para cada cambio, creen una rama a partir de `main`, por ejemplo `feat/carro`. Ejecuten las pruebas locales y abran un pull request para que otro integrante revise el código y los cambios en los contratos compartidos.
