"""
=========================================================================
OBJETIVO:
PRUEBA ESTATICA del pipeline de IA de GARRA-OS (requisito de la rubrica:
"el modelo debe probarse con datos estaticos antes de integrarlo al flujo
MQTT"). Este script NO usa MQTT ni la camara en vivo. Mide la PRECISION
de los dos modelos con datos locales y deja la evidencia en consola:

   1) RECONOCIMIENTO FACIAL (LBPH):
      Hace una particion train/test (hold-out) del dataset, entrena con
      una parte y evalua con la otra. Reporta la PRECISION (accuracy)
      global y por persona, y la distancia LBPH promedio. Asi el numero
      de precision es REAL y medido sobre tus propias imagenes.

   2) GESTO (MediaPipe):
      Clasifica las imagenes estaticas de test_images/ como palma abierta
      o no, segun el prefijo del nombre del archivo:
         test_images/palma_*.jpg    -> se espera PALMA ABIERTA
         test_images/nopalma_*.jpg  -> se espera NO palma
      y reporta cuantas acerto.

USO:
   python prueba_estatica.py

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
import random
import numpy as np
import config


# -------------------------------------------------------------------------
# PARTE 1: PRECISION DEL RECONOCIMIENTO FACIAL (hold-out)
# -------------------------------------------------------------------------
def evaluar_rostros(porcentaje_test=0.2, semilla=42):
    print("=" * 70)
    print("PRUEBA ESTATICA 1/2 - RECONOCIMIENTO FACIAL (LBPH)")
    print("=" * 70)

    if not os.path.isdir(config.CARPETA_DATASET):
        print(f"[X] No existe '{config.CARPETA_DATASET}'. Corre capturar_rostros.py.")
        return

    random.seed(semilla)

    # Armamos listas de (ruta, id, nombre) por persona y partimos train/test.
    train_rostros, train_ids = [], []
    test_items = []   # (ruta, id, nombre)
    etiquetas = {}
    next_id = 0

    for nombre in sorted(os.listdir(config.CARPETA_DATASET)):
        carpeta = os.path.join(config.CARPETA_DATASET, nombre)
        if not os.path.isdir(carpeta):
            continue
        archivos = [f for f in os.listdir(carpeta)
                    if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if len(archivos) < 2:
            print(f"[!] '{nombre}' tiene muy pocas imagenes; se omite.")
            continue

        random.shuffle(archivos)
        corte = max(1, int(len(archivos) * porcentaje_test))
        test_files = archivos[:corte]
        train_files = archivos[corte:]

        etiquetas[next_id] = nombre
        for f in train_files:
            img = cv2.imread(os.path.join(carpeta, f), cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            train_rostros.append(cv2.resize(img, config.TAM_ROSTRO))
            train_ids.append(next_id)
        for f in test_files:
            test_items.append((os.path.join(carpeta, f), next_id, nombre))
        next_id += 1

    if not train_rostros or not test_items:
        print("[X] No hay suficientes imagenes para evaluar.")
        return

    # Entrenamos SOLO con el train split.
    reconocedor = cv2.face.LBPHFaceRecognizer_create()
    reconocedor.train(train_rostros, np.array(train_ids))

    # Evaluamos sobre el test split.
    aciertos = 0
    total = len(test_items)
    dist_acumulada = 0.0
    por_persona = {}   # nombre -> [aciertos, total]

    for ruta, id_real, nombre in test_items:
        img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        img = cv2.resize(img, config.TAM_ROSTRO)
        id_pred, distancia = reconocedor.predict(img)
        dist_acumulada += distancia

        ok = (id_pred == id_real) and (distancia <= config.UMBRAL_LBPH)
        por_persona.setdefault(nombre, [0, 0])
        por_persona[nombre][1] += 1
        if ok:
            aciertos += 1
            por_persona[nombre][0] += 1

    print(f"\nImagenes de entrenamiento : {len(train_rostros)}")
    print(f"Imagenes de prueba        : {total}")
    print(f"Umbral LBPH usado         : {config.UMBRAL_LBPH}")
    print("\nPrecision por persona:")
    for nombre, (ac, tot) in por_persona.items():
        pct = 100.0 * ac / tot if tot else 0
        print(f"   - {nombre:<15} {ac}/{tot}   ({pct:.1f}%)")

    precision = 100.0 * aciertos / total
    dist_prom = dist_acumulada / total
    print(f"\n>>> PRECISION GLOBAL : {aciertos}/{total} = {precision:.1f}%")
    print(f">>> Distancia LBPH promedio: {dist_prom:.1f} "
          f"(menor = mejor; umbral = {config.UMBRAL_LBPH})")
    print()


# -------------------------------------------------------------------------
# PARTE 2: GESTO SOBRE IMAGENES ESTATICAS (MediaPipe)
# -------------------------------------------------------------------------
def evaluar_gestos():
    print("=" * 70)
    print("PRUEBA ESTATICA 2/2 - GESTO PALMA ABIERTA (MediaPipe)")
    print("=" * 70)

    carpeta = config.CARPETA_TEST_IMAGES
    if not os.path.isdir(carpeta):
        print(f"[!] No existe '{carpeta}'. Coloca imagenes palma_*.jpg y "
              f"nopalma_*.jpg para evaluar el gesto. Se omite esta parte.")
        return

    archivos = [f for f in os.listdir(carpeta)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if not archivos:
        print(f"[!] '{carpeta}' esta vacia. Se omite esta parte.")
        return

    # Importamos aqui para no exigir MediaPipe si solo se evalua rostros.
    from gestos import DetectorGestos
    detector = DetectorGestos()

    aciertos, total = 0, 0
    for f in sorted(archivos):
        ruta = os.path.join(carpeta, f)
        frame = cv2.imread(ruta)
        if frame is None:
            continue
        esperado = f.lower().startswith("palma")  # True si se espera palma
        detectado, _ = detector.hay_palma_abierta(frame)
        ok = (detectado == esperado)
        total += 1
        aciertos += 1 if ok else 0
        marca = "OK " if ok else "XX "
        print(f"   {marca} {f:<22} esperado={esperado!s:<5} "
              f"detectado={detectado!s:<5}")

    detector.cerrar()
    if total:
        print(f"\n>>> PRECISION GESTO : {aciertos}/{total} = "
              f"{100.0 * aciertos / total:.1f}%\n")


if __name__ == "__main__":
    evaluar_rostros()
    evaluar_gestos()
    print("Prueba estatica finalizada. Si los numeros son buenos, ya puedes")
    print("correr el pipeline completo con: python servidor_ia.py")
