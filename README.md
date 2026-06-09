# GARRA-OS · Integración de Inteligencia Artificial en el Ecosistema IoT (ESP32-CAM ↔ Python IA)

**Materia:** Sistemas Programables — Integración de IA (ESP32-CAM ↔ Python IA)
**Docente:** Ma. Verónica Tapia Ibarra
**Institución:** Instituto Tecnológico de León · Ingeniería en Sistemas Computacionales

## Integrantes
- Alcalá Ramos Luz Estefanía
- Bahena Mora Emilio Salvador
- Casas Bastidas José Iván
- Fischer González Patrick


## Objetivo

GARRA-OS ahora **percibe y decide**. El servidor de Python actúa como el cerebro: ve a través de una cámara, toma una decisión con modelos de IA y manda al robot una respuesta física por MQTT.

Pipeline de **dos etapas encadenadas**:

```
  Cámara (webcam → luego ESP32-CAM)
        │
        ▼  ETAPA 1 · MediaPipe Hands
        │   ¿Palma abierta? (gesto de "saludo") → ARMA el sistema
        ▼  ETAPA 2 · OpenCV LBPH
        │   Reconoce el rostro contra la base de datos local
        ▼  ETAPA 3 · (si hay MATCH)
        │   • gTTS  → "Hola [Nombre], bienvenido al laboratorio"
        │   • MQTT  → comandos a los actuadores
        ▼
  ESP32 (GARRA-OS): OLED cara feliz + servo saluda + buzzer beep
```

El gesto **arma** el reconocimiento (la cara solo se busca cuando ves una palma abierta), lo que ahorra CPU y hace al sistema más intencional.

## Tecnologías de IA usadas

| Etapa | Librería | Tipo de predicción | Precisión aprox. |
|---|---|---|---|
| Gesto | **MediaPipe Hands** | Detección de 21 landmarks + regla de dedos | ~90–95% en buena luz |
| Rostro | **OpenCV LBPH** | Clasificación supervisada (nombre + distancia) | **medida real** por `prueba_estatica.py` |
| Voz | **gTTS** | Síntesis de lenguaje natural (texto → audio) | — |

> En LBPH la "confianza" es una **distancia**: **menor = mejor**. Usamos un umbral (`UMBRAL_LBPH` en `config.py`); por encima de él, el rostro es "Desconocido".

## Rol crítico de la cámara

La cámara **no es un visualizador**: es la **única** entrada que dispara todo el pipeline. Sin el gesto y el rostro vistos por la cámara, el robot no hace nada. Mientras llega la ESP32-CAM física, la webcam de la laptop hace de cámara; para usar la cámara real se cambia **una sola línea** en `config.py`:

```python
FUENTE_VIDEO = "esp32cam"
ESP32CAM_URL = "http://<IP-de-tu-ESP32CAM>:81/stream"
```

## Estructura del repositorio

```
GARRA-OS-IA/
├── README.md
├── requirements.txt
├── .gitignore
│
├── ia/                       # ★ TODO el código de IA (se ejecuta desde aquí)
│   ├── config.py             # Configuración central (broker, tópicos, umbrales, rutas)
│   ├── gestos.py             # Etapa 1 — MediaPipe (palma abierta)
│   ├── reconocimiento.py     # Etapa 2 — OpenCV LBPH (reconocimiento facial)
│   ├── voz.py                # Etapa 3 — gTTS (saludo hablado)
│   ├── comunicacion_mqtt.py  # Cierre — publica comandos a los actuadores
│   ├── firebase_ia.py        # Escribe el reconocimiento en Firebase
│   ├── servidor_ia.py        # ★ Pipeline completo en tiempo real (el cerebro)
│   ├── capturar_rostros.py   # Construye el dataset desde la webcam
│   ├── entrenar_rostros.py   # Entrena el modelo LBPH
│   ├── prueba_estatica.py    # ★ Prueba estática (mide precisión SIN MQTT)
│   └── simulador_dashboard.py# (Demo) llena los sensores del dashboard sin hardware
│
├── credenciales/             # ← AQUÍ va firebase_credentials.json (en .gitignore)
├── dataset/                  # dataset/<Nombre>/*.jpg (rostros de cada integrante)
├── test_images/              # palma_*.jpg / nopalma_*.jpg para probar el gesto
├── modelo/                   # modelo_lbph.yml + etiquetas.json (generados)
├── dashboard/                # Web: index.html, app.js, style.css, logo.gif
├── esp32/                    # rutina_saludo.py (opcional, MicroPython)
└── docs/                     # Reporte en Word
```

> Las rutas a `dataset/`, `modelo/`, `test_images/` y `credenciales/` se
> resuelven solas (rutas absolutas calculadas desde la raíz), así que los
> scripts funcionan tanto si los corres desde la raíz (`python ia/servidor_ia.py`)
> como desde adentro de `ia/` (`cd ia` y luego `python servidor_ia.py`).

## Instalación

```bash
pip install -r requirements.txt
```

Si `cv2.face` da error, asegúrate de **no** tener instalado `opencv-python` junto a `opencv-contrib-python`:

```bash
pip uninstall opencv-python
pip install opencv-contrib-python
```

## Cómo correrlo (orden recomendado)

### 1) Construir la base de datos de rostros (una vez por integrante)

```bash
python ia/capturar_rostros.py Estefania
python ia/capturar_rostros.py Emilio
python ia/capturar_rostros.py Ivan
python ia/capturar_rostros.py Patrick
```

### 2) Entrenar el modelo

```bash
python ia/entrenar_rostros.py
```

### 3) Prueba estática (ANTES de MQTT — requisito de la rúbrica)

```bash
python ia/prueba_estatica.py
```

Esto imprime la **precisión real** del reconocimiento facial (partición train/test) y, si pones imágenes en `test_images/`, también la del gesto. **Captura esa salida como evidencia.**

### 4) Pipeline completo en tiempo real

Con la ESP32 de GARRA-OS encendida y conectada al broker:

```bash
python ia/servidor_ia.py
```

Muestra la **palma abierta** a la cámara → cuando reconozca a un integrante, oirás el saludo y el robot reaccionará (OLED feliz + servo saludando + beep). Presiona `q` para salir.


## Privacidad
La cámara solo se usa localmente para tomar la decisión; no se transmite ningún rostro por MQTT, solo el resultado (nombre + evento).
