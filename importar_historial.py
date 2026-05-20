import json
from pymongo import MongoClient

def importar():
    print("🔄 Conectando a MongoDB...")
    # Conexión local
    client = MongoClient("mongodb://localhost:27017/")
    db = client["agrovoice"]
    
    # Usamos la colección 'sensores' (como la tenías en tu captura)
    collection = db["sensores"]

    # Ruta exacta a tu JSON en D:
    # Si el archivo no tiene extensión .json, quítala de aquí abajo:
    ruta_json = r"D:\Ciencia_Datos_6to\P_P\2do_avance\datos_agrovoice.json"

    try:
        print(f"📂 Leyendo archivo desde: {ruta_json}")
        with open(ruta_json, 'r', encoding='utf-8') as f:
            datos = json.load(f)
        
        # Limpiamos la colección para no duplicar si lo corres dos veces
        collection.delete_many({})
        
        # Insertamos los ~3000 registros
        print(f"💾 Insertando {len(datos)} registros... espera un momento...")
        collection.insert_many(datos)
        
        print(f"✅ ¡ÉXITO! Se insertaron {len(datos)} registros en la colección 'sensores'.")
        print("👉 Ahora abre MongoDB Compass para verificar.")

    except FileNotFoundError:
        print("❌ ERROR: No encontró el archivo en D:\\...")
        print("Revisa que el nombre sea 'datos_agrovoice.json' o ajusta la ruta en el código.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    importar()