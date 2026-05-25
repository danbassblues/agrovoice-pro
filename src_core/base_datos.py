from pymongo import MongoClient
from datetime import datetime

# Cadena de conexión a MongoDB Atlas
ATLAS_URI = "mongodb+srv://agrovoice_user:AgroVoice2026@cluster0.iuul628.mongodb.net/?appName=Cluster0"

class GestorBD:
    def __init__(self):
        try:
            self.client = MongoClient(ATLAS_URI)
            self.db = self.client['agrovoice']
            print("✅ Conexión a MongoDB Atlas establecida")
        except Exception as e:
            print(f"❌ Error conectando a Atlas: {e}")
            raise
    
    def obtener_ultimos_registros(self, limit=12):
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
        try:
            registro = {
                "fecha": datetime.now(),
                "humedad_suelo": humedad_suelo,
                "temperatura": temperatura,
                "decision": decision,
                "tipo": "automatico"
            }
            self.db['registros'].insert_one(registro)
            print(f"✅ Registro guardado: {decision} - Humedad: {humedad_suelo}%")
            return True
        except Exception as e:
            print(f"Error guardando registro: {e}")
            return False
    
    def obtener_sensores(self, limit=100):
        try:
            sensores = list(self.db['sensores']
                          .find({})
                          .sort('fecha', -1)
                          .limit(limit))
            return sensores
        except Exception as e:
            print(f"Error obteniendo sensores: {e}")
            return []
    
    def guardar_clima_api(self, datos_clima):
        try:
            datos_clima['fecha'] = datetime.now()
            self.db['clima_real'].insert_one(datos_clima)
            print("✅ Datos de clima guardados")
            return True
        except Exception as e:
            print(f"⚠️ Error guardando clima: {e}")
            return False