"""
=========================================================================
OBJETIVO:
Fuente de video de GARRA-OS con tecnica ANTI-LATENCIA ("skip-frames").

Cuando la imagen llega por red (stream MJPEG de la ESP32-CAM), los cuadros
se acumulan en un buffer y el modelo de OpenCV terminaba procesando
fotogramas VIEJOS (desactualizados). Para evitarlo:

  1) Se fija el buffer de captura en 1 (CAP_PROP_BUFFERSIZE).
  2) Un hilo lee la camara SIN PARAR y guarda SOLO el ultimo fotograma.
  3) El bucle principal pide leer() y siempre recibe el cuadro MAS RECIENTE,
     descartando los atrasados. Eso es el "skip-frames".

Asi funciona igual con la webcam (FUENTE_VIDEO="webcam") que con la
ESP32-CAM real (FUENTE_VIDEO="esp32cam"), sin cambiar el resto del codigo.

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

import cv2
import threading
import config


class FuenteVideo:
    """
    Fuente de video con skip-frames. Uso:
        cam = FuenteVideo()
        if not cam.abierta(): ...
        ok, frame = cam.leer()
        ...
        cam.liberar()
    """

    def __init__(self):
        # Abrimos webcam o stream de la ESP32-CAM segun la configuracion.
        if config.FUENTE_VIDEO == "esp32cam":
            print(f"[VIDEO] Stream ESP32-CAM: {config.ESP32CAM_URL}")
            self.cap = cv2.VideoCapture(config.ESP32CAM_URL)
        else:
            print(f"[VIDEO] Webcam (indice {config.WEBCAM_INDEX})")
            self.cap = cv2.VideoCapture(config.WEBCAM_INDEX)

        # Bajamos la resolucion: menos datos = menos latencia.
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.ANCHO_FRAME)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.ALTO_FRAME)
        # Buffer de 1: que la captura no acumule cuadros viejos.
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        self._frame = None              # ultimo fotograma disponible
        self._corriendo = True
        self._lock = threading.Lock()   # protege el acceso al frame

        # Hilo que lee sin parar y se queda SOLO con el cuadro mas reciente.
        self._hilo = threading.Thread(target=self._actualizar, daemon=True)
        self._hilo.start()

    def abierta(self):
        """True si la camara/stream se abrio correctamente."""
        return self.cap.isOpened()

    def _actualizar(self):
        """Bucle del hilo lector: descarta lo viejo, guarda lo nuevo."""
        while self._corriendo:
            ok, frame = self.cap.read()
            if not ok:
                continue
            with self._lock:
                self._frame = frame      # pisamos el anterior (skip-frames)

    def leer(self):
        """Devuelve (True, fotograma_mas_reciente) o (False, None)."""
        with self._lock:
            if self._frame is None:
                return False, None
            return True, self._frame.copy()

    def liberar(self):
        """Detiene el hilo y libera la camara."""
        self._corriendo = False
        self._hilo.join(timeout=1.0)
        self.cap.release()
