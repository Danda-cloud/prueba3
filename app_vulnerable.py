# ============================================================
# CÓDIGO ORIGINAL PROPORCIONADO POR SECUREDEV — NO SEGURO
# Se conserva tal cual (fuente: Guía 3.2.2 / 3.3.2 / 3.5.2, OCY1102)
# únicamente como evidencia de auditoría. NO se despliega en producción.
#
# Vulnerabilidad: Cross-Site Scripting (XSS) Reflejado — CWE-79
# El parámetro 'name' se inserta sin escapar en la respuesta HTML,
# por lo que cualquier HTML/JavaScript enviado en la URL se ejecuta
# en el navegador de la víctima. PoC:
#   http://localhost:5000/hello?name=<script>alert(1)</script>
#
# Ver app.py para la versión corregida que sí se despliega.
# ============================================================
from flask import Flask, request

app = Flask(__name__)

@app.route('/hello')
def hello():
    name = request.args.get('name')
    return f"Hello, {name}!"

if __name__ == '__main__':
    app.run(debug=True)
