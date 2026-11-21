# SecureDev — Parcial 3 OCY1102 (DevSecOps / CI-CD)

Este proyecto implementa el pipeline de CI/CD pedido en la Evaluación Parcial 3
("Explotación y Mitigación de Vulnerabilidades Web"). Todo el código y la
configuración sale de las guías 3.1 a 3.5 que ya trabajaste (mismo app Flask
`/hello`, mismo patrón de Jenkinsfile, mismo docker-compose de Prometheus/Grafana).

## Archivos

| Archivo | Qué es |
|---|---|
| `app_vulnerable.py` | Código original de SecureDev, **sin corregir** (evidencia). |
| `app.py` | Código corregido: XSS mitigado + métricas para Prometheus. |
| `requirements-vulnerable-ORIGINAL.txt` | Dependencias originales (Flask 1.1.2, requests 2.24.0) — vulnerables. |
| `requirements.txt` | Dependencias parchadas. |
| `tests.py` | Pruebas unitarias + prueba de seguridad (regresión XSS). |
| `Dockerfile` | Imagen de la app. |
| `Jenkinsfile` | Pipeline completo: Build → Dependency Management → Test → Analyze → Deploy → Security Test. |
| `docker-compose.yml` + `prometheus.yml` | Levanta la app + Prometheus + Grafana juntos. |
| `grafana-dashboard-securedev.json` | Dashboard listo para importar en Grafana (3 paneles). |

## Vulnerabilidad identificada y corregida

- **Tipo:** Cross-Site Scripting (XSS) Reflejado — CWE-79.
- **Dónde:** `app_vulnerable.py`, endpoint `/hello`, parámetro `name`, insertado
  sin escapar en el HTML de respuesta.
- **PoC:** `http://localhost:5000/hello?name=<script>alert(1)</script>`
- **Corrección:** `markupsafe.escape(name)` antes de insertar el valor en la
  respuesta (`app.py`). Se agregó además `tests.py::test_hello_mitiga_xss_reflejado`
  para que el pipeline vuelva a fallar automáticamente si alguien rompe el fix.
- **Vulnerabilidad secundaria:** `debug=True` en el código original expone el
  debugger interactivo de Werkzeug (ejecución remota de código). Corregido con
  `FLASK_DEBUG=0` por defecto.
- **Dependencias vulnerables identificadas:**
  - `Flask==1.1.2` → CVE-2023-30861 (fuga de cookie de sesión). Parchado a `3.1.3`.
  - `requests==2.24.0` → CVE-2023-32681 (fuga de header `Proxy-Authorization`
    en redirecciones HTTPS). Parchado a `2.34.2`.
  - Confirmado con herramientas reales (no simulado):
    - `pip-audit -r requirements-vulnerable-ORIGINAL.txt` → **35 vulnerabilidades
      conocidas** en 4 paquetes (Flask, requests y sus dependencias transitivas
      `idna`/`urllib3`).
    - `pip-audit -r requirements.txt` (parchado) → **"No known vulnerabilities
      found"**.
    - `bandit app_vulnerable.py` → `B201 flask_debug_true` (**High**, CWE-94):
      confirma el debugger expuesto.
    - `bandit app.py` (corregido) → solo queda `B104` (Medium, "bind a todas
      las interfaces"), aceptado porque la app corre dentro de un contenedor
      Docker aislado (no expuesto directamente en la interfaz del host).

## Cómo ejecutarlo (orden recomendado)

```bash
# 1) Build de la imagen
docker build -t flask-app-securedev .

# 2) Pruebas y análisis locales (opcional, el Jenkinsfile ya lo hace)
pip install pipenv
pipenv install -r requirements.txt
pipenv run pytest tests.py -v
pipenv run pip install bandit
pipenv run bandit -r app.py

# 3) Monitoreo: levantar app + Prometheus + Grafana juntos
docker-compose up -d
#   App:        http://localhost:5000/hello?name=Jenkins
#   Prometheus: http://localhost:9090/targets  (job "flask-app" debe estar UP)
#   Grafana:    http://localhost:3000  (admin/admin)
#   -> En Grafana: Connections > Data sources > Add > Prometheus
#      URL = http://prometheus:9090 > Save & Test
#   -> Dashboards > Import > subir grafana-dashboard-securedev.json
#      (selecciona tu data source Prometheus cuando lo pida)

# 4) Pipeline en Jenkins: crea un job "Pipeline script from SCM" apuntando
#    a este repo (igual que en la Formativa 3) y ejecútalo. El Jenkinsfile
#    ya incluye las 6 etapas pedidas.
```

## CHECKLIST DE CAPTURAS — mapeado 1 a 1 a "Desarrollo EV3.docx"

Sigue este orden; cada punto corresponde a un "(Pegar Pantallazos)" del documento.

### Bloque 1 — Pipeline CI/CD (Build, Test, Deploy)
1. `docker ps` con Jenkins corriendo + panel inicial de Jenkins (`localhost:8080`).
2. Repositorio Git con `app.py`, `app_vulnerable.py`, `Jenkinsfile`, `requirements.txt` subidos.
3. Job de Jenkins configurado como "Pipeline script from SCM" apuntando al repo.
4. Pipeline corriendo (Stage View) con las 6 etapas visibles.
5. Pipeline finalizado (todas las etapas en verde o con el detalle de qué falló).

### Bloque 2 — Vulnerabilidad: identificación y corrección
6. `app_vulnerable.py` abierto mostrando el código inseguro (línea `return f"Hello, {name}!"`).
7. Prueba manual del XSS **contra el código original**: despliega `app_vulnerable.py`
   temporalmente (`python app_vulnerable.py`) y entra a
   `http://localhost:5000/hello?name=<script>alert(1)</script>` — debe
   aparecer el popup de JavaScript. Captura el popup.
8. Log de la etapa **Analyze** (Bandit) mostrando el hallazgo en `app.py` corregido
   (o en una corrida contra `app_vulnerable.py` si quieres mostrar el "antes/después").
9. `app.py` corregido abierto, mostrando `escape(name)`.
10. Repite el paso 7 pero contra la app **corregida**: mismo payload,
    ahora el navegador muestra el texto plano (sin ejecutar el script).
11. Resultado de `pipenv run pytest tests.py -v` con
    `test_hello_mitiga_xss_reflejado` en verde.

### Bloque 3 — Pruebas automatizadas de seguridad (OWASP ZAP)
12. Comando de ZAP corriendo en la etapa **Security Test** del pipeline (log de Jenkins).
13. `zap-report.html` generado, **primera corrida contra `app_vulnerable.py`**
    desplegado → debe listar la alerta de XSS reflejado.
14. `zap-report.html`, **segunda corrida contra `app.py`** (corregido) desplegado
    → la alerta de XSS ya no debería aparecer (o aparece solo como informativa).
15. Breve texto tuyo (puede ir directo en el Word) indicando qué vulnerabilidad
    reportó ZAP y qué acción se tomó — ya está redactado en el documento, revísalo
    y ajústalo con lo que realmente te arroje tu escaneo.

### Bloque 4 — Monitorización con Grafana
16. `docker-compose up -d` corriendo + `docker ps` mostrando app, prometheus y grafana.
17. `http://localhost:9090/targets` con el job `flask-app` en estado **UP**.
18. Grafana con el Data Source Prometheus configurado (Save & Test en verde).
19. Dashboard importado (`grafana-dashboard-securedev.json`) mostrando los 3 paneles
    con datos (aunque sea en 0).
20. **Simulación de incidente en tiempo real:** desde una terminal, ejecuta varias
    veces `curl "http://localhost:5000/hello?name=<script>alert(1)</script>"`
    y observa en Grafana cómo sube el panel "Peticiones sospechosas a /hello" —
    captura el dashboard con el pico. Esto documenta la detección del intento
    de ataque y confirma que, aunque llega el payload, la respuesta ya no lo
    ejecuta (mitigación activa + visibilidad).

Con estas 20 capturas cubres cada "(Pegar Pantallazos)" del documento oficial.
