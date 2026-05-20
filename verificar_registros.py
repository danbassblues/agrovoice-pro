# crear archivo: verificar_registros.py
from pymongo import MongoClient

def verificar_registros():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['agrovoice']
    
    if 'registros' in db.list_collection_names():
        registros = db['registros']
        total = registros.count_documents({})
        
        print(f"📊 Total de registros históricos: {total}")
        
        if total > 0:
            print("\n📝 Últimos 5 registros:")
            for reg in registros.find().sort('fecha', -1).limit(5):
                fecha = reg.get('fecha', 'sin fecha')
                if hasattr(fecha, 'strftime'):
                    fecha = fecha.strftime("%d/%m %H:%M")
                print(f"  • {fecha} - Humedad: {reg.get('humedad_suelo', 'N/A')}% - {reg.get('decision', 'N/A')}")
        else:
            print("\n⚠️ No hay registros aún")
            print("💡 Prueba:")
            print("   1. Haz clic en 'Activar Riego Manual' en la web")
            print("   2. O ejecuta: python generar_historial.py")
    else:
        print("⚠️ La colección 'registros' no existe")
        print("💡 Ejecuta primero: python generar_historial.py")
    
    client.close()

if __name__ == "__main__":
    verificar_registros()