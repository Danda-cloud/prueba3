"""
Pruebas automatizadas de la etapa 'Test' del pipeline.
Incluye una prueba de seguridad de regresión: si alguien vuelve a
romper el escape de /hello, esta prueba debe fallar y detener el
pipeline antes de llegar a Deploy.
"""
import pytest
from app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c


def test_hello_funcional(client):
    """Caso funcional básico: la app responde correctamente."""
    resp = client.get('/hello?name=Mundo')
    assert resp.status_code == 200
    assert b'Hello, Mundo!' in resp.data


def test_hello_sin_parametro(client):
    """No debe romperse si no se envía 'name'."""
    resp = client.get('/hello')
    assert resp.status_code == 200


def test_hello_mitiga_xss_reflejado(client):
    """
    PRUEBA DE SEGURIDAD (regresión XSS - CWE-79).
    Un payload de XSS reflejado no debe aparecer sin escapar en la
    respuesta. Si esta prueba falla, la vulnerabilidad volvió.
    """
    payload = "<script>alert(1)</script>"
    resp = client.get(f'/hello?name={payload}')
    body = resp.data.decode('utf-8')
    assert '<script>alert(1)</script>' not in body
    assert '&lt;script&gt;' in body


def test_metrics_disponible(client):
    """El endpoint de métricas debe responder para que Prometheus pueda leerlo."""
    resp = client.get('/metrics')
    assert resp.status_code == 200
