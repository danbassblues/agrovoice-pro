#!/usr/bin/env python3
"""
🚀 MAIN.PY - AgroVoice Pro
Orquestador del sistema: Une Voz, IA, BD y APIs.
Ubicación: /agrovoice_pro/main.py
"""

import sys
import os
import random
import time

# Importar módulos internos desde las carpetas src_
from src_utils.voz import hablar
from src_core.ia_modelo import ModeloRiego
from src_core.base_datos import GestorBD
from src_core.apis_externas import obtener_clima_real
from src_core.actuadores import ControlRiego

def iniciar_sistema():
    print("="*60)
    print("🌰 AGROVOICE PRO - SISTEMA DE RIEGO INTELIGENTE")
    print("="*60)
    
    # 1. Inicializar componentes
    hablar("Iniciando sistema AgroVoice Pro.")
    bd = GestorBD()
    ia = ModeloRiego()
    
    # 2. Cargar o entrenar modelo de IA
    print("\n🧠 Cargando modelo de IA...")
    ia.cargar_o_crear()
    
    # Opcional: Descomenta la siguiente línea si quieres reentrenar 
    # con los últimos datos de MongoDB cada vez que inicies:
    # ia.entrenar_con_mongo() 
    
    # 3. Obtener clima real (o simulado si no hay API Key)
    print("\n☁️ Consultando clima externo...")
    clima = obtener_clima_real()
    
    if clima:
        temp_amb = clima['temperatura_ambiente']
        hum_amb = clima['humedad_ambiente']
        desc = clima.get('descripcion', 'desconocido')
        hablar(f"Clima actual: {temp_amb} grados, humedad {hum_amb} por ciento. Condición: {desc}.")
    else:
        temp_amb = 30.0 # Valor por defecto si falla la API
        hum_amb = 40.0
        hablar("No se pudo obtener clima externo. Usando valores base para la decisión.")

    # 4. Simulación de sensores de suelo 
    # (En producción, esto vendría de un sensor físico conectado a GPIO/I2C)
    humedad_suelo = round(random.uniform(15, 45), 1)
    
    print(f"\n📊 Datos de Sensores de Suelo:")
    print(f"   Humedad Suelo: {humedad_suelo}%")
    print(f"   Temp Ambiente: {temp_amb}°C")

    # 5. Tomar decisión con la IA
    decision = ia.predecir(humedad_suelo, temp_amb)
    
    print(f"\n🤖 Decisión de la IA: {decision.upper()}")
    
    # 6. Comunicar resultado y guardar en MongoDB
    if decision == "regar":
        hablar("La humedad del suelo es baja. Se recomienda activar el riego inmediatamente.")
        bd.guardar_registro_riego(humedad_suelo, temp_amb, "regar")
    else:
        hablar("Las condiciones son óptimas. No es necesario regar por ahora.")
        bd.guardar_registro_riego(humedad_suelo, temp_amb, "no_regar")

    hablar("Ciclo de monitoreo completado. Sistema en espera.")
    print("\n✅ Ciclo terminado. Revisa MongoDB Compass en 'agrovoice.registros' para ver el dato guardado.")

if __name__ == "__main__":
    try:
        iniciar_sistema()
    except KeyboardInterrupt:
        print("\n👋 Sistema detenido manualmente por el usuario.")
    except Exception as e:
        print(f"\n❌ Error crítico inesperado: {e}")
        import traceback
        traceback.print_exc()
