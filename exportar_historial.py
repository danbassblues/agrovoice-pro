# crear archivo: exportar_historial.py
from pymongo import MongoClient
import pandas as pd
from datetime import datetime

def exportar_historial():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['agrovoice']
    
    # Obtener registros
    registros = list(db['registros'].find({}, {'_id': 0}))
    
    if registros:
        df = pd.DataFrame(registros)
        
        # Guardar como CSV
        filename = f"historial_riego_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        df.to_csv(filename, index=False)
        
        print(f"✅ Historial exportado a: {filename}")
        print(f"📊 Total registros: {len(registros)}")
        print(f"📅 Período: {df['fecha'].min()} a {df['fecha'].max()}")
        
        # Estadísticas rápidas
        print(f"\n📈 Resumen:")
        print(f"  - Riegos: {len(df[df['decision']=='regar'])} veces")
        print(f"  - No riegos: {len(df[df['decision']=='no_regar'])} veces")
    else:
        print("⚠️ No hay registros para exportar")
    
    client.close()

if __name__ == "__main__":
    exportar_historial()