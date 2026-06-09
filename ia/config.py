"""
=========================================================================
OBJETIVO:
Configuracion central del modulo de IA de GARRA-OS. Aqui viven TODAS las
constantes que comparten los demas scripts: el broker MQTT, los topicos
de comando, la fuente de video, los umbrales de cada modelo y la base de
datos de rostros. Tener un solo archivo de configuracion evita repetir
valores y permite cambiar el sistema completo desde un solo lugar
(por ejemplo, pasar de la webcam a la ESP32-CAM con UNA sola linea).

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
MATERIA : Sistemas Programables - Integracion de IA en el Ecosistema IoT
=========================================================================
"""

import os

# -------------------------------------------------------------------------
# 0) RUTAS DEL PROYECTO
# -------------------------------------------------------------------------
# Este archivo vive en GARRA-OS-IA/ia/. La RAIZ del proyecto es la carpeta
# de arriba (GARRA-OS-IA/). Calculamos rutas ABSOLUTAS desde ahi para que
# las carpetas dataset/, modelo/, test_images/ y credenciales/ se
# encuentren SIN IMPORTAR desde donde ejecutes los scripts.
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# -------------------------------------------------------------------------
# 1) FUENTE DE VIDEO
# -------------------------------------------------------------------------
# Aqui decidimos de donde sacamos los fotogramas. Mientras no tengamos la
# ESP32-CAM lista, usamos la webcam de la laptop. Cuando la camara este
# lista, solo se cambia FUENTE_VIDEO a "esp32cam" y se pone la URL del
# stream MJPEG. El resto del codigo NO cambia (esa es la idea).
FUENTE_VIDEO = "webcam"          # "webcam"  o  "esp32cam"

# Indice de la webcam de la laptop (0 = camara integrada por defecto).
WEBCAM_INDEX = 0

# URL del stream MJPEG de la ESP32-CAM (firmware CameraWebServer).
# Solo se usa si FUENTE_VIDEO == "esp32cam".
ESP32CAM_URL = "http://192.168.1.50:81/stream"

# Resolucion de captura. Bajarla reduce la latencia del pipeline.
ANCHO_FRAME = 640
ALTO_FRAME  = 480


# -------------------------------------------------------------------------
# 2) MQTT (debe coincidir con el firmware de la ESP32 de la Unidad 4)
# -------------------------------------------------------------------------
BROKER  = "test.mosquitto.org"   # Broker publico, sin login.
PUERTO  = 1883                   # Puerto MQTT estandar (sin TLS).
ID_NODO = "01"                   # Mismo ID que usa la ESP32.

# Topicos de COMANDO. Son EXACTAMENTE los que la ESP32 de GARRA-OS ya
# escucha desde la unidad pasada, asi que el servidor de IA puede mandar
# ordenes sin reflashear nada en el robot.
TOP_CMD_OLED   = f"garra/comando/oled/{ID_NODO}"     # "feliz" / "alerta" / "neutro"
TOP_CMD_SERVO  = f"garra/comando/servo/{ID_NODO}"    # 0-180 grados
TOP_CMD_BUZZER = f"garra/comando/buzzer/{ID_NODO}"   # JSON {"frecuencia":..,"duracion":..}
TOP_CMD_PARO   = f"garra/comando/paro/{ID_NODO}"     # paro de emergencia

# Topico NUEVO opcional: rutina completa de bienvenida (saludo coreografiado).
# Si flasheas el archivo esp32/rutina_saludo.py, la ESP32 lo entiende.
# Si NO, el servidor igual manda OLED+servo+buzzer por separado (ver abajo).
TOP_CMD_SALUDO = f"garra/comando/saludo/{ID_NODO}"   # texto: el nombre detectado

# Topico de telemetria que el servidor publica para dejar evidencia de
# lo que la IA "decidio" (util para el dashboard de la Unidad 3).
TOP_EVENTO_IA  = f"garra/ia/evento/{ID_NODO}"        # JSON con el resultado


# -------------------------------------------------------------------------
# 3) ETAPA 1 - GESTO (MediaPipe Hands)
# -------------------------------------------------------------------------
# Cuantos dedos extendidos consideramos "palma abierta" (gesto de saludo).
DEDOS_PARA_PALMA = 4

# Cuantos fotogramas seguidos hay que ver la palma abierta para confirmar
# el gesto. Sube este numero si hay falsos disparos por ruido.
FRAMES_CONFIRMAR_GESTO = 5

# Confianza minima de deteccion/seguimiento de MediaPipe (0.0 - 1.0).
MP_MIN_DETECCION  = 0.6
MP_MIN_SEGUIMIENTO = 0.6


# -------------------------------------------------------------------------
# 4) ETAPA 2 - ROSTRO (OpenCV LBPH)
# -------------------------------------------------------------------------
# Carpeta con las imagenes de entrenamiento, organizadas asi:
#   dataset/Estefania/*.jpg
#   dataset/Emilio/*.jpg
#   dataset/Ivan/*.jpg
#   dataset/Patrick/*.jpg
CARPETA_DATASET = os.path.join(RAIZ, "dataset")

# Archivos que genera el script de entrenamiento.
ARCHIVO_MODELO    = os.path.join(RAIZ, "modelo", "modelo_lbph.yml")
ARCHIVO_ETIQUETAS = os.path.join(RAIZ, "modelo", "etiquetas.json")

# Tamano al que normalizamos cada rostro antes de entrenar/predecir.
TAM_ROSTRO = (200, 200)

# UMBRAL de LBPH. OJO: en LBPH la "confianza" es una DISTANCIA, asi que
# MENOR es MEJOR. Si la distancia es menor que este umbral, lo aceptamos
# como match; si es mayor, lo tratamos como "Desconocido".
# Valor tipico util: 70. Subelo si rechaza a gente conocida; bajalo si
# acepta a desconocidos.
UMBRAL_LBPH = 70.0

# Clasificador Haar para DETECTAR rostros (viene incluido con OpenCV).
HAAR_CASCADE = "haarcascade_frontalface_default.xml"

# Carpeta con imagenes estaticas para probar el gesto (palma_*.jpg /
# nopalma_*.jpg). La usa prueba_estatica.py.
CARPETA_TEST_IMAGES = os.path.join(RAIZ, "test_images")


# -------------------------------------------------------------------------
# 5) ETAPA 3 - VOZ (gTTS) y ANTI-SPAM
# -------------------------------------------------------------------------
# Frase que se sintetiza. {nombre} se reemplaza por la persona reconocida.
FRASE_SALUDO = "Hola {nombre}, bienvenido al laboratorio"

# Idioma de gTTS ("es" = espanol).
IDIOMA_TTS = "es"

# Tiempo (segundos) que debe pasar para volver a saludar a la MISMA
# persona. Evita que el robot salude 30 veces por segundo.
COOLDOWN_SALUDO = 12.0

# Carpeta donde se guardan los MP3 generados por gTTS (cache).
CARPETA_AUDIO = os.path.join(RAIZ, "audio_cache")


# -------------------------------------------------------------------------
# 6) FIREBASE (la MISMA base de la Unidad 3 de GARRA-OS)
# -------------------------------------------------------------------------
# Si lo pones en True, cada reconocimiento se escribe en tu Realtime
# Database y se ve en el dashboard / en la consola de Firebase.
# Si lo dejas en False, el sistema funciona igual pero sin tocar Firebase.
USAR_FIREBASE = True

# Archivo de credenciales del servidor (la "clave privada" que descargaste
# en la Unidad 3 desde: Configuracion del proyecto -> Cuentas de servicio).
# VA EN la carpeta credenciales/ (al lado de las carpetas dataset/ y ia/).
FIREBASE_CRED = os.path.join(RAIZ, "credenciales", "firebase_credentials.json")

# URL de tu Realtime Database (la misma de la Unidad 3).
FIREBASE_URL = "https://garra-os-default-rtdb.firebaseio.com/"

# Nodo donde se guarda el reconocimiento dentro de la base. Se usa la
# raiz (igual que /telemetria, /alertas, /comandos de tu dashboard) para
# que la tarjeta del dashboard lo lea facil.
#   /reconocimiento/ultimo     -> el ultimo rostro reconocido
#   /reconocimiento/historial  -> log de todos los saludos
FIREBASE_NODO = "reconocimiento"
