# crear archivo: generar_historial_realista.py
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

def generar_historial_realista():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['agrovoice']
    registros = db['registros']
    
    # Limpiar registros anteriores si quieres
    # registros.delete_many({})
    
    print("📝 Generando historial realista de 7 días...")
    
    for dia in range(7):
        fecha_base = datetime.now() - timedelta(days=7-dia)
        
        # 8 registros por día (cada 3 horas)
        for hora in [0, 3, 6, 9, 12, 15, 18, 21]:
            fecha = fecha_base.replace(hour=hora, minute=0, second=0)
            
            # Patrón realista: humedad baja al mediodía (calor)
            if 12 <= hora <= 15:
                humedad = random.uniform(15, 35)  # más seco
            elif 0 <= hora <= 6:
                humedad = random.uniform(45, 70)  # más húmedo (rocío)
            else:
                humedad = random.uniform(30, 55)  # normal
            
            temperatura = 20 + (hora / 24) * 15  # más calor al mediodía
            
            decision = "regar" if humedad < 30 else "no_regar"
            
            registro = {
                "fecha": fecha,
                "humedad_suelo": round(humedad, 1),
                "temperatura": round(temperatura, 1),
                "decision": decision,
                "tipo": "automatico"
            }
            
            registros.insert_one(registro)
    
    total = registros.count_documents({})
    print(f"✅ Historial realista generado: {total} registros")
    client.close()

if __name__ == "__main__":
    generar_historial_realista()