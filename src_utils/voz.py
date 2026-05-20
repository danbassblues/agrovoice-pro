import sys

def hablar(texto):
    """Síntesis de voz compatible con Windows y Linux"""
    print(f"🔊 [VOZ] {texto}")  # Siempre muestra texto en consola
    
    if sys.platform.startswith("win"):
        #  MODO WINDOWS: Usa pyttsx3 (Motor nativo)
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)  # Velocidad
            engine.say(texto)
            engine.runAndWait()
        except Exception:
            # Si falla la voz, al menos queda el print de arriba
            pass
    else:
        # 🐧 MODO LINUX: Aquí iría tu código original de Piper/espeak
        pass