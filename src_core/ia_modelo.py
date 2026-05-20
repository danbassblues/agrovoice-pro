#!/usr/bin/env python3
"""
🧠 Módulo de IA - AgroVoice Pro
Ubicación: src_core/ia_modelo.py
Maneja: Carga, Entrenamiento con MongoDB, Normalización y Predicción
"""

import sys
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
from pymongo import MongoClient

# ==========================================
#  IMPORTANTE: RUTA A CONFIG.PY
# ==========================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import config
except ImportError:
    print("❌ Error: No se encontró config.py en la carpeta raíz.")
    sys.exit(1)

class ModeloRiego:
    def __init__(self):
        self.modelo = None
        # Conexión segura a MongoDB con timeout
        self.db_client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=3000)

    def cargar_o_crear(self):
        """Carga modelo existente o crea arquitectura nueva"""
        if os.path.exists(config.MODEL_PATH):
            print("📦 Cargando modelo guardado...")
            self.modelo = tf.keras.models.load_model(str(config.MODEL_PATH))
        else:
            print("🆕 Creando nueva arquitectura neuronal...")
            self.modelo = self._construir_arquitectura()

    def _construir_arquitectura(self):
        """Red neuronal optimizada para datos agrícolas"""
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(2,)),  # [humedad, temperatura]
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dropout(0.2),       # Previene sobreajuste
            tf.keras.layers.Dense(8, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def entrenar_con_mongo(self):
        """Extrae datos, normaliza y entrena"""
        print("🔄 Conectando a MongoDB para extraer datos...")
        try:
            db = self.db_client[config.MONGO_DB_NAME]
            coleccion = db[config.MONGO_COLECCION_DATOS]
            cursor = coleccion.find({}, {"humedad": 1, "temperatura": 1, "accion": 1, "_id": 0})
            datos = list(cursor)

            if len(datos) < 10:
                print("⚠️ Pocos datos (<10). Usando conjunto simulado para demo.")
                X = np.array([[20, 35], [30, 32], [40, 28], [15, 38], [35, 30]], dtype=np.float32)
                y = np.array([1, 1, 0, 1, 0], dtype=np.float32)
            else:
                print(f"✅ Se encontraron {len(datos)} registros históricos.")
                X = np.array([[d['humedad'], d['temperatura']] for d in datos], dtype=np.float32)
                y = np.array([1 if d['accion'] == 'regar' else 0 for d in datos], dtype=np.float32)

            # 🔑 Normalización (Humedad 0-100 -> 0-1 | Temp 0-50 -> 0-1)
            X_norm = X.copy()
            X_norm[:, 0] /= 100.0
            X_norm[:, 1] /= 50.0

            # ️ EarlyStopping: Para el entrenamiento si deja de mejorar
            callback = EarlyStopping(monitor='loss', patience=config.PATIENCE_EARLY_STOP, restore_best_weights=True)

            print(f"🧠 Entrenando {config.EPOCHS_ENTRENAMIENTO} épocas máximas...")
            self.modelo.fit(X_norm, y, epochs=config.EPOCHS_ENTRENAMIENTO, validation_split=0.2,
                            callbacks=[callback], verbose=1)

            self.modelo.save(str(config.MODEL_PATH))
            print(f"💾 Modelo guardado exitosamente en {config.MODEL_PATH}")
            
        except Exception as e:
            print(f"❌ Error durante entrenamiento: {e}")

    def predecir(self, humedad, temperatura):
        """Retorna 'regar' o 'no_regar' basado en inputs"""
        if self.modelo is None:
            self.cargar_o_crear()
            
        X = np.array([[humedad, temperatura]], dtype=np.float32)
        X[:, 0] /= 100.0
        X[:, 1] /= 50.0
        
        pred = float(self.modelo.predict(X, verbose=0)[0][0])
        return "regar" if pred > config.UMBRAL_RIEGO else "no_regar"

# ==========================================
#  BLOQUE DE PRUEBA LOCAL
# ==========================================
if __name__ == "__main__":
    print("🧪 Iniciando prueba del módulo IA...")
    modelo = ModeloRiego()
    modelo.cargar_o_crear()
    
    # Entrenar con datos reales de Mongo
    modelo.entrenar_con_mongo()
    
    # Probar predicción
    humedad_test, temp_test = 25.0, 32.0
    decision = modelo.predecir(humedad_test, temp_test)
    print(f"🤖 Predicción (Humedad: {humedad_test}%, Temp: {temp_test}°C) → {decision.upper()}")
    print("✅ Módulo IA listo y operativo.")
