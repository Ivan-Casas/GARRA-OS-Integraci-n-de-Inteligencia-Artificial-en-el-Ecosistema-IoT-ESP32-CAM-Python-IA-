"""
=========================================================================
OBJETIVO:
Puente entre el servidor de IA de GARRA-OS y Firebase Realtime Database.
Cada vez que la IA reconoce a una persona, este modulo escribe el evento
en la MISMA base de datos de la Unidad 3, para que el reconocimiento
facial se vea en la consola de Firebase y en el dashboard de GARRA-OS.

QUE ESCRIBE:
   /garraos/01/reconocimiento/ultimo     -> set()  : el ultimo rostro
        { persona, confianza, hora_ts }
   /garraos/01/reconocimiento/historial  -> push() : un registro por saludo

Reutiliza el firebase_credentials.json (la clave privada del servidor) que
ya descargaste en la Unidad 3. Solo hay que copiarlo a esta carpeta.

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

import os
import config

# firebase-admin es el SDK de Firebase para servidores Python.
# Instalacion: pip install firebase-admin
# Lo importamos con try para que, si no esta instalado, el sistema NO
# truene: simplemente avisa y sigue trabajando sin Firebase.
try:
    import firebase_admin
    from firebase_admin import credentials, db
    _HAY_FIREBASE = True
except Exception:
    _HAY_FIREBASE = False


class FirebaseIA:
    """
    Escribe los reconocimientos en la Realtime Database de GARRA-OS.

    Uso:
        fb = FirebaseIA()
        fb.registrar("Ivan", 22.0)
    """

    def __init__(self):
        # activo = True solo si todo se inicializo bien.
        self.activo = False

        # Si el usuario apago Firebase en config, no hacemos nada.
        if not config.USAR_FIREBASE:
            print("[FB] Firebase desactivado en config (USAR_FIREBASE=False).")
            return

        # Si la libreria no esta instalada, avisamos y seguimos sin FB.
        if not _HAY_FIREBASE:
            print("[FB] firebase-admin no esta instalado; se omite Firebase.")
            print("[FB] Instala con: pip install firebase-admin")
            return

        # Si no encontramos el archivo de credenciales, avisamos.
        if not os.path.exists(config.FIREBASE_CRED):
            print(f"[FB] No se encontro '{config.FIREBASE_CRED}'.")
            print("[FB] Copia tu firebase_credentials.json (el de la Unidad 3) "
                  "a esta carpeta.")
            return

        # Inicializamos Firebase (solo si no se habia inicializado antes).
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(config.FIREBASE_CRED)
                firebase_admin.initialize_app(
                    cred, {"databaseURL": config.FIREBASE_URL}
                )
            self.activo = True
            print(f"[FB] Firebase conectado: {config.FIREBASE_URL}")
        except Exception as e:
            print("[FB] No se pudo inicializar Firebase:", e)

    def registrar(self, nombre, distancia):
        """
        Escribe en Firebase que se reconocio a 'nombre' con cierta
        'distancia' (confianza LBPH; menor = mejor). No bloquea el video
        de forma notable porque la escritura es pequena.
        """
        if not self.activo:
            return

        try:
            datos = {
                "persona": nombre,
                # Redondeamos la distancia LBPH a 1 decimal.
                "confianza": round(float(distancia), 1),
                # {".sv": "timestamp"} = "pon la hora del servidor de Firebase".
                "hora_ts": {".sv": "timestamp"},
            }

            base = config.FIREBASE_NODO

            # 1) Ultimo reconocimiento (se sobreescribe): facil de leer en
            #    el dashboard para mostrar "Ultima persona reconocida".
            db.reference(f"{base}/ultimo").set(datos)

            # 2) Historial (se agrega uno nuevo cada vez): log completo.
            db.reference(f"{base}/historial").push(datos)

            print(f"[FB] Reconocimiento escrito en Firebase: {nombre}")
        except Exception as e:
            print("[FB] Error al escribir en Firebase:", e)
