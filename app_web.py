# app_web.py - AgroVoice Pro - Version Estable con PDF
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import sys
import os
from datetime import datetime
import random
import statistics

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import config
    print("✅ config.py importado")
except Exception as e:
    print(f"⚠️ Usando config por defecto: {e}")
    class config:
        MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        MONGO_DB_NAME = "agrovoice"

from src_core.ia_modelo import ModeloRiego
from src_core.base_datos import GestorBD
from src_core.apis_externas import obtener_clima_real

app = FastAPI(title="AgroVoice Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")

def generar_html(context):
    filas_tabla = ""
    for reg in context['historial'][:10]:
        filas_tabla += f"""
        <tr>
            <td>{reg.get('fecha', 'N/A')} None
            <td>{reg.get('humedad_suelo', 'N/A')}% None
            <td>{reg.get('temperatura', 'N/A')}°C None
            <td>{reg.get('decision', 'N/A')} None
        </tr>
        """
    
    if not context['historial']:
        filas_tabla = '<tr><td colspan="4" class="text-center">No hay registros aún</td></tr>'
    
    decision_js = context['decision'].lower().replace('"', '\\"')
    humedad_js = context['humedad_suelo']
    
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AgroVoice Pro</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
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
        .btn-voz {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            border: none;
            padding: 8px 20px;
            border-radius: 25px;
            color: white;
            margin-top: 10px;
            cursor: pointer;
        }}
        .btn-pdf {{
            background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
            border: none;
            padding: 8px 20px;
            border-radius: 25px;
            color: white;
            margin-top: 10px;
            cursor: pointer;
            margin-left: 10px;
        }}
        .historial-table {{
            max-height: 250px;
            overflow-y: auto;
        }}
        .table {{
            background: white;
        }}
        .table thead th {{
            color: #667eea;
        }}
        .progress-bar {{
            background-color: #28a745;
        }}
        .chart-container {{
            padding: 15px;
            height: 280px;
            position: relative;
        }}
        .grafica-titulo {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container" id="report-content">
        <div class="dashboard-title">
            <h1>🌾 AgroVoice Pro</h1>
            <p>Sistema de Riego Inteligente con IA y Asistente de Voz</p>
            <small>Última actualización: {context['now']}</small>
        </div>

        <!-- Fila de botones PDF -->
        <div class="row mb-3">
            <div class="col-12 text-end">
                <button class="btn-pdf" onclick="exportarPDF()">
                    📄 Exportar Reporte PDF
                </button>
            </div>
        </div>

        <!-- Tarjetas de sensores -->
        <div class="row">
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h5>💧 Humedad del Suelo</h5>
                        <div class="sensor-value">{context['humedad_suelo']}%</div>
                        <div class="mt-2">
                            <div class="progress">
                                <div class="progress-bar" style="width: {context['humedad_suelo']}%"></div>
                            </div>
                        </div>
                        <small>Óptimo: 30-70%</small>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h5>🌡️ Temperatura Ambiente</h5>
                        <div class="sensor-value">{context['temp']}°C</div>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-body text-center">
                        <h5>💨 Humedad Ambiente</h5>
                        <div class="sensor-value">{context['hum_amb']}%</div>
                        <p>{context['descripcion']}</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gráfica 1 -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">📈 Tendencia de Humedad (Últimas 24h)</div>
                        <div class="chart-container"><canvas id="humedadChart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Estadísticas y Predicción -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">📊 Estadísticas Históricas</div>
                        <div id="estadisticas-container">Cargando...</div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🔮 Predicción para Mañana</div>
                        <div id="prediccion-container">Cargando...</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gráficas 2 y 3 -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🔄 Humedad vs Temperatura</div>
                        <div class="chart-container"><canvas id="comparativaChart"></canvas></div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🎯 Decisiones de Riego</div>
                        <div class="chart-container"><canvas id="decisionesChart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Gráfica 4 -->
        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">📅 Riegos por Día</div>
                        <div class="chart-container"><canvas id="riegosChart"></canvas></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Decisión -->
        <div class="row">
            <div class="col-md-12">
                <div class="card decision-card">
                    <div class="card-body">
                        <h3>🤖 Decisión del Sistema</h3>
                        <div class="sensor-value" style="color: {'#28a745' if 'regar' in context['decision'].lower() else '#dc3545'}">
                            {context['decision']}
                        </div>
                        <button class="btn-voz" onclick="repetirMensaje()">🔊 Repetir</button>
                        <button class="btn-riego mt-3" onclick="activarRiegoManual()">💧 Riego Manual</button>
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
                        <h5>📋 Historial de Riegos</h5>
                        <div class="historial-table">
                            <table class="table table-striped table-sm">
                                <thead><tr><th>Fecha</th><th>Humedad</th><th>Temp</th><th>Decisión</th></tr></thead>
                                <tbody>{filas_tabla}</tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ========== EXPORTAR PDF ==========
        function exportarPDF() {{
            const element = document.getElementById('report-content');
            const opt = {{
                margin: [10, 10, 10, 10],
                filename: 'agrovoice_pro_reporte_' + new Date().toISOString().slice(0,19) + '.pdf',
                image: {{ type: 'jpeg', quality: 0.98 }},
                html2canvas: {{ scale: 2, useCORS: true, logging: false }},
                jsPDF: {{ unit: 'mm', format: 'a4', orientation: 'portrait' }}
            }};
            html2pdf().set(opt).from(element).save();
        }}
        
        // ========== VOZ ==========
        const synthesis = window.speechSynthesis;
        
        function hablar(texto) {{
            if(!synthesis) return;
            synthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(texto);
            utterance.lang = 'es-MX';
            utterance.rate = 0.95;
            synthesis.speak(utterance);
        }}
        
        function hablarDecision(decision, humedad) {{
            if(decision.toLowerCase().includes("regar") && !decision.toLowerCase().includes("no")) {{
                hablar("Humedad del suelo en " + humedad + " por ciento. Es momento de regar.");
            }} else {{
                hablar("Humedad del suelo en " + humedad + " por ciento. No es necesario regar.");
            }}
        }}
        
        function repetirMensaje() {{
            hablarDecision("{decision_js}", {humedad_js});
        }}
        
        // ========== GRÁFICAS ==========
        async function cargarGraficaHumedad() {{
            const res = await fetch('/api/historial');
            const data = await res.json();
            new Chart(document.getElementById('humedadChart'), {{
                type: 'line',
                data: {{
                    labels: data.fechas,
                    datasets: [{{
                        label: 'Humedad (%)',
                        data: data.humedades,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102,126,234,0.1)',
                        fill: true,
                        tension: 0.4
                    }}]
                }},
                options: {{ responsive: true, maintainAspectRatio: true }}
            }});
        }}
        
        async function cargarGraficaComparativa() {{
            const res = await fetch('/api/historial');
            const data = await res.json();
            const temps = data.humedades.map(h => 20 + (h/100)*25);
            new Chart(document.getElementById('comparativaChart'), {{
                type: 'bar',
                data: {{
                    labels: data.fechas,
                    datasets: [
                        {{ label: 'Humedad (%)', data: data.humedades, backgroundColor: '#667eea' }},
                        {{ label: 'Temperatura (C)', data: temps, backgroundColor: '#dc3545', type: 'line' }}
                    ]
                }},
                options: {{ responsive: true }}
            }});
        }}
        
        async function cargarGraficaDecisiones() {{
            const res = await fetch('/api/estadisticas');
            const data = await res.json();
            new Chart(document.getElementById('decisionesChart'), {{
                type: 'doughnut',
                data: {{
                    labels: ['Regar', 'No Regar', 'Manual'],
                    datasets: [{{
                        data: [data.regar, data.no_regar, data.manual],
                        backgroundColor: ['#28a745', '#dc3545', '#ffc107']
                    }}]
                }},
                options: {{ responsive: true }}
            }});
        }}
        
        async function cargarGraficaRiegos() {{
            const res = await fetch('/api/riegos-por-dia');
            const data = await res.json();
            new Chart(document.getElementById('riegosChart'), {{
                type: 'bar',
                data: {{
                    labels: data.dias,
                    datasets: [{{
                        label: 'Riegos',
                        data: data.cantidades,
                        backgroundColor: '#667eea'
                    }}]
                }},
                options: {{ responsive: true }}
            }});
        }}
        
        // ========== ESTADÍSTICAS ==========
        async function cargarEstadisticas() {{
            try {{
                const res = await fetch('/api/estadisticas-datos');
                const data = await res.json();
                if(data.error) {{
                    document.getElementById('estadisticas-container').innerHTML = '<div class="alert alert-warning">Sin datos</div>';
                    return;
                }}
                const html = '<div style="padding:10px">' +
                    '<p><strong>📊 Total:</strong> ' + data.total + ' registros</p>' +
                    '<p><strong>📈 Media:</strong> ' + data.media + '%</p>' +
                    '<p><strong>📉 Mediana:</strong> ' + data.mediana + '%</p>' +
                    '<p><strong>📊 Desviación:</strong> ' + data.desviacion + '%</p>' +
                    '<p><strong>🔻 Mínimo:</strong> ' + data.minimo + '%</p>' +
                    '<p><strong>🔺 Máximo:</strong> ' + data.maximo + '%</p>' +
                    '<hr><p><strong>📊 Distribución:</strong></p>' +
                    '<p>25-35%: ' + ((data.rango_25_35/data.total)*100).toFixed(1) + '% (' + data.rango_25_35 + ')</p>' +
                    '<p>35-45%: ' + ((data.rango_35_45/data.total)*100).toFixed(1) + '% (' + data.rango_35_45 + ')</p>' +
                    '<p>45-55%: ' + ((data.rango_45_55/data.total)*100).toFixed(1) + '% (' + data.rango_45_55 + ')</p>' +
                    '<p>55-65%: ' + ((data.rango_55_65/data.total)*100).toFixed(1) + '% (' + data.rango_55_65 + ')</p>' +
                    '</div>';
                document.getElementById('estadisticas-container').innerHTML = html;
            }} catch(e) {{
                document.getElementById('estadisticas-container').innerHTML = '<div class="alert alert-danger">Error</div>';
            }}
        }}
        
        // ========== PREDICCIÓN ==========
        async function cargarPrediccionManana() {{
            try {{
                const res = await fetch('/api/prediccion-manana');
                const data = await res.json();
                if(data.error) {{
                    document.getElementById('prediccion-container').innerHTML = '<div class="alert alert-warning">Sin datos</div>';
                    return;
                }}
                const color = data.decision === 'regar' ? '#28a745' : '#dc3545';
                const html = '<div style="text-align:center;padding:10px">' +
                    '<p><strong>Basado en ' + data.base_datos + ' registros</strong></p>' +
                    '<div style="display:flex;justify-content:space-around;margin:15px 0">' +
                        '<div><strong>💧 Humedad</strong><br><span style="font-size:1.8em">' + data.humedad_estimada + '%</span></div>' +
                        '<div><strong>🌡️ Temperatura</strong><br><span style="font-size:1.8em">' + data.temperatura_estimada + '°C</span></div>' +
                    '</div>' +
                    '<div style="background:' + color + ';border-radius:15px;padding:15px;margin:10px 0">' +
                        '<span style="font-size:1.5em;color:white">' + data.decision.toUpperCase() + '</span>' +
                    '</div>' +
                    '<p><strong>🎯 Probabilidad:</strong> ' + data.probabilidad + '%</p>' +
                    '</div>';
                document.getElementById('prediccion-container').innerHTML = html;
            }} catch(e) {{
                document.getElementById('prediccion-container').innerHTML = '<div class="alert alert-danger">Error</div>';
            }}
        }}
        
        // ========== RIEGO MANUAL ==========
        async function activarRiegoManual() {{
            try {{
                const res = await fetch('/regar', {{ method: 'POST' }});
                const data = await res.json();
                if(data.status === 'success') {{
                    document.getElementById('mensajeRiego').innerHTML = '<div class="alert alert-success">✅ Riego activado</div>';
                    hablar("Riego manual activado");
                    setTimeout(() => location.reload(), 2000);
                }}
            }} catch(e) {{
                console.error(e);
            }}
        }}
        
        // ========== INICIALIZACIÓN ==========
        window.addEventListener('load', () => {{
            cargarGraficaHumedad();
            cargarGraficaComparativa();
            cargarGraficaDecisiones();
            cargarGraficaRiegos();
            cargarEstadisticas();
            cargarPrediccionManana();
            setTimeout(() => {{
                hablarDecision("{decision_js}", {humedad_js});
            }}, 1500);
        }});
    </script>
</body>
</html>
    """

# ==================== APIs ====================

@app.get("/api/historial")
async def api_historial():
    try:
        bd = GestorBD()
        registros = list(bd.db['registros'].find({}, {'_id': 0, 'fecha': 1, 'humedad_suelo': 1}).sort('fecha', -1).limit(24))
        registros.reverse()
        datos = {"fechas": [], "humedades": []}
        for reg in registros:
            fecha = reg.get('fecha')
            if fecha and hasattr(fecha, 'strftime'):
                datos["fechas"].append(fecha.strftime("%H:%M"))
            else:
                datos["fechas"].append("N/A")
            datos["humedades"].append(reg.get('humedad_suelo', 0))
        return datos
    except:
        return {"fechas": [], "humedades": []}

@app.get("/api/estadisticas")
async def api_estadisticas():
    try:
        bd = GestorBD()
        return {
            "regar": bd.db['registros'].count_documents({"decision": "regar"}),
            "no_regar": bd.db['registros'].count_documents({"decision": "no_regar"}),
            "manual": bd.db['registros'].count_documents({"decision": "regar_manual"})
        }
    except:
        return {"regar": 0, "no_regar": 0, "manual": 0}

@app.get("/api/riegos-por-dia")
async def api_riegos_por_dia():
    try:
        bd = GestorBD()
        pipeline = [
            {"$group": {"_id": {"$dateToString": {"format": "%d/%m", "date": "$fecha"}}, "count": {"$sum": 1}}},
            {"$sort": {"_id": -1}},
            {"$limit": 7}
        ]
        resultados = list(bd.db['registros'].aggregate(pipeline))
        resultados.reverse()
        return {"dias": [r["_id"] for r in resultados], "cantidades": [r["count"] for r in resultados]}
    except:
        return {"dias": [], "cantidades": []}

@app.get("/api/estadisticas-datos")
async def api_estadisticas_datos():
    try:
        bd = GestorBD()
        sensores = list(bd.db['sensores'].find({}, {'_id': 0, 'humedad_suelo': 1}))
        humedades = [s['humedad_suelo'] for s in sensores if 'humedad_suelo' in s]
        if not humedades:
            return {"error": "No hay datos"}
        return {
            "media": round(statistics.mean(humedades), 1),
            "mediana": round(statistics.median(humedades), 1),
            "desviacion": round(statistics.stdev(humedades), 1),
            "minimo": round(min(humedades), 1),
            "maximo": round(max(humedades), 1),
            "total": len(humedades),
            "rango_25_35": len([h for h in humedades if 25 <= h <= 35]),
            "rango_35_45": len([h for h in humedades if 35 <= h <= 45]),
            "rango_45_55": len([h for h in humedades if 45 <= h <= 55]),
            "rango_55_65": len([h for h in humedades if 55 <= h <= 65])
        }
    except:
        return {"error": "Error"}

@app.get("/api/prediccion-manana")
async def api_prediccion_manana():
    try:
        bd = GestorBD()
        sensores = list(bd.db['sensores'].find({}, {'_id': 0, 'humedad_suelo': 1, 'temperatura': 1}).sort('fecha', -1).limit(30))
        if not sensores:
            return {"error": "No hay datos"}
        humedades = [s['humedad_suelo'] for s in sensores]
        temperaturas = [s['temperatura'] for s in sensores]
        humedad_estimada = round(sum(humedades) / len(humedades), 1)
        temperatura_estimada = round(sum(temperaturas) / len(temperaturas), 1)
        decision = "regar" if humedad_estimada < 30 else "no_regar"
        if humedad_estimada < 25:
            probabilidad = 95
        elif humedad_estimada < 30:
            probabilidad = 85
        elif humedad_estimada < 35:
            probabilidad = 60
        elif humedad_estimada < 45:
            probabilidad = 30
        else:
            probabilidad = 10
        return {
            "humedad_estimada": humedad_estimada,
            "temperatura_estimada": temperatura_estimada,
            "decision": decision,
            "probabilidad": probabilidad,
            "base_datos": len(humedades)
        }
    except:
        return {"error": "Error"}

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        bd = GestorBD()
        ia = ModeloRiego()
        ia.cargar_o_crear()
        clima = obtener_clima_real() or {"temperatura_ambiente": 28.0, "humedad_ambiente": 45.0, "descripcion": "Cielo despejado"}
        humedad_suelo = round(random.uniform(15, 55), 1)
        decision = ia.predecir(humedad_suelo, clima["temperatura_ambiente"])
        historial = []
        try:
            if hasattr(bd, 'db'):
                for reg in bd.db['registros'].find({}).sort('fecha', -1).limit(20):
                    fecha = reg.get('fecha')
                    fecha_str = fecha.strftime("%d/%m/%Y %H:%M") if fecha and hasattr(fecha, 'strftime') else "Sin fecha"
                    historial.append({"fecha": fecha_str, "humedad_suelo": reg.get('humedad_suelo', 'N/A'), "temperatura": reg.get('temperatura', 'N/A'), "decision": reg.get('decision', 'N/A')})
        except:
            pass
        context = {
            "humedad_suelo": float(humedad_suelo),
            "temp": float(clima.get("temperatura_ambiente", 25.0)),
            "hum_amb": float(clima.get("humedad_ambiente", 45.0)),
            "descripcion": str(clima.get("descripcion", "")),
            "decision": str(decision) if decision else "Sin decision",
            "historial": historial,
            "now": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        }
        return HTMLResponse(content=generar_html(context))
    except Exception as e:
        return HTMLResponse(content=f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)

@app.post("/regar")
async def activar_riego_manual():
    try:
        bd = GestorBD()
        if hasattr(bd, 'db'):
            bd.db['registros'].insert_one({"fecha": datetime.now(), "humedad_suelo": 0, "temperatura": 0, "decision": "regar_manual", "tipo": "manual"})
        return {"status": "success"}
    except:
        return {"status": "error"}

if __name__ == "__main__":
    print("🚀 AgroVoice Pro Web en http://localhost:8000")
    print("📄 Boton PDF habilitado")
    uvicorn.run("app_web:app", host="0.0.0.0", port=8000, reload=True)