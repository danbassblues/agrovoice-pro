# Este es el app_web.py completo y corregido CON DIAGNÓSTICO
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import sys
import os
from datetime import datetime
import random

# ===== DIAGNÓSTICO PARA RENDER =====
print("=== DIAGNÓSTICO DE ARCHIVOS ===")
print("Directorio actual:", os.getcwd())
print("Archivos en directorio:", os.listdir("."))
print("¿Existe config.py?", os.path.exists("config.py"))

# Buscar config.py en todo el árbol
for root, dirs, files in os.walk("."):
    if "config.py" in files:
        print(f"✅ config.py encontrado en: {root}")
    if "app_web.py" in files:
        print(f"✅ app_web.py encontrado en: {root}")
# =================================

# Asegurar que el directorio actual está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Intentar importar config
try:
    import config
    print("✅ config.py importado correctamente")
    print(f"📦 MONGO_URI desde config: {config.MONGO_URI[:50]}...")
except Exception as e:
    print(f"❌ Error importando config: {e}")
    # Crear config en memoria como fallback
    class config:
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        MONGO_DB_NAME = "agrovoice"
        MONGO_COLECCION_DATOS = "registros"
        MONGO_COLECCION_CLIMA = "clima_real"
        MODEL_PATH = "data/modelo_riego_v2.keras"
        OPENWEATHER_API_KEY = ""
        LATITUD = 25.6866
        LONGITUD = -100.3161
    print("⚠️ Usando configuración de respaldo")

from src_core.ia_modelo import ModeloRiego
from src_core.base_datos import GestorBD
from src_core.apis_externas import obtener_clima_real

app = FastAPI(title="AgroVoice Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")

def generar_html(context):
    """Genera el HTML con los datos del historial incluidos y gráfica"""
    
    # Construir filas de la tabla del historial
    filas_tabla = ""
    for reg in context['historial']:
        filas_tabla += f"""
        <tr>
            <td>{reg.get('fecha', 'N/A')}</td>
            <td>{reg.get('humedad_suelo', 'N/A')}%</td>
            <td>{reg.get('temperatura', 'N/A')}°C</td>
            <td>{reg.get('decision', 'N/A')}</td>
        </tr>
        """
    
    if not context['historial']:
        filas_tabla = '<tr><td colspan="4" class="text-center">No hay registros aún</td></tr>'
    
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgroVoice Pro - Sistema de Riego Inteligente</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        .card {{
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            background: white;
        }}
        .dashboard-title {{
            color: white;
            text-align: center;
            padding: 30px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .sensor-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .decision-card {{
            text-align: center;
            padding: 20px;
        }}
        .btn-riego {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            padding: 15px 30px;
            font-size: 1.2em;
            border-radius: 50px;
            color: white;
            cursor: pointer;
            transition: transform 0.3s;
        }}
        .btn-riego:hover {{
            transform: scale(1.05);
        }}
        .historial-table {{
            max-height: 300px;
            overflow-y: auto;
        }}
        .table {{
            background: white;
        }}
        .progress-bar {{
            background-color: #28a745;
        }}
        .chart-container {{
            padding: 20px;
            height: 320px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="dashboard-title">
            <h1>🌾 AgroVoice Pro</h1>
            <p>Sistema de Riego Inteligente</p>
            <small>Última actualización: {context['now']}</small>
        </div>

        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h5 class="card-title">💧 Humedad del Suelo</h5>
                        <div class="sensor-value">{context['humedad_suelo']}%</div>
                        <div class="mt-2">
                            <div class="progress">
                                <div class="progress-bar" style="width: {context['humedad_suelo']}%"></div>
                            </div>
                        </div>
                        <small class="text-muted">Nivel óptimo: 30-70%</small>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h5 class="card-title">🌡️ Temperatura Ambiente</h5>
                        <div class="sensor-value">{context['temp']}°C</div>
                    </div>
                </div>
            </div>

            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h5 class="card-title">💨 Humedad Ambiente</h5>
                        <div class="sensor-value">{context['hum_amb']}%</div>
                        <p class="mt-2">{context['descripcion']}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- GRÁFICA DE TENDENCIA -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5>📈 Tendencia de Humedad (Últimas 24h)</h5>
                        <div class="chart-container">
                            <canvas id="humedadChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card decision-card">
                    <div class="card-body">
                        <h3>🤖 Decisión del Sistema</h3>
                        <div class="sensor-value" style="font-size: 1.8em; color: {'#28a745' if 'regar' in context['decision'].lower() else '#dc3545'}">
                            {context['decision']}
                        </div>
                        <button class="btn-riego mt-3" onclick="activarRiegoManual()">
                            💧 Activar Riego Manual
                        </button>
                        <div id="mensajeRiego" class="mt-3"></div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5>📊 Historial de Riegos</h5>
                        <div class="historial-table">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>Fecha/Hora</th>
                                        <th>Humedad Suelo</th>
                                        <th>Temperatura</th>
                                        <th>Decisión</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {filas_tabla}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Cargar datos para la gráfica
        async function cargarGrafica() {{
            try {{
                const response = await fetch('/api/historial');
                const data = await response.json();
                
                const ctx = document.getElementById('humedadChart').getContext('2d');
                
                new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: data.fechas,
                        datasets: [{{
                            label: 'Humedad del Suelo (%)',
                            data: data.humedades,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#764ba2',
                            pointBorderColor: '#fff',
                            pointRadius: 5,
                            pointHoverRadius: 7
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{
                                position: 'top',
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return context.parsed.y + '%';
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                max: 100,
                                title: {{
                                    display: true,
                                    text: 'Humedad (%)'
                                }}
                            }},
                            x: {{
                                title: {{
                                    display: true,
                                    text: 'Hora'
                                }}
                            }}
                        }}
                    }}
                }});
            }} catch (error) {{
                console.error('Error cargando gráfica:', error);
            }}
        }}
        
        // Función para riego manual
        async function activarRiegoManual() {{
            try {{
                const response = await fetch('/regar', {{ method: 'POST' }});
                const data = await response.json();
                const mensajeDiv = document.getElementById('mensajeRiego');
                if (data.status === 'success') {{
                    mensajeDiv.innerHTML = '<div class="alert alert-success">✅ Riego activado correctamente</div>';
                    setTimeout(() => location.reload(), 2000);
                }} else {{
                    mensajeDiv.innerHTML = '<div class="alert alert-danger">❌ Error al activar el riego</div>';
                }}
            }} catch (error) {{
                console.error('Error:', error);
                document.getElementById('mensajeRiego').innerHTML = '<div class="alert alert-danger">❌ Error de conexión</div>';
            }}
        }}
        
        // Cargar gráfica al iniciar
        cargarGrafica();
    </script>
</body>
</html>
    """
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        print("🟢 Iniciando dashboard...")
        bd = GestorBD()
        ia = ModeloRiego()
        ia.cargar_o_crear()

        clima = obtener_clima_real() or {
            "temperatura_ambiente": 28.0, 
            "humedad_ambiente": 45.0, 
            "descripcion": "Cielo despejado (simulado)"
        }
        
        # Simular humedad del suelo (puedes cambiarlo por un sensor real)
        humedad_suelo = round(random.uniform(15, 55), 1)
        decision = ia.predecir(humedad_suelo, clima["temperatura_ambiente"])

        # OBTENER HISTORIAL REAL DE MongoDB
        historial = []
        try:
            # Buscar en la colección 'registros'
            if hasattr(bd, 'db'):
                registros = bd.db['registros'].find({}).sort('fecha', -1).limit(20)
                for reg in registros:
                    # Formatear la fecha
                    fecha = reg.get('fecha', None)
                    if fecha and hasattr(fecha, 'strftime'):
                        fecha_str = fecha.strftime("%d/%m/%Y %H:%M")
                    else:
                        fecha_str = str(fecha) if fecha else "Sin fecha"
                    
                    historial.append({
                        "fecha": fecha_str,
                        "humedad_suelo": reg.get('humedad_suelo', 'N/A'),
                        "temperatura": reg.get('temperatura', 'N/A'),
                        "decision": reg.get('decision', 'N/A')
                    })
                print(f"📊 Historial cargado: {len(historial)} registros")
        except Exception as e:
            print(f"⚠️ Error cargando historial: {e}")
            historial = []

        context = {
            "humedad_suelo": float(humedad_suelo),
            "temp": float(clima.get("temperatura_ambiente", 25.0)),
            "hum_amb": float(clima.get("humedad_ambiente", 45.0)),
            "descripcion": str(clima.get("descripcion", "")),
            "decision": str(decision) if decision else "Sin decisión",
            "historial": historial,
            "now": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        
        html_content = generar_html(context)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(content=f"""
        <html>
            <body>
                <h1>Error en el servidor</h1>
                <p>{str(e)}</p>
            </body>
        </html>
        """, status_code=500)


@app.post("/regar")
async def activar_riego_manual():
    try:
        bd = GestorBD()
        # Guardar el registro de riego manual
        if hasattr(bd, 'db'):
            registro = {
                "fecha": datetime.now(),
                "humedad_suelo": 0,  # Se actualizará con el sensor real
                "temperatura": 0,
                "decision": "regar_manual",
                "tipo": "manual"
            }
            bd.db['registros'].insert_one(registro)
            print("✅ Riego manual registrado")
        return {"status": "success"}
    except Exception as e:
        print(f"❌ Error en riego manual: {e}")
        return {"status": "error"}


@app.get("/api/historial")
async def api_historial():
    """API para obtener datos de la gráfica"""
    try:
        bd = GestorBD()
        registros = list(bd.db['registros']
                        .find({}, {'_id': 0, 'fecha': 1, 'humedad_suelo': 1})
                        .sort('fecha', -1)
                        .limit(24))
        
        # Invertir para orden cronológico
        registros.reverse()
        
        # Formatear para la gráfica
        datos = {
            "fechas": [],
            "humedades": []
        }
        
        for reg in registros:
            fecha = reg.get('fecha')
            if fecha and hasattr(fecha, 'strftime'):
                datos["fechas"].append(fecha.strftime("%H:%M"))
            else:
                datos["fechas"].append("N/A")
            datos["humedades"].append(reg.get('humedad_suelo', 0))
        
        return datos
    except Exception as e:
        print(f"Error en API: {e}")
        return {"fechas": [], "humedades": []}


if __name__ == "__main__":
    print("🚀 AgroVoice Pro Web → http://localhost:8000")
    print("📊 Mostrando historial desde MongoDB")
    uvicorn.run("app_web:app", host="0.0.0.0", port=8000, reload=True)