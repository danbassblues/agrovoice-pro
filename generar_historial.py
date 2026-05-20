# crear archivo: generar_historial.py
from pymongo import MongoClient
from datetime import datetime, timedelta
import random

def generar_historial():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['agrovoice']
    
    # Crear colección registros si no existe
    if 'registros' not in db.list_collection_names():
        db.create_collection('registros')
    
    registros = db['registros']
    
    # Generar 20 registros históricos simulados
    print("📝 Generando historial de riegos...")
    
    for i in range(20):
        fecha = datetime.now() - timedelta(hours=i*3)
        humedad = random.uniform(15, 65)
        temperatura = random.uniform(20, 35)
        decision = "regar" if humedad < 30 else "no_regar"
        
        registro = {
            "fecha": fecha,
            "humedad_suelo": round(humedad, 1),
            "temperatura": round(temperatura, 1),
            "decision": decision,
            "tipo": "automatico"
        }
        
        registros.insert_one(registro)
        print(f"  ✓ {fecha.strftime('%H:%M')} - Humedad: {humedad:.1f}% → {decision}")
    
    total = registros.count_documents({})
    print(f"\n✅ Historial generado: {total} registros")
    client.close()

if __name__ == "__main__":
    generar_historial()