"""Tests de observabilidad: /metrics, request-id y manejo de errores."""
import re

from app import create_app


def test_metrics_endpoint_expone_prometheus():
    client = create_app().test_client()

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    cuerpo = response.get_data(as_text=True)
    assert "flask_http_request_total" in cuerpo
    assert "citibike_dashboard_info" in cuerpo


def test_request_id_se_genera_y_se_propaga():
    client = create_app().test_client()

    response = client.get("/health")

    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    assert re.fullmatch(r"[0-9a-f]{32}", request_id)


def test_request_id_entrante_se_respeta():
    client = create_app().test_client()

    response = client.get("/health", headers={"X-Request-ID": "prueba-123"})

    assert response.headers["X-Request-ID"] == "prueba-123"


def test_error_http_conserva_su_codigo():
    client = create_app().test_client()

    response = client.get("/ruta-inexistente")

    assert response.status_code == 404
    assert response.headers.get("X-Request-ID")


def test_error_no_controlado_devuelve_500_y_cuenta(monkeypatch):
    import app.routes as routes

    def _falla():
        raise RuntimeError("fallo simulado")

    monkeypatch.setattr(routes, "obtener_resumen_dashboard", _falla)
    client = create_app().test_client()

    response = client.get("/")

    assert response.status_code == 500
    assert response.get_json()["error"] == "Error interno"
    assert response.get_json()["request_id"] == response.headers["X-Request-ID"]

    metrics = client.get("/metrics").get_data(as_text=True)
    assert "citibike_errors_total" in metrics
