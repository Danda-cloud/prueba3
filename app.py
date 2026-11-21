"""
SecureDev - Aplicación Flask (versión corregida)
=================================================
Corrige la vulnerabilidad XSS reflejado (CWE-79) encontrada en el
código original (ver app_vulnerable.py) en el endpoint /hello, y
expone métricas en /metrics para que Prometheus/Grafana puedan
monitorear el servicio en tiempo real, incluyendo un contador de
peticiones con patrones típicos de intento de inyección.

Correcciones aplicadas respecto al código original:
  1. El parámetro 'name' se escapa con markupsafe.escape() antes de
     insertarse en la respuesta HTML -> neutraliza <script>, onerror=,
     etc. (mitiga CWE-79, hallazgo de Bandit/OWASP ZAP).
  2. El modo debug de Flask/Werkzeug queda desactivado por defecto
     (FLASK_DEBUG=0). Un debugger interactivo expuesto en producción
     permite ejecución remota de código (segunda vulnerabilidad
     detectada durante la revisión de seguridad).
  3. Se agregan métricas (Counter) para poder observar en Grafana
     cuántas peticiones a /hello contienen caracteres sospechosos de
     un intento de XSS, lo que permite detectar un "incidente" en
     tiempo real aunque el ataque ya esté mitigado en el código.
"""
import os
from flask import Flask, request
from markupsafe import escape
from prometheus_client import Summary, Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_TIME = Summary(
    'request_processing_seconds', 'Tiempo de procesamiento de la petición'
)
HELLO_REQUESTS_TOTAL = Counter(
    'hello_requests_total', 'Total de peticiones recibidas en /hello'
)
HELLO_SUSPICIOUS_REQUESTS_TOTAL = Counter(
    'hello_suspicious_requests_total',
    'Peticiones a /hello con payload compatible con un intento de XSS'
)


def _parece_intento_de_inyeccion(valor: str) -> bool:
    """Heurística simple para detectar un posible intento de XSS en 'name'."""
    v = valor.lower()
    return any(marca in v for marca in ('<', '>', 'script', 'onerror=', 'javascript:'))


@app.route('/metrics')
def metrics():
    """Endpoint que consume Prometheus (ver prometheus.yml, job 'flask-app')."""
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}


@app.route('/hello')
@REQUEST_TIME.time()
def hello():
    """
    Endpoint corregido. PoC del código original ya NO funciona:
        /hello?name=<script>alert(1)</script>  ->  se devuelve escapado,
        el navegador muestra el texto literal, no ejecuta el script.
    """
    name = request.args.get('name', '')
    HELLO_REQUESTS_TOTAL.inc()

    if _parece_intento_de_inyeccion(name):
        HELLO_SUSPICIOUS_REQUESTS_TOTAL.inc()

    return f"Hello, {escape(name)}!"


@app.route('/')
def index():
    return "SecureDev - app corregida. Ver /hello?name=... y /metrics."


if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)
