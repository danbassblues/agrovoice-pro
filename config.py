#!/usr/bin/env python3
"""
 CONFIGURACIÓN CENTRALIZADA - AgroVoice Pro
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno (si existen)
load_dotenv()

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = DATA_DIR / "modelo_riego_v2.keras"
VOCES_DIR = Path.home() / "voces_piper"

# Crear directorio data si no existe
DATA_DIR.mkdir(exist_ok=True)

# =========================
#  CONFIGURACIÓN DE VOZ
# =========================
VOZ_MODELO_ACTIVO = "ald"  # Cambiar a "claude" si lo descargaste
VOZ_VELOCIDAD = 1.05
VOZ_ESPEAK_FALLBACK = "es+f3"

if VOZ_MODELO_ACTIVO == "claude":
    VOICE_PATH = VOCES_DIR / "es_MX-claude-high.onnx"
elif VOZ_MODELO_ACTIVO == "josefina":
    VOICE_PATH = VOCES_DIR / "es_MX-josefina-medium.onnx"
else:
    VOICE_PATH = VOCES_DIR / "es_MX-ald-medium.onnx"

# =========================
# 🧠 CONFIGURACIÓN IA
# =========================
UMBRAL_RIEGO = 0.5
EPOCHS_ENTRENAMIENTO = 50
PATIENCE_EARLY_STOP = 5

# =========================
# 🌍 COORDENADAS Y APIS
# =========================
LATITUD = float(os.getenv("LAT_RANCHO", 25.6866))
LONGITUD = float(os.getenv("LON_RANCHO", -100.3161))
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# =========================
# 💾 BASE DE DATOS
# =========================
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "agrovoice"
MONGO_COLECCION_DATOS = "registros"
MONGO_COLECCION_CLIMA = "clima_real"
