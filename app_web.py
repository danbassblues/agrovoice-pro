# Este es el app_web.py completo y corregido
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn
import sys
import os
from datetime import datetime
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src_core.ia_modelo import ModeloRiego
from src_core.base_datos import GestorBD
from src_core.apis_externas import obtener_clima_real

app = FastAPI(title="AgroVoice Pro")
app.mount("/static", StaticFiles(directory="static"), name="static")

def generar_html(context):
    """Genera el HTML con los datos del historial incluidos"""
    
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
            max-height: 400px;
            overflow-y: auto;
        }}
        .table {{
            background: white;
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
    </script>
</body>
</html>
    """

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
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


if __name__ == "__main__":
    print("🚀 AgroVoice Pro Web → http://localhost:8000")
    print("📊 Mostrando historial desde MongoDB")
    uvicorn.run("app_web:app", host="0.0.0.0", port=8000, reload=True)