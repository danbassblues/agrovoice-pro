from pymongo import MongoClient
from datetime import datetime
import config

class GestorBD:
    def __init__(self):
        try:
            # Usar MONGO_URI desde config.py
            self.client = MongoClient(config.MONGO_URI)
            self.db = self.client[config.MONGO_DB_NAME]
            print("✅ Conexión a MongoDB establecida")
        except Exception as e:
            print(f"❌ Error conectando a MongoDB: {e}")
            raise
    
    def obtener_ultimos_registros(self, limit=12):
        """Obtiene los últimos registros de riego"""
        try:
            registros = list(self.db['registros']
                           .find({})
                           .sort('fecha', -1)
                           .limit(limit))
            return registros
        except Exception as e:
            print(f"Error obteniendo registros: {e}")
            return []
    
    def guardar_registro_riego(self, humedad_suelo, temperatura, decision):
        """Guarda un registro de riego"""
        try:
            registro = {
                "fecha": datetime.now(),
                "humedad_suelo": humedad_suelo,
                "temperatura": temperatura,
                "decision": decision,
                "tipo": "automatico"
            }
            self.db['registros'].insert_one(registro)
            print(f"✅ Registro guardado: {decision}")
            return True
        except Exception as e:
            print(f"Error guardando registro: {e}")
            return False
    
    def obtener_sensores(self, limit=1000):
        """Obtiene datos históricos de sensores"""
        try:
            sensores = list(self.db['sensores']
                          .find({})
                          .limit(limit))
            return sensores
        except Exception as e:
            print(f"Error obteniendo sensores: {e}")
            return []
    
    def guardar_clima_api(self, datos_clima):
        """Guarda los datos del clima obtenidos de la API"""
        try:
            datos_clima['fecha'] = datetime.now()
            self.db['clima_real'].insert_one(datos_clima)
            print("✅ Datos de clima guardados")
            return True
        except Exception as e:
            print(f"⚠️ Error guardando clima: {e}")
            return False