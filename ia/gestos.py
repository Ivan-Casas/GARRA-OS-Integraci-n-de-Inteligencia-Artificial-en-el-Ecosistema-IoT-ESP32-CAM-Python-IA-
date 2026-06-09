"""
=========================================================================
OBJETIVO:
Etapa 1 del pipeline de IA de GARRA-OS. Encapsula la deteccion del gesto
de SALUDO (palma abierta) usando MediaPipe Hands.

QUE PREDICE / TIPO DE MODELO:
MediaPipe Hands es un modelo pre-entrenado por Google que regresa 21
puntos clave (landmarks) de la mano. Aqui NO entrenamos nada: usamos
esos 21 puntos para calcular cuantos dedos estan extendidos. Si hay
suficientes dedos extendidos, lo clasificamos como "palma abierta".
   - Tipo de prediccion : deteccion de landmarks + regla geometrica.
   - Precision aproximada: la deteccion de la mano de MediaPipe ronda
     el ~90-95% en buena luz; la clasificacion palma/no-palma con
     nuestra regla de dedos es muy estable (>95%) si la mano se ve de
     frente y completa.

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

# OpenCV lo usamos solo para convertir el espacio de color (MediaPipe
# espera RGB y OpenCV entrega BGR).
import cv2

# MediaPipe es la libreria de IA de Google para vision en tiempo real.
# Instalacion: pip install mediapipe
import mediapipe as mp

# Importamos los umbrales desde la configuracion central.
import config


class DetectorGestos:
    """
    Detecta si en el fotograma hay una PALMA ABIERTA (gesto de saludo).

    Uso:
        detector = DetectorGestos()
        hay_saludo, frame_anotado = detector.hay_palma_abierta(frame)
    """

    def __init__(self):
        # Modulo de manos de MediaPipe.
        self.mp_manos = mp.solutions.hands
        # Utilidad para dibujar los landmarks sobre el frame (debug visual).
        self.mp_dibujo = mp.solutions.drawing_utils

        # Creamos el objeto Hands. max_num_hands=1 porque solo nos
        # interesa una mano saludando; asi va mas rapido.
        self.manos = self.mp_manos.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=config.MP_MIN_DETECCION,
            min_tracking_confidence=config.MP_MIN_SEGUIMIENTO,
        )

        # Indices de las PUNTAS de cada dedo segun MediaPipe:
        #   8 = indice, 12 = medio, 16 = anular, 20 = menique.
        # (El pulgar se evalua aparte porque se mueve en horizontal.)
        self.PUNTAS = [8, 12, 16, 20]

    def _contar_dedos(self, landmarks, ancho, alto):
        """
        Cuenta cuantos dedos estan extendidos a partir de los 21 landmarks.
        Regla: un dedo (no pulgar) esta extendido si su PUNTA esta mas
        arriba (menor coordenada Y) que su articulacion media (PIP).
        """
        # Convertimos los landmarks normalizados (0-1) a pixeles.
        puntos = [(int(p.x * ancho), int(p.y * alto)) for p in landmarks.landmark]

        dedos_extendidos = 0

        # --- Dedos indice, medio, anular, menique ---
        for punta in self.PUNTAS:
            # La articulacion PIP esta 2 indices antes de la punta.
            pip = punta - 2
            # En coordenadas de imagen, "arriba" = Y mas pequena.
            if puntos[punta][1] < puntos[pip][1]:
                dedos_extendidos += 1

        # --- Pulgar (se mueve en horizontal, comparamos X) ---
        # Punta del pulgar = 4, articulacion = 3. Esta extendido si la
        # punta esta mas a la izquierda o derecha que la articulacion
        # (lo evaluamos en valor absoluto para que sirva con ambas manos).
        if abs(puntos[4][0] - puntos[3][0]) > 20:
            dedos_extendidos += 1

        return dedos_extendidos

    def hay_palma_abierta(self, frame):
        """
        Recibe un fotograma BGR (de OpenCV) y regresa:
           (bool palma_abierta, frame con landmarks dibujados)
        """
        alto, ancho = frame.shape[:2]

        # MediaPipe trabaja en RGB.
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        resultado = self.manos.process(frame_rgb)

        palma_abierta = False

        # Si MediaPipe encontro una mano:
        if resultado.multi_hand_landmarks:
            for mano in resultado.multi_hand_landmarks:
                # Dibujamos los puntos sobre el frame (evidencia visual).
                self.mp_dibujo.draw_landmarks(
                    frame, mano, self.mp_manos.HAND_CONNECTIONS
                )
                # Contamos dedos y decidimos si es palma abierta.
                n = self._contar_dedos(mano, ancho, alto)
                if n >= config.DEDOS_PARA_PALMA:
                    palma_abierta = True

        return palma_abierta, frame

    def cerrar(self):
        """Libera los recursos de MediaPipe."""
        self.manos.close()
