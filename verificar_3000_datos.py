# crear archivo: verificar_3000_datos.py
from pymongo import MongoClient

def verificar_datos():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['agrovoice']
    
    # Verificar colección sensores
    sensores = db['sensores']
    total = sensores.count_documents({})
    
    print("✅ VERIFICACIÓN DE DATOS\n" + "="*40)
    print(f"📊 Total de registros en sensores: {total}")
    
    if total >= 3000:
        print("🎉 ¡Tienes 3,000+ registros! Perfecto para entrenar la IA")
        
        # Ver últimos registros
        ultimos = sensores.find().sort('fecha', -1).limit(3)
        print("\n📝 Últimos 3 registros agregados:")
        for doc in ultimos:
            fecha = doc.get('fecha', 'sin fecha')
            humedad = doc.get('humedad_suelo', 'N/A')
            temp = doc.get('temperatura', 'N/A')
            print(f"  • {fecha} - Humedad: {humedad}% - Temp: {temp}°C")
        
        # Sugerencia de entrenamiento
        print("\n🚀 PRÓXIMO PASO:")
        print("  Tu modelo de IA está listo para reentrenarse con 3,000 datos")
        print("  Esto mejorará significativamente las predicciones de riego")
        
    else:
        print(f"⚠️ Aún faltan {3000 - total} registros para llegar a 3,000")
    
    client.close()

if __name__ == "__main__":
    verificar_datos()