# =========================================================================
# OBJETIVO:
# (OPCIONAL) Handler MicroPython para la ESP32 de GARRA-OS que escucha el
# topico NUEVO de saludo (garra/comando/saludo/01) y ejecuta una rutina de
# bienvenida mas vistosa: muestra el NOMBRE de la persona en la OLED, hace
# que el servo del cuello "salude" y suena el buzzer.
#
# NO es obligatorio: el servidor de IA ya manda OLED+servo+buzzer por los
# topicos que tu firmware de la Unidad 4 YA entiende. Este archivo solo
# agrega el extra de mostrar el nombre. Integra esta funcion dentro del
# callback MQTT de tu Comunicaciones.py si quieres usarla.
#
# INTEGRANTES:
#   - Alcala Ramos Luz Estefania        [Codigo: 23240079]
#   - Bahena Mora Emilio Salvador       [Codigo: 23240009]
#   - Casas Bastidas Jose Ivan          [Codigo: 23240883]
#   - Fischer Gonzalez Patrick          [Codigo: 23240045]
#
# PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
# DOCENTE : Ma. Veronica Tapia Ibarra
# =========================================================================

import time


def rutina_saludo(actuadores, nombre):
    """
    Ejecuta la bienvenida en el hardware.
    'actuadores' es la instancia de ActuatorBox (la HAL de la Unidad 4),
    asi respetamos el encapsulamiento: este archivo NO toca pines.

    'nombre' es el texto recibido por MQTT (la persona reconocida por la IA).
    """
    # 1) Cara feliz.
    actuadores.mostrar_emocion("feliz")

    # 2) Mostrar el nombre en la OLED (si tu HAL tiene mostrar_texto;
    #    si no, puedes adaptarlo a tu metodo de dibujo de texto).
    try:
        actuadores.mostrar_texto("Hola " + nombre + "!")
    except AttributeError:
        # Si la HAL no tiene mostrar_texto, simplemente lo ignoramos.
        pass

    # 3) Beep de bienvenida.
    actuadores.emitir_sonido(988, 0.15)

    # 4) El cuello saluda: vaiven del servo.
    for _ in range(2):
        actuadores.mover_cuello(130)
        time.sleep(0.35)
        actuadores.mover_cuello(50)
        time.sleep(0.35)
    actuadores.mover_cuello(90)


# -------------------------------------------------------------------------
# COMO INTEGRARLO en el callback MQTT de tu Comunicaciones.py:
#
#   from rutina_saludo import rutina_saludo
#
#   def _callback(topico, mensaje):
#       t = topico.decode()
#       m = mensaje.decode()
#       if t == b"garra/comando/saludo/01".decode():
#           rutina_saludo(self.actuadores, m)
#       # ... tus otros topicos (oled, servo, buzzer, paro) ...
#
# Y suscribete al topico nuevo al conectar:
#   self.cliente.subscribe(b"garra/comando/saludo/01")
# -------------------------------------------------------------------------
