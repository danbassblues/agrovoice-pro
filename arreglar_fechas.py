from pymongo import MongoClient
from datetime import datetime, timedelta

def arreglar_fechas():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['agrovoice']
    coleccion = db['sensores']
    
    # Obtener documentos sin fecha
    documentos = list(coleccion.find({'fecha': {'$exists': False}}))
    
    if documentos:
        print(f"📅 Arreglando fechas para {len(documentos)} documentos...")
        
        fecha_base = datetime.now() - timedelta(days=30)
        
        for i, doc in enumerate(documentos):
            nueva_fecha = fecha_base + timedelta(hours=i)
            coleccion.update_one(
                {'_id': doc['_id']},
                {'$set': {'fecha': nueva_fecha}}
            )
            
            if (i + 1) % 500 == 0:
                print(f"  Procesados {i+1} documentos...")
        
        print(f"✅ Fechas agregadas a {len(documentos)} documentos")
    else:
        print("✅ Todos los documentos ya tienen fecha")
    
    client.close()

if __name__ == "__main__":
    arreglar_fechas()