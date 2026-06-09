"""
=========================================================================
OBJETIVO:
Cierre del pipeline de IA de GARRA-OS. Encapsula el cliente MQTT que el
servidor de IA usa para MANDAR COMANDOS a los actuadores fisicos de la
ESP32 cuando hay un saludo reconocido. Aqui es donde la "decision" de la
IA se convierte en una ACCION FISICA del robot:

   IA reconoce a la persona  ->  MQTT  ->  ESP32:
        - OLED  : muestra cara feliz
        - SERVO : hace el gesto de saludar con el cuello
        - BUZZER: emite un beep de bienvenida

Estos topicos son EXACTAMENTE los que el firmware de GARRA-OS (Unidad 4)
ya escucha, asi que no hay que reflashear la ESP32 para que reaccione.

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

# Cliente MQTT de Python. Instalacion: pip install paho-mqtt
import paho.mqtt.client as mqtt

# json para empaquetar el comando del buzzer y el evento de IA.
import json

# time para la pequena coreografia del servo (mover y regresar).
import time

# threading para que la coreografia del servo no bloquee el video.
import threading

# Configuracion central (broker, topicos).
import config


class PuenteActuadores:
    """
    Publica comandos MQTT hacia los actuadores de GARRA-OS.

    Uso:
        puente = PuenteActuadores()
        puente.conectar()
        puente.rutina_bienvenida("Estefania")
    """

    def __init__(self):
        self.client = mqtt.Client()
        self.conectado = False

    def conectar(self):
        """Conecta al broker MQTT publico."""
        self.client.on_connect = self._on_connect
        print(f"[MQTT] Conectando a {config.BROKER}:{config.PUERTO} ...")
        self.client.connect(config.BROKER, config.PUERTO, keepalive=60)
        # loop_start corre el cliente en su propio hilo (no bloquea).
        self.client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.conectado = True
            print(f"[MQTT] Conectado al broker {config.BROKER}")
        else:
            print(f"[MQTT] Fallo de conexion, codigo {rc}")

    # ---------------------------------------------------------------------
    # Comandos individuales a cada actuador (reutilizan los topicos de la
    # ESP32 que ya existen desde la Unidad 4).
    # ---------------------------------------------------------------------
    def cara_feliz(self):
        self.client.publish(config.TOP_CMD_OLED, "feliz")

    def cara_neutra(self):
        self.client.publish(config.TOP_CMD_OLED, "neutro")

    def mover_servo(self, grados):
        self.client.publish(config.TOP_CMD_SERVO, str(int(grados)))

    def beep(self, frecuencia=880, duracion=0.2):
        carga = json.dumps({"frecuencia": frecuencia, "duracion": duracion})
        self.client.publish(config.TOP_CMD_BUZZER, carga)

    # ---------------------------------------------------------------------
    # Rutina completa de bienvenida (lo que dispara la IA).
    # ---------------------------------------------------------------------
    def _coreografia(self, nombre):
        """
        Secuencia fisica del saludo. Corre en un hilo para no congelar el
        video mientras el servo se mueve.
        """
        # 1) Cara feliz en la OLED.
        self.cara_feliz()

        # 2) Beep corto de bienvenida.
        self.beep(frecuencia=988, duracion=0.15)

        # 3) El cuello "saluda": va y viene un par de veces.
        for _ in range(2):
            self.mover_servo(130)
            time.sleep(0.35)
            self.mover_servo(50)
            time.sleep(0.35)
        # Regresa al centro.
        self.mover_servo(90)

        # 4) Tambien publicamos el evento de IA (evidencia + dashboard).
        evento = json.dumps({"evento": "saludo", "persona": nombre})
        self.client.publish(config.TOP_EVENTO_IA, evento)

        # 5) Si flasheaste el handler opcional en la ESP32, le mandamos
        #    el nombre para que lo muestre en la OLED. Si no lo flasheaste,
        #    este publish simplemente es ignorado por la ESP32.
        self.client.publish(config.TOP_CMD_SALUDO, nombre)

    def rutina_bienvenida(self, nombre):
        """Lanza la coreografia de bienvenida sin bloquear el bucle."""
        hilo = threading.Thread(target=self._coreografia, args=(nombre,), daemon=True)
        hilo.start()

    def desconectar(self):
        """Deja al robot en estado neutro y cierra la conexion."""
        self.cara_neutra()
        time.sleep(0.2)
        self.client.loop_stop()
        self.client.disconnect()
