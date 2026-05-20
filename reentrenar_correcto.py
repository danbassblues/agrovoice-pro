# crear archivo: reentrenar_correcto.py
from src_core.ia_modelo import ModeloRiego
from src_core.base_datos import GestorBD
import numpy as np
import joblib

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
        y = np.array([1 if s['humedad_suelo'] < 30 else 0 for s in sensores])
        
        print(f"🎯 Distribución: Regar: {sum(y)} veces ({sum(y)/len(y)*100:.1f}%)")
        
        # Entrenar modelo (si existe método fit)
        if hasattr(modelo, 'fit'):
            modelo.fit(X, y)
            print("✅ Modelo entrenado correctamente")
        
        # Guardar usando joblib (método alternativo)
        if hasattr(modelo, 'modelo'):
            joblib.dump(modelo.modelo, 'modelo_riego.pkl')
            print("✅ Modelo guardado en 'modelo_riego.pkl'")
        
        print("\n🧪 Probando modelo con 3000 datos:")
        pruebas = [(20, 25, "Humedad baja"), (50, 25, "Humedad óptima"), (80, 30, "Humedad alta")]
        for humedad, temp, desc in pruebas:
            decision = modelo.predecir(humedad, temp)
            print(f"  {desc}: {humedad}% → {decision}")
        
        print("\n✅ Proceso completado!")
    else:
        print(f"⚠️ Solo {len(sensores)} registros")

if __name__ == "__main__":
    reentrenar_modelo()