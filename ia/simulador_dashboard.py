"""
=========================================================================
OBJETIVO:
(SOLO PARA DEMO / CAPTURAS) Como no hay sensores fisicos conectados, este
script escribe datos SIMULADOS directamente en Firebase para que el resto
del dashboard (estado en linea, distancia, aceleracion, bateria, alertas)
NO se vea vacio en las capturas de pantalla.

  ⚠️ IMPORTANTE / HONESTIDAD ACADEMICA:
  Estos NO son lecturas reales de sensores: son valores generados para que
  el dashboard luzca completo. La parte REAL y evaluable de esta entrega es
  el RECONOCIMIENTO FACIAL (servidor_ia.py + tu camara), que SI usa datos
  reales. No presentes estos numeros como mediciones reales de hardware.

  No necesita MQTT ni la ESP32: escribe directo en la Realtime Database
  usando las mismas credenciales del servidor (firebase_credentials.json).

USO:
   python simulador_dashboard.py
   (Ctrl+C para detener; deja el sistema "fuera de linea" al salir.)

INTEGRANTES:
  - Alcala Ramos Luz Estefania        [Codigo: 23240079]
  - Bahena Mora Emilio Salvador       [Codigo: 23240009]
  - Casas Bastidas Jose Ivan          [Codigo: 23240883]
  - Fischer Gonzalez Patrick          [Codigo: 23240045]

PROYECTO: GARRA-OS - Agente Robotico Autonomo con Interfaz Cognitiva
DOCENTE : Ma. Veronica Tapia Ibarra
=========================================================================
"""

import time
import math
import random
import config

try:
    import firebase_admin
    from firebase_admin import credentials, db
except Exception:
    print("Falta firebase-admin. Instala con: pip install firebase-admin")
    raise


def ahora_ms():
    """Hora actual en milisegundos (lo que espera el dashboard)."""
    return int(time.time() * 1000)


def main():
    # Inicializa Firebase (reutiliza las credenciales del servidor de IA).
    if not firebase_admin._apps:
        cred = credentials.Certificate(config.FIREBASE_CRED)
        firebase_admin.initialize_app(cred, {"databaseURL": config.FIREBASE_URL})
    print(f"[SIM] Conectado a {config.FIREBASE_URL}")
    print("[SIM] Generando telemetria de DEMO. Ctrl+C para detener.\n")

    t = 0
    bateria = 92.0
    try:
        while True:
            # Distancia: onda suave entre ~15 y ~85 cm.
            distancia = 50 + 35 * math.sin(t / 6.0) + random.uniform(-2, 2)
            distancia = max(5, round(distancia, 1))

            # Aceleracion: pequenas variaciones alrededor de la gravedad en Z.
            acc = {
                "x": round(random.uniform(-0.08, 0.08), 2),
                "y": round(random.uniform(-0.08, 0.08), 2),
                "z": round(0.98 + random.uniform(-0.03, 0.03), 2),
            }

            # Bateria: baja muy lentamente.
            bateria = max(8.0, bateria - 0.05)

            # Escribimos telemetria y estado.
            db.reference("/telemetria").set({
                "distancia_cm": distancia,
                "aceleracion": acc,
                "bateria_pct": round(bateria, 1),
            })
            db.reference("/estado").set({
                "online": True,
                "ultima_actualizacion": ahora_ms(),
            })

            # De vez en cuando, una alerta de demo (cuando "algo se acerca").
            if distancia < 20 and random.random() < 0.5:
                db.reference("/alertas").push({
                    "timestamp": ahora_ms(),
                    "datos": {
                        "severidad": "media",
                        "fuente": "distancia",
                        "mensaje": f"Objeto cercano detectado a {distancia} cm",
                    },
                })
                print(f"[SIM] Alerta: objeto a {distancia} cm")

            print(f"[SIM] dist={distancia}cm  bat={bateria:.1f}%  acc_z={acc['z']}")
            t += 1
            time.sleep(2)

    except KeyboardInterrupt:
        # Al salir, marcamos el sistema como fuera de linea.
        db.reference("/estado").set({"online": False, "ultima_actualizacion": ahora_ms()})
        print("\n[SIM] Detenido. Sistema marcado fuera de linea.")


if __name__ == "__main__":
    main()
