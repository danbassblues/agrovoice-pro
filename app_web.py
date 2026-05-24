# app_web.py - AgroVoice Pro con Sistema de Voz, 4 Gráficas, Estadísticas y Predicción
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
print("¿Existe config.py?", os.path.exists("config.py"))
# =================================

# Asegurar que el directorio actual está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Intentar importar config
try:
    import config
    print("✅ config.py importado correctamente")
except Exception as e:
    print(f"❌ Error importando config: {e}")
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
    """Genera el HTML con 4 gráficas, sistema de voz, estadísticas y predicción"""
    
    # Construir filas de la tabla del historial
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
    
    # Variables para inyección segura en JavaScript
    decision_js = context['decision'].lower().replace('"', '\\"')
    humedad_js = context['humedad_suelo']
    
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
            position: relative;
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
            position: relative;
        }}
        .grafica-titulo {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
            text-align: center;
        }}
        .btn-voz {{
            background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
            border: none;
            padding: 8px 20px;
            border-radius: 25px;
            color: white;
            font-size: 0.9em;
            margin-top: 10px;
            cursor: pointer;
            transition: transform 0.2s;
        }}
        .btn-voz:hover {{
            transform: scale(1.05);
        }}
        .badge-voz {{
            position: absolute;
            top: 10px;
            right: 15px;
            background: #38ef7d;
            color: #000;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: bold;
        }}
        .stat-number {{
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .prediccion-box {{
            text-align: center;
            padding: 15px;
            border-radius: 15px;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="dashboard-title">
            <h1>🌾 AgroVoice Pro</h1>
            <p>Sistema de Riego Inteligente con Asistente de Voz</p>
            <small>Última actualización: {context['now']}</small>
            <span class="badge-voz">🔊 Voz Activa</span>
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

        <!-- GRÁFICAS 2 y 3 -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🔄 Comparativa: Humedad vs Temperatura</div>
                        <div class="chart-container">
                            <canvas id="comparativaChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🎯 Distribución de Decisiones</div>
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
                        <div class="chart-container">
                            <canvas id="riegosChart"></canvas>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- 🆕 NUEVA SECCIÓN: ESTADÍSTICAS Y PREDICCIÓN -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">📊 Distribución de Datos Históricos</div>
                        <div id="estadisticas-container">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Cargando...</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-body">
                        <div class="grafica-titulo">🔮 Predicción para Mañana</div>
                        <div id="prediccion-container">
                            <div class="text-center">
                                <div class="spinner-border text-primary" role="status">
                                    <span class="visually-hidden">Cargando...</span>
                                </div>
                            </div>
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
                        <button class="btn-voz" onclick="repetirMensaje()">
                            🔊 Repetir mensaje
                        </button>
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
                            <table class="table table-striped table-sm">
                                <thead>
                                    <tr><th>Fecha/Hora</th><th>Humedad</th><th>Temperatura</th><th>Decisión</th></tr>
                                </thead>
                                <tbody>
                                    {filas_tabla}
                                </tbody>
                            <table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // ========== FUNCIONES DE VOZ ==========
        const synthesis = window.speechSynthesis;
        
        function hablar(texto) {{
            if (!synthesis) {{
                console.log("⚠️ Web Speech API no soportada");
                return;
            }}
            synthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(texto);
            utterance.lang = 'es-MX';
            utterance.rate = 0.95;
            utterance.pitch = 1.0;
            utterance.volume = 1.0;
            synthesis.speak(utterance);
            console.log("🔊 Hablando:", texto);
        }}
        
        function hablarDecision(decision, humedad) {{
            if (!decision) return;
            const decisionLower = decision.toLowerCase();
            let mensaje = "";
            if (decisionLower.includes("regar") && !decisionLower.includes("no")) {{
                mensaje = `Humedad del suelo en ${{humedad}} por ciento. Es momento de regar.`;
            }} else {{
                mensaje = `Humedad del suelo en ${{humedad}} por ciento. No es necesario regar.`;
            }}
            hablar(mensaje);
        }}
        
        function alertaCritica(humedad) {{
            if (humedad === undefined) return;
            if (humedad < 25) {{
                hablar(`¡Alerta crítica! La humedad del suelo está en ${{humedad}} por ciento. Active el riego de inmediato.`);
            }} else if (humedad < 35) {{
                hablar(`Atención: la humedad del suelo está en ${{humedad}} por ciento. Considere regar pronto.`);
            }}
        }}
        
        function repetirMensaje() {{
            hablarDecision("{decision_js}", {humedad_js});
        }}
        
        function silenciarVoz() {{
            if (synthesis) {{
                synthesis.cancel();
            }}
        }}

        // ========== GRÁFICA 1: Tendencia de Humedad ==========
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
                            pointRadius: 5
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        scales: {{ 
                            y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Humedad (%)' }} }},
                            x: {{ title: {{ display: true, text: 'Hora' }} }} 
                        }}
                    }}
                }});
            }} catch(e) {{ console.error("Error gráfica humedad:", e); }}
        }}
        
        // ========== GRÁFICA 2: Comparativa ==========
        async function cargarGraficaComparativa() {{
            try {{
                const response = await fetch('/api/historial');
                const data = await response.json();
                const temperaturas = data.humedades.map(h => 20 + (h / 100) * 25);
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
                        scales: {{
                            y: {{ title: {{ display: true, text: 'Humedad (%)' }}, beginAtZero: true, max: 100 }},
                            y1: {{ 
                                position: 'right', 
                                title: {{ display: true, text: 'Temperatura (°C)' }}, 
                                beginAtZero: true, 
                                max: 50, 
                                grid: {{ drawOnChartArea: false }} 
                            }}
                        }}
                    }}
                }});
            }} catch(e) {{ console.error("Error gráfica comparativa:", e); }}
        }}
        
        // ========== GRÁFICA 3: Decisiones (Pastel) ==========
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
                            data: [data.regar || 0, data.no_regar || 0, data.manual || 0],
                            backgroundColor: ['#28a745', '#dc3545', '#ffc107'],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        plugins: {{
                            legend: {{ position: 'bottom' }}
                        }}
                    }}
                }});
            }} catch(e) {{ console.error("Error gráfica decisiones:", e); }}
        }}
        
        // ========== GRÁFICA 4: Riegos por día ==========
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
                            backgroundColor: 'rgba(102, 126, 234, 0.7)',
                            borderColor: '#667eea',
                            borderWidth: 2,
                            borderRadius: 10
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: true,
                        scales: {{ 
                            y: {{ beginAtZero: true, title: {{ display: true, text: 'Riegos' }}, ticks: {{ stepSize: 1 }} }} 
                        }}
                    }}
                }});
            }} catch(e) {{ console.error("Error gráfica riegos:", e); }}
        }}
        
        // ========== ESTADÍSTICAS DE DATOS ==========
        async function cargarEstadisticas() {{
            try {{
                const response = await fetch('/api/estadisticas-datos');
                const data = await response.json();
                
                if (data.error) {{
                    document.getElementById('estadisticas-container').innerHTML = 
                        '<div class="alert alert-warning">No hay datos disponibles</div>';
                    return;
                }}
                
                const total = data.total;
                const p25_35 = ((data.rango_25_35 / total) * 100).toFixed(1);
                const p35_45 = ((data.rango_35_45 / total) * 100).toFixed(1);
                const p45_55 = ((data.rango_45_55 / total) * 100).toFixed(1);
                const p55_65 = ((data.rango_55_65 / total) * 100).toFixed(1);
                
                const html = `
                    <div style="margin-bottom: 15px;">
                        <div style="background: #e9ecef; border-radius: 10px; margin-bottom: 8px;">
                            <div style="background: #28a745; width: ${p25_35}%; border-radius: 10px; padding: 5px; color: white;">25-35%: ${p25_35}%</div>
                        </div>
                        <div style="background: #e9ecef; border-radius: 10px; margin-bottom: 8px;">
                            <div style="background: #17a2b8; width: ${p35_45}%; border-radius: 10px; padding: 5px; color: white;">35-45%: ${p35_45}%</div>
                        </div>
                        <div style="background: #e9ecef; border-radius: 10px; margin-bottom: 8px;">
                            <div style="background: #ffc107; width: ${p45_55}%; border-radius: 10px; padding: 5px; color: #333;">45-55%: ${p45_55}%</div>
                        </div>
                        <div style="background: #e9ecef; border-radius: 10px; margin-bottom: 8px;">
                            <div style="background: #dc3545; width: ${p55_65}%; border-radius: 10px; padding: 5px; color: white;">55-65%: ${p55_65}%</div>
                        </div>
                    </div>
                    <table class="table table-sm">
                        <tr><td>📊 Total registros</td><td><strong>${data.total}</strong></td></tr>
                        <tr><td>📈 Media de humedad</td><td><strong>${data.media}%</strong></td></tr>
                        <tr><td>📉 Mediana</td><td><strong>${data.mediana}%</strong></td></tr>
                        <tr><td>📊 Desviación estándar</td><td><strong>${data.desviacion}%</strong></td></tr>
                        <tr><td>🔻 Mínimo</td><td><strong>${data.minimo}%</strong></td></tr>
                        <tr><td>🔺 Máximo</td><td><strong>${data.maximo}%</strong></td></tr>
                    </table>
                `;
                document.getElementById('estadisticas-container').innerHTML = html;
            }} catch(e) {{
                console.error("Error cargando estadisticas:", e);
            }}
        }}
        
        // ========== PREDICCIÓN PARA MAÑANA ==========
        async function cargarPrediccionManana() {{
            try {{
                const response = await fetch('/api/prediccion-manana');
                const data = await response.json();
                
                if (data.error) {{
                    document.getElementById('prediccion-container').innerHTML = 
                        '<div class="alert alert-warning">No hay datos suficientes para predicción</div>';
                    return;
                }}
                
                const colorDecision = data.decision === 'regar' ? '#28a745' : '#dc3545';
                const iconoDecision = data.decision === 'regar' ? '🌊' : '✅';
                
                const html = `
                    <div style="text-align: center;">
                        <div style="font-size: 0.9em; margin-bottom: 15px; color: #666;">
                            📍 Basado en ${data.base_datos} registros recientes
                        </div>
                        <div style="display: flex; justify-content: space-around; margin-bottom: 20px;">
                            <div>
                                <div>💧 Humedad estimada</div>
                                <div style="font-size: 2em; font-weight: bold;">${data.humedad_estimada}%</div>
                            </div>
                            <div>
                                <div>🌡️ Temperatura</div>
                                <div style="font-size: 2em; font-weight: bold;">${data.temperatura_estimada}°C</div>
                            </div>
                        </div>
                        <div style="background: ${colorDecision}; border-radius: 15px; padding: 15px; margin: 15px 0;">
                            <div style="font-size: 1.5em; font-weight: bold; color: white;">
                                ${iconoDecision} ${data.decision.toUpperCase()}
                            </div>
                        </div>
                        <div style="margin-top: 15px;">
                            <div style="font-size: 0.9em; margin-bottom: 5px;">🎯 Probabilidad de la predicción</div>
                            <div style="position: relative; height: 30px; background: #e9ecef; border-radius: 15px; margin: 10px 0;">
                                <div style="position: absolute; width: ${data.probabilidad}%; background: ${colorDecision}; height: 30px; border-radius: 15px; text-align: center; color: white; line-height: 30px;">
                                    ${data.probabilidad}%
                                </div>
                            </div>
                            <small class="text-muted">Basado en tendencia histórica de 30 días</small>
                        </div>
                    </div>
                `;
                document.getElementById('prediccion-container').innerHTML = html;
            }} catch(e) {{
                console.error("Error cargando prediccion:", e);
            }}
        }}
        
        // ========== RIEGO MANUAL CON VOZ ==========
        async function activarRiegoManual() {{
            try {{
                const response = await fetch('/regar', {{ method: 'POST' }});
                const data = await response.json();
                const mensajeDiv = document.getElementById('mensajeRiego');
                if (data.status === 'success') {{
                    mensajeDiv.innerHTML = '<div class="alert alert-success">✅ Riego activado correctamente</div>';
                    hablar("Riego manual activado. El sistema está regando el cultivo.");
                    setTimeout(() => location.reload(), 3000);
                }} else {{
                    mensajeDiv.innerHTML = '<div class="alert alert-danger">❌ Error al activar el riego</div>';
                    hablar("Error al activar el riego manual.");
                }}
            }} catch (error) {{
                console.error('Error:', error);
                document.getElementById('mensajeRiego').innerHTML = '<div class="alert alert-danger">❌ Error de conexión</div>';
                hablar("Error de conexión con el servidor.");
            }}
        }}
        
        // ========== INICIALIZACIÓN AL CARGAR ==========
        window.addEventListener('load', () => {{
            cargarGraficaHumedad();
            cargarGraficaComparativa();
            cargarGraficaDecisiones();
            cargarGraficaRiegos();
            cargarEstadisticas();
            cargarPrediccionManana();
            
            setTimeout(() => {{
                console.log("🎤 Iniciando asistente de voz...");
                hablarDecision("{decision_js}", {humedad_js});
                alertaCritica({humedad_js});
            }}, 2000);
        }});
        
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                silenciarVoz();
            }}
        }});
        
        window.addEventListener('beforeunload', () => {{
            if (synthesis) {{
                synthesis.cancel();
            }}
        }});
    </script>
</body>
</html>
    """

# ==================== APIS PARA GRÁFICAS ====================

@app.get("/api/historial")
async def api_historial():
    """API para datos de humedad"""
    try:
        bd = GestorBD()
        registros = list(bd.db['registros']
                        .find({}, {'_id': 0, 'fecha': 1, 'humedad_suelo': 1})
                        .sort('fecha', -1)
                        .limit(24))
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
    except Exception as e:
        print(f"Error en API historial: {e}")
        return {"fechas": [], "humedades": []}


@app.get("/api/estadisticas")
async def api_estadisticas():
    """API para estadísticas de decisiones"""
    try:
        bd = GestorBD()
        total_regar = bd.db['registros'].count_documents({"decision": "regar"})
        total_no_regar = bd.db['registros'].count_documents({"decision": "no_regar"})
        total_manual = bd.db['registros'].count_documents({"decision": "regar_manual"})
        return {"regar": total_regar, "no_regar": total_no_regar, "manual": total_manual}
    except Exception as e:
        print(f"Error en estadisticas: {e}")
        return {"regar": 0, "no_regar": 0, "manual": 0}


@app.get("/api/riegos-por-dia")
async def api_riegos_por_dia():
    """API para riegos agrupados por día"""
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
    except Exception as e:
        print(f"Error en riegos-por-dia: {e}")
        return {"dias": [], "cantidades": []}


@app.get("/api/estadisticas-datos")
async def api_estadisticas_datos():
    """API para estadísticas descriptivas de los datos históricos"""
    try:
        bd = GestorBD()
        # Obtener todos los datos de humedad
        sensores = list(bd.db['sensores'].find({}, {'_id': 0, 'humedad_suelo': 1}))
        
        humedades = [s['humedad_suelo'] for s in sensores if 'humedad_suelo' in s]
        
        if not humedades:
            return {"error": "No hay datos"}
        
        import statistics
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
    except Exception as e:
        print(f"Error en estadisticas-datos: {e}")
        return {"error": str(e)}


@app.get("/api/prediccion-manana")
async def api_prediccion_manana():
    """API para predecir si regar mañana basado en datos históricos"""
    try:
        bd = GestorBD()
        
        # Obtener últimos 30 días de datos
        sensores = list(bd.db['sensores']
                       .find({}, {'_id': 0, 'humedad_suelo': 1, 'temperatura': 1})
                       .sort('fecha', -1)
                       .limit(30))
        
        if not sensores:
            return {"error": "No hay datos suficientes"}
        
        # Calcular promedios recientes
        humedades_recientes = [s['humedad_suelo'] for s in sensores]
        temperaturas_recientes = [s['temperatura'] for s in sensores]
        
        # Estimación para mañana (promedio)
        humedad_estimada = round(sum(humedades_recientes) / len(humedades_recientes), 1)
        temperatura_estimada = round(sum(temperaturas_recientes) / len(temperaturas_recientes), 1)
        
        # Decisión basada en umbral
        decision = "regar" if humedad_estimada < 30 else "no_regar"
        
        # Calcular tendencia (diferencia entre primer y último registro)
        tendencia = humedades_recientes[0] - humedades_recientes[-1] if len(humedades_recientes) > 1 else 0
        
        # Calcular probabilidad basada en humedad estimada y tendencia
        if humedad_estimada < 25:
            probabilidad = 95
        elif humedad_estimada < 30:
            probabilidad = 85
        elif humedad_estimada < 35:
            probabilidad = 60 if tendencia < 0 else 40
        elif humedad_estimada < 45:
            probabilidad = 30 if tendencia < 0 else 20
        else:
            probabilidad = 10
        
        return {
            "humedad_estimada": humedad_estimada,
            "temperatura_estimada": temperatura_estimada,
            "decision": decision,
            "probabilidad": probabilidad,
            "base_datos": len(humedades_recientes),
            "tendencia": round(tendencia, 1)
        }
    except Exception as e:
        print(f"Error en prediccion-manana: {e}")
        return {"error": str(e)}


# ==================== ENDPOINTS PRINCIPALES ====================

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
        
        humedad_suelo = round(random.uniform(15, 55), 1)
        decision = ia.predecir(humedad_suelo, clima["temperatura_ambiente"])

        historial = []
        try:
            if hasattr(bd, 'db'):
                registros = bd.db['registros'].find({}).sort('fecha', -1).limit(20)
                for reg in registros:
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
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", status_code=500)


@app.post("/regar")
async def activar_riego_manual():
    try:
        bd = GestorBD()
        if hasattr(bd, 'db'):
            registro = {
                "fecha": datetime.now(),
                "humedad_suelo": 0,
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


if __name__ == "__main__":
    print("🚀 AgroVoice Pro Web → http://localhost:8000")
    print("🔊 Sistema de voz integrado")
    print("📊 4 gráficas profesionales activas")
    print("📈 Sección de estadísticas y predicción agregada")
    uvicorn.run("app_web:app", host="0.0.0.0", port=8000, reload=True)