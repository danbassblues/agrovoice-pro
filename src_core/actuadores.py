#!/usr/bin/env python3
"""
⚡ Módulo de Actuadores - AgroVoice Pro
Ubicación: src_core/actuadores.py
Maneja: Activación de relés/válvulas de riego
"""
import sys
import time

class ControlRiego:
    def __init__(self, pin_rele=18, simulacion=True):
        """
        pin_rele: Pin GPIO donde está conectado el relé (ej. 18 en Raspberry Pi)
        simulacion: Si True, solo imprime en consola (para demo en laptop). 
                    Si False, intenta usar GPIO real.
        """
        self.pin = pin_rele
        self.simulacion = simulacion
        
        if not self.simulacion:
            try:
                # Intentar importar RPi.GPIO si estamos en Linux/Raspberry
                import RPi.GPIO as GPIO
                self.GPIO = GPIO
                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.pin, GPIO.OUT)
                GPIO.output(self.pin, GPIO.LOW) # Apagado por seguridad
                print("✅ Hardware de riego inicializado.")
            except ImportError:
                print("⚠️ Advertencia: RPi.GPIO no encontrado. Usando modo simulación.")
                self.simulacion = True

    def activar_riego(self, duracion_segundos=5):
        """Abre la válvula de riego por X segundos"""
        if self.simulacion:
            print(f"💧 [SIMULACIÓN] Válvula ABERTA por {duracion_segundos} segundos...")
            # Aquí podrías poner un sonido de agua si quieres
            time.sleep(duracion_segundos) # Simula el tiempo de espera
            print("💧 [SIMULACIÓN] Válvula CERRADA.")
        else:
            print(f"💧 [HARDWARE] Activando Relé en Pin {self.pin}...")
            self.GPIO.output(self.pin, self.GPIO.HIGH) # Activa el relé
            time.sleep(duracion_segundos)
            self.GPIO.output(self.pin, self.GPIO.LOW)  # Desactiva el relé
            print("💧 [HARDWARE] Riego finalizado.")

    def limpiar(self):
        """Limpia recursos GPIO al cerrar"""
        if not self.simulacion:
            self.GPIO.cleanup()