"""
=========================================================================
OBJETIVO:
Entrenar el modelo de reconocimiento facial LBPH de GARRA-OS a partir de
las imagenes guardadas en la carpeta dataset/. Genera dos archivos:
   - modelo/modelo_lbph.yml   -> el modelo entrenado
   - modelo/etiquetas.json    -> el mapa {id_numerico: "Nombre"}

QUE PREDICE / TIPO DE MODELO:
LBPH (Local Binary Patterns Histograms) aprende un histograma de
patrones binarios locales por persona. En prediccion compara el rostro
nuevo contra esos histogramas y entrega la etiqueta mas parecida + una
distancia (menor = mas parecido). Es un clasificador supervisado clasico,
ligero, que corre en CPU sin GPU.

USO:
   python entrenar_rostros.py

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
import json
import numpy as np
import config


def cargar_dataset():
    """
    Recorre dataset/<Nombre>/*.jpg y arma:
       - rostros : lista de imagenes (np.array en gris)
       - ids     : lista de id numerico por imagen
       - etiquetas: dict {id_numerico: "Nombre"}
    """
    rostros, ids = [], []
    etiquetas = {}
    siguiente_id = 0

    if not os.path.isdir(config.CARPETA_DATASET):
        raise FileNotFoundError(
            f"No existe la carpeta '{config.CARPETA_DATASET}'. "
            f"Primero corre capturar_rostros.py."
        )

    # Cada subcarpeta es una persona.
    for nombre in sorted(os.listdir(config.CARPETA_DATASET)):
        carpeta = os.path.join(config.CARPETA_DATASET, nombre)
        if not os.path.isdir(carpeta):
            continue

        etiquetas[siguiente_id] = nombre

        for archivo in os.listdir(carpeta):
            if not archivo.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            ruta = os.path.join(carpeta, archivo)
            img = cv2.imread(ruta, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            img = cv2.resize(img, config.TAM_ROSTRO)
            rostros.append(img)
            ids.append(siguiente_id)

        print(f"[ENTRENA] '{nombre}' -> id {siguiente_id} "
              f"({ids.count(siguiente_id)} imagenes)")
        siguiente_id += 1

    return rostros, ids, etiquetas


def main():
    print("[ENTRENA] Cargando dataset...")
    rostros, ids, etiquetas = cargar_dataset()

    if len(rostros) == 0:
        print("[ENTRENA] No hay imagenes. Corre capturar_rostros.py primero.")
        return

    # Creamos y entrenamos el reconocedor (necesita opencv-contrib-python).
    reconocedor = cv2.face.LBPHFaceRecognizer_create()
    reconocedor.train(rostros, np.array(ids))

    # Guardamos modelo y etiquetas.
    os.makedirs(os.path.dirname(config.ARCHIVO_MODELO), exist_ok=True)
    reconocedor.save(config.ARCHIVO_MODELO)
    with open(config.ARCHIVO_ETIQUETAS, "w", encoding="utf-8") as f:
        json.dump(etiquetas, f, ensure_ascii=False, indent=2)

    print(f"[ENTRENA] Modelo guardado en {config.ARCHIVO_MODELO}")
    print(f"[ENTRENA] Etiquetas: {etiquetas}")
    print(f"[ENTRENA] Total de imagenes entrenadas: {len(rostros)}")


if __name__ == "__main__":
    main()
