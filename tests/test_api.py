"""Tests de las rutas HTML y la API REST (sin red)."""
import pytest

from app import create_app
from app.services import ml_service, parquet_service


@pytest.fixture
def client(monkeypatch):
    def _falla():
        raise ConnectionError("S3 no disponible en tests")

    monkeypatch.setattr(parquet_service, "leer_parquet_desde_s3", _falla)
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    monkeypatch.setattr(ml_service, "_modelo", None)
    return create_app().test_client()


@pytest.mark.parametrize("ruta", ["/", "/exploracion", "/prediccion"])
def test_paginas_html_responden(client, ruta):
    assert client.get(ruta).status_code == 200


def test_api_resumen(client):
    data = client.get("/api/resumen").get_json()

    assert data["kpis"]["total_viajes"] == 100
    assert {"viajes_por_hora", "top_estaciones", "histograma_edad"} <= set(data)


def test_api_metricas_modelo(client):
    data = client.get("/api/modelo/metricas").get_json()

    assert 0 <= data["accuracy"] <= 1
    assert 0 <= data["pr_auc"] <= 1
    assert 0 <= data["umbral_decision"] <= 1
    assert len(data["matriz_confusion"]) == 2


def test_api_datos_con_filtros(client):
    resp = client.get("/api/datos?pagina=2&por_pagina=20&hora_min=6&usertype=Customer")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["pagina"] == 2
    assert data["por_pagina"] == 20
    assert all(f["hour"] >= 6 and f["usertype"] == "Customer" for f in data["datos"])


def test_predict_sin_modelo_devuelve_503(client):
    resp = client.post("/predict", json={"hour": 8})

    assert resp.status_code == 503
    assert resp.get_json() == {"error": "Modelo no disponible"}


def test_predict_error_de_procesamiento_devuelve_500(client, monkeypatch):
    monkeypatch.setattr("app.routes.disponible", lambda: True)
    monkeypatch.setattr("app.routes.predecir", lambda datos: None)

    resp = client.post("/predict", json={"hour": 8})

    assert resp.status_code == 500


def test_predict_ok(client, monkeypatch):
    esperado = {
        "probabilidad_largo": 0.7,
        "prediccion": 1,
        "etiqueta": "largo",
        "umbral_decision": 0.46,
    }
    monkeypatch.setattr("app.routes.disponible", lambda: True)
    monkeypatch.setattr("app.routes.predecir", lambda datos: esperado)

    resp = client.post("/predict", json={"hour": 8})

    assert resp.status_code == 200
    assert resp.get_json() == esperado
