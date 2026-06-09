"""
=========================================================================
OBJETIVO:
Servidor de IA (el "cerebro") de GARRA-OS. Implementa el PIPELINE COMPLETO
en tiempo real de toma de decisiones inteligente:

   Camara (webcam / ESP32-CAM)
        |
        v  ETAPA 1: MediaPipe detecta PALMA ABIERTA (gesto de saludo)
        |           -> el gesto ARMA el sistema
        v  ETAPA 2: OpenCV LBPH reconoce el ROSTRO contra la BD local
        |           -> valida quien es la persona
        v  ETAPA 3 (si hay MATCH):
        |     - gTTS sintetiza "Hola [Nombre], bienvenido al laboratorio"
        |     - MQTT publica los comandos hacia los ACTUADORES de la ESP32
        v
   ESP32 (GARRA-OS): OLED cara feliz + servo saluda + buzzer beep

Cumple el flujo exigido: Camara -> MQTT(salida) -> Servidor IA -> MQTT -> Actuador.
La webcam de la laptop hace de ESP32-CAM por ahora; para usar la camara
real solo se cambia FUENTE_VIDEO en config.py.

DOCUMENTACION DEL MODELO (resumen):
   - MediaPipe Hands : deteccion de 21 landmarks (modelo pre-entrenado de
                       Google) + regla de dedos para clasificar "palma".
   - OpenCV LBPH     : clasificador supervisado de rostros; predice la
                       etiqueta (nombre) + una distancia (menor = mejor).
                       Precision real medida por prueba_estatica.py.
   - gTTS            : sintesis de voz (genera el saludo hablado).

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

import cv2
import time
import config

# Modulos propios (cada uno es una etapa del pipeline).
from gestos import DetectorGestos
from reconocimiento import ReconocedorFacial
from voz import Voz
from comunicacion_mqtt import PuenteActuadores
from firebase_ia import FirebaseIA
from camara import FuenteVideo


def main():
    print("=" * 70)
    print("GARRA-OS | Servidor de IA (pipeline gesto -> rostro -> voz/MQTT)")
    print("=" * 70)

    # ---- Inicializamos las 4 etapas ----
    gestos = DetectorGestos()
    rostros = ReconocedorFacial()
    rostros.cargar_modelo()      # carga el LBPH entrenado
    voz = Voz()
    puente = PuenteActuadores()
    puente.conectar()
    firebase = FirebaseIA()      # escribe el reconocimiento en Firebase
    time.sleep(1)                # damos un segundo a la conexion MQTT

    cap = FuenteVideo()          # camara con skip-frames (anti-latencia)
    if not cap.abierta():
        print("[X] No se pudo abrir la fuente de video.")
        return

    # ---- Variables de control del pipeline ----
    frames_palma = 0             # cuadros seguidos con palma abierta
    gesto_confirmado = False     # ya se confirmo el gesto de saludo
    ultimo_saludo = {}           # nombre -> timestamp del ultimo saludo

    print("[INFO] Sistema activo. Muestra la PALMA ABIERTA para saludar.")
    print("[INFO] Presiona 'q' en la ventana de video para salir.\n")

    try:
        while True:
            # leer() entrega SIEMPRE el fotograma mas reciente (skip-frames),
            # asi el modelo nunca procesa cuadros atrasados.
            ok, frame = cap.leer()
            if not ok:
                time.sleep(0.03)     # aun no llega el primer cuadro
                continue

            # Espejo horizontal: se siente mas natural (como un espejo).
            frame = cv2.flip(frame, 1)

            # ---------------------------------------------------------
            # ETAPA 1: detectar gesto de palma abierta
            # ---------------------------------------------------------
            palma, frame = gestos.hay_palma_abierta(frame)

            if palma:
                frames_palma += 1
                if frames_palma >= config.FRAMES_CONFIRMAR_GESTO:
                    gesto_confirmado = True
            else:
                frames_palma = 0
                gesto_confirmado = False

            estado = "Esperando palma abierta..."
            color = (0, 200, 255)

            # ---------------------------------------------------------
            # ETAPA 2: si el gesto esta confirmado, reconocer rostro
            # ---------------------------------------------------------
            if gesto_confirmado:
                estado = "Palma OK -> buscando rostro..."
                color = (0, 255, 255)

                nombre, distancia, caja = rostros.reconocer(frame)

                if caja is not None:
                    x, y, w, h = caja
                    etiqueta = (f"{nombre} ({distancia:.0f})"
                                if distancia is not None else nombre)
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, etiqueta, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                    # -------------------------------------------------
                    # ETAPA 3: match positivo -> voz + MQTT (con cooldown)
                    # -------------------------------------------------
                    if nombre != "Desconocido":
                        ahora = time.time()
                        if ahora - ultimo_saludo.get(nombre, 0) > config.COOLDOWN_SALUDO:
                            ultimo_saludo[nombre] = ahora
                            print(f"[PIPELINE] MATCH: {nombre} "
                                  f"(dist={distancia:.1f}) -> saludo + actuadores")
                            voz.saludar(nombre)               # gTTS (hilo)
                            puente.rutina_bienvenida(nombre)  # MQTT (hilo)
                            firebase.registrar(nombre, distancia)  # -> Firebase
                        estado = f"Bienvenido, {nombre}!"
                        color = (0, 255, 0)
                    else:
                        estado = "Rostro NO reconocido"
                        color = (0, 0, 255)

            # ---- Overlay de estado en pantalla ----
            cv2.rectangle(frame, (0, 0), (frame.shape[1], 40), (30, 30, 30), -1)
            cv2.putText(frame, estado, (10, 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

            cv2.imshow("GARRA-OS | Vision IA", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\n[INFO] Detenido por el usuario.")

    finally:
        # Apagado ordenado: liberar camara, ventanas, MediaPipe y dejar
        # el robot en estado neutro.
        cap.liberar()
        cv2.destroyAllWindows()
        gestos.cerrar()
        puente.desconectar()
        print("[INFO] Sistema apagado correctamente.")


if __name__ == "__main__":
    main()
