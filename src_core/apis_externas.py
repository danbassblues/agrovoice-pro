#!/usr/bin/env python3
"""
☁️ Módulo de APIs Externas - AgroVoice Pro
Ubicación: src_core/apis_externas.py
"""

import sys
import os
import requests
from datetime import datetime

# ==========================================
#  SOLUCIÓN ROBUSTA DE RUTAS
# ==========================================
# Obtener la ruta absoluta de la carpeta raíz del proyecto (agrovoice_pro)
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

try:
    import config
    from src_core.base_datos import GestorBD
except ImportError as e:
    print(f"❌ Error crítico de importación: {e}")
    print(f"   Asegúrate de que config.py esté en: {ROOT_DIR}")
    sys.exit(1)
def obtener_clima_real():
    """Consulta la API y guarda el resultado en Mongo"""
    
    # Si no hay API Key configurada, usamos datos simulados para la demo
    if not config.OPENWEATHER_API_KEY or config.OPENWEATHER_API_KEY == "":
        print("⚠️ Sin API Key. Usando datos climáticos simulados para demo.")
        datos_simulados = {
            "timestamp": datetime.now(),
            "temperatura_ambiente": 32.5,
            "humedad_ambiente": 45,
            "descripcion": "cielo despejado (simulado)",
            "fuente": "openweather_mock"
        }
        bd = GestorBD()
        bd.guardar_clima_api(datos_simulados)
        return datos_simulados

    url = f"https://api.openweathermap.org/data/2.5/weather?lat={config.LATITUD}&lon={config.LONGITUD}&appid={config.OPENWEATHER_API_KEY}&units=metric&lang=es"
    
    try:
        respuesta = requests.get(url).json()
        
        if respuesta.get("cod") != 200:
            raise Exception(respuesta.get("message"))

        datos_reales = {
            "timestamp": datetime.now(),
            "temperatura_ambiente": respuesta['main']['temp'],
            "humedad_ambiente": respuesta['main']['humidity'],
            "descripcion": respuesta['weather'][0]['description'],
            "fuente": "openweather_real"
        }
        
        bd = GestorBD()
        bd.guardar_clima_api(datos_reales)
        return datos_reales

    except Exception as e:
        print(f"❌ Error consultando API Clima: {e}")
        return None

# 🧪 Prueba local
if __name__ == "__main__":
    print("🌍 Probando conexión a APIs externas...")
    clima = obtener_clima_real()
    if clima:
        print(f"✅ Clima obtenido: {clima['temperatura_ambiente']}°C, {clima['descripcion']}")
    else:
        print("❌ No se pudo obtener clima.")
