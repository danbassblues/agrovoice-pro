#!/usr/bin/env python3
"""
💾 Módulo de Base de Datos - AgroVoice Pro
Ubicación: src_core/base_datos.py
Maneja: Conexión MongoDB, Inserción de datos históricos y climáticos
"""
import sys
import os
from pymongo import MongoClient, errors
from datetime import datetime

# Ruta absoluta a la raíz del proyecto
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ROOT_DIR)

try:
    import config
except ImportError:
    print("❌ Error: No se encontró config.py en la raíz.")
    sys.exit(1)

class GestorBD:
    def __init__(self):
        try:
            self.client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)
            self.client.admin.command("ping") # Verificar conexión
            self.db = self.client[config.MONGO_DB_NAME]
            print("✅ Conexión a MongoDB establecida.")
        except Exception as e:
            print(f"❌ Error crítico de conexión a BD: {e}")
            self.db = None

    def guardar_registro_riego(self, humedad, temperatura, accion):
        """Guarda una decisión de riego en la colección 'registros'"""
        if self.db is None: return
        
        doc = {
            "timestamp": datetime.now(),
            "humedad": humedad,
            "accion": accion,
            "fuente": "sensor_simulado" # En futuro será real
        }
        
        try:
            self.db[config.MONGO_COLECCION_DATOS].insert_one(doc)
            print(f"💾 Registro guardado: {accion} (H:{humedad}, T:{temperatura})")
        except Exception as e:
            print(f"⚠️ Error al guardar en BD: {e}")

    def guardar_clima_api(self, datos_clima):
        """Guarda datos frescos de API en la colección 'clima_real'"""
        if self.db is None: return
        
        try:
            self.db[config.MONGO_COLECCION_CLIMA].insert_one(datos_clima)
            print(f"🌤️ Clima API guardado: {datos_clima.get('descripcion', 'N/A')}")
        except Exception as e:
            print(f"⚠️ Error al guardar clima: {e}")

    def obtener_ultimo_clima(self):
        """Recupera el último dato climático registrado"""
        if not self.db: return None
        ultimo = self.db[config.MONGO_COLECCION_CLIMA].find_one(sort=[("timestamp", -1)])
        return ultimo

# 🧪 Prueba local
if __name__ == "__main__":
    bd = GestorBD()
    bd.guardar_registro_riego(25.0, 30.0, "regar")
    print("✅ Módulo BD probado.")
