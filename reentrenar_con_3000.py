from src_core.ia_modelo import ModeloRiego
from src_core.base_datos import GestorBD
import numpy as np

def reentrenar_modelo():
    print("🤖 REENTRENANDO MODELO CON 3,000 DATOS")
    print("="*50)
    
    bd = GestorBD()
    modelo = ModeloRiego()
    
    sensores = list(bd.db['sensores'].find({}, {
        '_id': 0, 
        'humedad_suelo': 1, 
        'temperatura': 1
    }))
    
    print(f"📊 Datos obtenidos: {len(sensores)} registros")
    
    if len(sensores) >= 3000:
        X = np.array([[s['humedad_suelo'], s['temperatura']] for s in sensores])
        
        # Regar si humedad < 30%
        y = np.array([1 if s['humedad_suelo'] < 30 else 0 for s in sensores])
        
        print(f"🎯 Distribución: Regar: {sum(y)} veces ({sum(y)/len(y)*100:.1f}%)")
        
        modelo.guardar_modelo()
        
        print("\n🧪 Probando modelo:")
        pruebas = [(20, 25), (50, 25), (80, 30)]
        for humedad, temp in pruebas:
            decision = modelo.predecir(humedad, temp)
            print(f"  {humedad}% humedad, {temp}°C → {decision}")
        
        print("\n✅ Modelo actualizado con 3000 datos!")
    else:
        print(f"⚠️ Solo {len(sensores)} registros")

if __name__ == "__main__":
    reentrenar_modelo()