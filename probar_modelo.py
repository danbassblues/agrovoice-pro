from src_core.ia_modelo import ModeloRiego

def probar_modelo():
    print("🧪 PROBANDO MODELO")
    print("="*30)
    
    modelo = ModeloRiego()
    modelo.cargar_o_crear()
    
    print("\nHumedad | Temp | Decisión")
    print("-" * 30)
    
    casos = [(15, 20), (35, 25), (55, 30), (75, 35)]
    
    for humedad, temp in casos:
        decision = modelo.predecir(humedad, temp)
        icono = "💧" if "regar" in decision.lower() else "✅"
        print(f"  {humedad}%    | {temp}°C  | {icono} {decision}")

if __name__ == "__main__":
    probar_modelo()