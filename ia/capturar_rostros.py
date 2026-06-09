"""
=========================================================================
OBJETIVO:
Herramienta de apoyo para CONSTRUIR la base de datos local de rostros de
GARRA-OS. Abre la webcam, detecta tu rostro y guarda automaticamente N
recortes en dataset/<Nombre>/. Hay que correrlo UNA vez por cada
integrante (cambiando el nombre) antes de entrenar el modelo.

USO:
   python capturar_rostros.py Estefania
   python capturar_rostros.py Ivan
   ... (uno por integrante)

CONSEJO: captura en distintas poses y con distinta luz para que el
reconocimiento sea mas robusto.

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
import os
import sys
import config

# Cuantas imagenes capturar por persona.
N_IMAGENES = 40


def main():
    # El nombre se pasa por la linea de comandos.
    if len(sys.argv) < 2:
        print("Uso: python capturar_rostros.py <Nombre>")
        return
    nombre = sys.argv[1]

    # Carpeta destino: dataset/<Nombre>/
    carpeta = os.path.join(config.CARPETA_DATASET, nombre)
    os.makedirs(carpeta, exist_ok=True)

    # Detector Haar empaquetado con OpenCV.
    ruta_haar = os.path.join(cv2.data.haarcascades, config.HAAR_CASCADE)
    detector = cv2.CascadeClassifier(ruta_haar)

    cam = cv2.VideoCapture(config.WEBCAM_INDEX)
    print(f"[CAPTURA] Capturando {N_IMAGENES} rostros de '{nombre}'. ESC para salir.")

    contador = 0
    while contador < N_IMAGENES:
        ok, frame = cam.read()
        if not ok:
            print("[CAPTURA] No se pudo leer la camara.")
            break

        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rostros = detector.detectMultiScale(gris, 1.1, 5, minSize=(80, 80))

        for (x, y, w, h) in rostros:
            # Recortamos, normalizamos tamano y guardamos.
            rostro = cv2.resize(gris[y:y + h, x:x + w], config.TAM_ROSTRO)
            ruta = os.path.join(carpeta, f"{nombre}_{contador:03d}.jpg")
            cv2.imwrite(ruta, rostro)
            contador += 1

            # Dibujamos la caja y el progreso.
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(frame, f"{contador}/{N_IMAGENES}", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            break  # solo un rostro por frame

        cv2.imshow("Captura de rostros - GARRA-OS", frame)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC
            break

    cam.release()
    cv2.destroyAllWindows()
    print(f"[CAPTURA] Listo. Se guardaron {contador} imagenes en {carpeta}")


if __name__ == "__main__":
    main()
