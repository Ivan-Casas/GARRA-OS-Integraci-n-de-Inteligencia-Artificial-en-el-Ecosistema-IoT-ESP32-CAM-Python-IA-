"""
=========================================================================
OBJETIVO:
Etapa 2 del pipeline de IA de GARRA-OS. Encapsula la DETECCION de rostros
(Haar Cascade) y el RECONOCIMIENTO facial (LBPH) usando OpenCV, validando
cada rostro contra la base de datos local de integrantes.

QUE PREDICE / TIPO DE MODELO:
   - Deteccion : Haar Cascade (clasificador en cascada de Viola-Jones)
                 dice DONDE hay un rostro en la imagen.
   - Reconocim.: LBPH (Local Binary Patterns Histograms) dice DE QUIEN
                 es ese rostro, comparandolo contra los rostros con que
                 fue entrenado. Regresa una etiqueta (nombre) y una
                 "confianza" que en realidad es una DISTANCIA: menor =
                 mas parecido. Por eso usamos un UMBRAL: si la distancia
                 es mayor que el umbral, el rostro es "Desconocido".
   - Precision aproximada: con ~30 imagenes por persona y pocas personas,
                 en luz controlada LBPH suele dar 85-95% de aciertos.
                 La precision REAL la mide prueba_estatica.py sobre tus
                 propias imagenes (no inventamos el numero).

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

# OpenCV. OJO: el reconocedor LBPH vive en el modulo cv2.face, que SOLO
# esta disponible si instalas 'opencv-contrib-python' (no el normal).
import cv2

# os para construir rutas y leer carpetas.
import os

# json para guardar/leer el mapa numero_etiqueta -> nombre.
import json

# Configuracion central.
import config


class ReconocedorFacial:
    """
    Detecta y reconoce rostros contra la base de datos local.

    Uso:
        rec = ReconocedorFacial()
        rec.cargar_modelo()                 # carga el .yml entrenado
        nombre, dist, caja = rec.reconocer(frame)
    """

    def __init__(self):
        # Cargamos el detector Haar que viene EMPAQUETADO con OpenCV.
        ruta_haar = os.path.join(cv2.data.haarcascades, config.HAAR_CASCADE)
        self.detector = cv2.CascadeClassifier(ruta_haar)

        # Creamos el reconocedor LBPH (necesita opencv-contrib-python).
        self.reconocedor = cv2.face.LBPHFaceRecognizer_create()

        # Diccionario {id_numerico: "Nombre"} que se llena al cargar.
        self.etiquetas = {}

        # Bandera para no intentar predecir sin modelo cargado.
        self.modelo_cargado = False

    def detectar_rostros(self, frame_gris):
        """
        Regresa una lista de cajas (x, y, w, h) de los rostros detectados.
        Trabaja sobre imagen en ESCALA DE GRISES (Haar lo requiere).
        """
        return self.detector.detectMultiScale(
            frame_gris,
            scaleFactor=1.1,   # cuanto se reduce la imagen en cada escala
            minNeighbors=5,    # cuantos vecinos confirman una deteccion
            minSize=(80, 80),  # ignora rostros muy pequenos (ruido)
        )

    def cargar_modelo(self):
        """Carga el modelo LBPH y el mapa de etiquetas desde disco."""
        if not os.path.exists(config.ARCHIVO_MODELO):
            raise FileNotFoundError(
                f"No existe {config.ARCHIVO_MODELO}. "
                f"Primero corre entrenar_rostros.py."
            )
        self.reconocedor.read(config.ARCHIVO_MODELO)

        with open(config.ARCHIVO_ETIQUETAS, "r", encoding="utf-8") as f:
            # Las claves del JSON son strings; las pasamos a int.
            crudo = json.load(f)
            self.etiquetas = {int(k): v for k, v in crudo.items()}

        self.modelo_cargado = True

    def reconocer(self, frame):
        """
        Recibe un frame BGR. Detecta el rostro mas grande, lo reconoce y
        regresa: (nombre, distancia, caja).
           - nombre   : "Estefania", "Ivan", ... o "Desconocido"
           - distancia: confianza LBPH (menor = mejor); None si no hay rostro
           - caja     : (x, y, w, h) o None
        """
        if not self.modelo_cargado:
            raise RuntimeError("Llama a cargar_modelo() antes de reconocer().")

        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = self.detectar_rostros(gris)

        if len(rostros) == 0:
            return None, None, None

        # Nos quedamos con el rostro MAS GRANDE (el mas cercano a la camara).
        x, y, w, h = max(rostros, key=lambda r: r[2] * r[3])

        # Recortamos y normalizamos el tamano, igual que en entrenamiento.
        rostro = gris[y:y + h, x:x + w]
        rostro = cv2.resize(rostro, config.TAM_ROSTRO)

        # Predecimos: LBPH regresa (id_etiqueta, distancia).
        id_etiqueta, distancia = self.reconocedor.predict(rostro)

        # Aplicamos el umbral: si la distancia es mayor, es Desconocido.
        if distancia <= config.UMBRAL_LBPH:
            nombre = self.etiquetas.get(id_etiqueta, "Desconocido")
        else:
            nombre = "Desconocido"

        return nombre, distancia, (x, y, w, h)
