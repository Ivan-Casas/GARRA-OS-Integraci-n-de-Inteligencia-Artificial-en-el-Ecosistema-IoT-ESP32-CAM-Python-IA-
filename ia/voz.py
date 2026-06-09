"""
=========================================================================
OBJETIVO:
Etapa 3 (salida) del pipeline de IA de GARRA-OS. Encapsula la generacion
de lenguaje natural hablado con gTTS (Google Text-to-Speech): cuando hay
un MATCH positivo de rostro, sintetiza y reproduce el saludo personalizado
"Hola [Nombre], bienvenido al laboratorio".

DETALLE TECNICO IMPORTANTE:
gTTS necesita INTERNET (le pide el audio a Google) y devuelve un MP3.
Para que la sintesis NO congele el bucle de video, la reproduccion se
hace en un HILO aparte. Ademas, los MP3 ya generados se CACHEAN: si ya
saludamos a "Ivan" una vez, no le volvemos a pedir el audio a Google.

Para reproducir el MP3 se usa pygame (mas confiable que playsound en
Windows con Python nuevo). Si pygame no esta disponible, se intenta
playsound; si tampoco, el sistema NO truena: solo imprime el saludo.

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

# gTTS: Google Text-to-Speech. Instalacion: pip install gTTS
from gtts import gTTS

# os para manejar rutas de los MP3 cacheados.
import os

# threading para reproducir el audio sin bloquear el video.
import threading

# Configuracion central (frase, idioma).
import config


# -------------------------------------------------------------------------
# Elegimos el reproductor de audio disponible, en orden de fiabilidad.
#   1) pygame   (recomendado; pip install pygame)
#   2) playsound (alternativa)
#   3) ninguno  -> solo se imprime el saludo, sin audio
# -------------------------------------------------------------------------
_BACKEND = None
try:
    import pygame
    pygame.mixer.init()
    _BACKEND = "pygame"
except Exception:
    try:
        from playsound import playsound
        _BACKEND = "playsound"
    except Exception:
        _BACKEND = None


class Voz:
    """
    Sintetiza y reproduce saludos personalizados.

    Uso:
        voz = Voz()
        voz.saludar("Estefania")   # no bloquea: reproduce en otro hilo
    """

    def __init__(self):
        # Carpeta donde guardamos los MP3 ya generados (cache).
        self.carpeta_cache = config.CARPETA_AUDIO
        os.makedirs(self.carpeta_cache, exist_ok=True)

    def _generar_mp3(self, nombre):
        """
        Crea (si no existe) el MP3 del saludo para 'nombre' y regresa su
        ruta. Usa cache para no llamar a Google cada vez.
        """
        ruta = os.path.join(self.carpeta_cache, f"saludo_{nombre}.mp3")

        if not os.path.exists(ruta):
            frase = config.FRASE_SALUDO.format(nombre=nombre)
            # gTTS pide el audio a Google y lo guarda como MP3.
            tts = gTTS(text=frase, lang=config.IDIOMA_TTS)
            tts.save(ruta)

        return ruta

    def _reproducir(self, ruta):
        """Reproduce el MP3 (corre dentro de un hilo)."""
        if _BACKEND == "pygame":
            try:
                import pygame
                pygame.mixer.music.load(ruta)
                pygame.mixer.music.play()
                # Esperamos a que termine para liberar el archivo.
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
            except Exception as e:
                print("[VOZ] No se pudo reproducir (pygame):", e)
        elif _BACKEND == "playsound":
            try:
                from playsound import playsound
                playsound(ruta)
            except Exception as e:
                print("[VOZ] No se pudo reproducir (playsound):", e)
        else:
            print("[VOZ] (sin reproductor de audio; instala pygame para oir el saludo)")

    def saludar(self, nombre):
        """
        Genera (o reutiliza) el saludo y lo reproduce en un hilo aparte
        para no congelar el video.
        """
        frase = config.FRASE_SALUDO.format(nombre=nombre)
        print(f"[VOZ] {frase}")

        try:
            ruta = self._generar_mp3(nombre)
        except Exception as e:
            # Si falla gTTS (p.ej. sin internet), avisamos y seguimos.
            print("[VOZ] Error al generar el audio con gTTS:", e)
            return

        # Lanzamos la reproduccion en segundo plano.
        hilo = threading.Thread(target=self._reproducir, args=(ruta,), daemon=True)
        hilo.start()
