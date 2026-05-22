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
    """Genera el HTML con 4 gráficas profesionales"""
    
    filas_tabla = ""
    for reg in context['historial']:
        filas_tabla += f"""
        <tr>
            <td>{reg.get('fecha', 'N/A')}</td>
            <td>{reg.get('humedad_suelo', 'N/A')}%</td>
            <td>{reg.get('temperatura', 'N/A')}°C\n</td>
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
            padding-bottom: 30px;
        }}
        .card {{
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 20px;
            background: white;
            transition: transform 0.3s;
        }}
        .card:hover {{
            transform: translateY(-5px);
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
            max-height: 250px;
            overflow-y: auto;
        }}
        .table {{
            background: white;
        }}
        .progress-bar {{
            background-color: #28a745;
        }}
        .chart-container {{
            padding: 15px;
            height: 280px;
        }}
        .grafica-titulo {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
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

        <!-- Tarjetas de sensores -->
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

        <!-- GRÁFICA 1: Tendencia de Humedad -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">📈 Tendencia de Humedad (Últimas 24h)</div>
                        <div class="chart-container">
                            <canvas id="humedadChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- GRÁFICAS 2 y 3: Comparativa y Pastel -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🔄 Humedad vs Temperatura</div>
                        <div class="chart-container">
                            <canvas id="comparativaChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🎯 Decisiones de Riego</div>
                        <div class="chart-container">
                            <canvas id="decisionesChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- GRÁFICA 4: Riegos por día -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">📅 Riegos por Día (Última semana)</div>
                        <div class="chart-container" style="height: 300px;">
                            <canvas id="riegosChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Decisión del Sistema -->
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

        <!-- Historial -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <h5>📊 Historial de Riegos</h5>
                        <div class="historial-table">
                            <table class="table table-striped">
                                <thead>
                                    <tr><th>Fecha/Hora</th><th>Humedad Suelo</th><th>Temperatura</th><th>Decisión</th></tr>
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
        // Variable global para almacenar datos de comparativa
        let datosComparativa = {{}};
        
        // Gráfica 1: Tendencia de Humedad
        async function cargarGraficaHumedad() {{
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
                            tooltip: {{ callbacks: {{ label: (ctx) => ctx.parsed.y + '%' }} }}
                        }},
                        scales: {{ y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Humedad (%)' }} }},
                                   x: {{ title: {{ display: true, text: 'Hora' }} }} }}
                    }}
                }});
                
                // Guardar datos para la gráfica de comparativa
                datosComparativa = data;
            }} catch (error) {{
                console.error('Error:', error);
            }}
        }}
        
        // Gráfica 2: Humedad vs Temperatura (simulada)
        async function cargarGraficaComparativa() {{
            try {{
                const response = await fetch('/api/historial');
                const data = await response.json();
                
                // Simular temperaturas para la comparativa (datos reales si existieran)
                const temperaturas = data.humedades.map(h => 20 + (h / 100) * 20);
                
                const ctx = document.getElementById('comparativaChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: data.fechas,
                        datasets: [
                            {{
                                label: 'Humedad (%)',
                                data: data.humedades,
                                backgroundColor: 'rgba(102, 126, 234, 0.7)',
                                borderColor: '#667eea',
                                borderWidth: 1,
                                yAxisID: 'y'
                            }},
                            {{
                                label: 'Temperatura (°C)',
                                data: temperaturas,
                                backgroundColor: 'rgba(220, 53, 69, 0.7)',
                                borderColor: '#dc3545',
                                borderWidth: 1,
                                type: 'line',
                                yAxisID: 'y1'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        if (context.dataset.label === 'Humedad (%)') {{
                                            return context.parsed.y + '%';
                                        }} else {{
                                            return context.parsed.y + '°C';
                                        }}
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                title: {{ display: true, text: 'Humedad (%)' }},
                                beginAtZero: true,
                                max: 100
                            }},
                            y1: {{
                                position: 'right',
                                title: {{ display: true, text: 'Temperatura (°C)' }},
                                beginAtZero: true,
                                max: 40,
                                grid: {{ drawOnChartArea: false }}
                            }}
                        }}
                    }}
                }});
            }} catch (error) {{
                console.error('Error:', error);
            }}
        }}
        
        // Gráfica 3: Decisiones (Pastel)
        async function cargarGraficaDecisiones() {{
            try {{
                const response = await fetch('/api/estadisticas');
                const data = await response.json();
                
                const ctx = document.getElementById('decisionesChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: ['🌊 Regar', '✅ No Regar', '✋ Manual'],
                        datasets: [{{
                            data: [data.regar, data.no_regar, data.manual],
                            backgroundColor: ['#28a745', '#dc3545', '#ffc107'],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{ position: 'bottom' }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        const total = data.regar + data.no_regar + data.manual;
                                        const porcentaje = ((context.raw / total) * 100).toFixed(1);
                                        return context.label + ': ' + context.raw + ' (' + porcentaje + '%)';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }} catch (error) {{
                console.error('Error:', error);
            }}
        }}
        
        // Gráfica 4: Riegos por día
        async function cargarGraficaRiegos() {{
            try {{
                const response = await fetch('/api/riegos-por-dia');
                const data = await response.json();
                
                const ctx = document.getElementById('riegosChart').getContext('2d');
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: data.dias,
                        datasets: [{{
                            label: 'Cantidad de Riegos',
                            data: data.cantidades,
                            backgroundColor: 'linear-gradient(135deg, #667eea, #764ba2)',
                            backgroundColor: 'rgba(102, 126, 234, 0.7)',
                            borderColor: '#667eea',
                            borderWidth: 2,
                            borderRadius: 10
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return context.parsed.y + ' riegos';
                                    }}
                                }}
                            }}
                        }},
                        scales: {{
                            y: {{
                                beginAtZero: true,
                                title: {{ display: true, text: 'Cantidad de Riegos' }},
                                ticks: {{ stepSize: 1 }}
                            }}
                        }}
                    }}
                }});
            }} catch (error) {{
                console.error('Error:', error);
            }}
        }}
        
        // Riego manual
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
        
        // Cargar todas las gráficas
        cargarGraficaHumedad();
        cargarGraficaComparativa();
        cargarGraficaDecisiones();
        cargarGraficaRiegos();
    </script>
</body>
</html>
    """

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

@app.get("/api/estadisticas")
async def api_estadisticas():
    """API para estadísticas de decisiones"""
    try:
        bd = GestorBD()
        
        # Contar decisiones
        total_regar = bd.db['registros'].count_documents({"decision": "regar"})
        total_no_regar = bd.db['registros'].count_documents({"decision": "no_regar"})
        total_manual = bd.db['registros'].count_documents({"decision": "regar_manual"})
        
        return {
            "regar": total_regar,
            "no_regar": total_no_regar,
            "manual": total_manual
        }
    except Exception as e:
        print(f"Error en estadisticas: {e}")
        return {"regar": 0, "no_regar": 0, "manual": 0}


@app.get("/api/riegos-por-dia")
async def api_riegos_por_dia():
    """API para riegos agrupados por día"""
    try:
        bd = GestorBD()
        
        # Agrupar por día
        pipeline = [
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%d/%m", "date": "$fecha"}
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": -1}},
            {"$limit": 7}
        ]
        
        resultados = list(bd.db['registros'].aggregate(pipeline))
        resultados.reverse()
        
        return {
            "dias": [r["_id"] for r in resultados],
            "cantidades": [r["count"] for r in resultados]
        }
    except Exception as e:
        print(f"Error en riegos-por-dia: {e}")
        return {"dias": [], "cantidades": []}



if __name__ == "__main__":
    print("🚀 AgroVoice Pro Web → http://localhost:8000")
    print("📊 Mostrando historial desde MongoDB")
    uvicorn.run("app_web:app", host="0.0.0.0", port=8000, reload=True)