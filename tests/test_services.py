"""Tests de los servicios del dashboard (sin red: S3 se simula con monkeypatch)."""
import numpy as np
import pandas as pd
import pytest

from app.services import ml_service, model_service, parquet_service, s3_service


@pytest.fixture
def sin_s3(monkeypatch):
    """Fuerza el fallo de lectura desde S3 para usar los datos de respaldo."""

    def _falla():
        raise ConnectionError("S3 no disponible en tests")

    monkeypatch.setattr(parquet_service, "leer_parquet_desde_s3", _falla)


# --- s3_service -----------------------------------------------------------

def test_url_parquet_se_arma_desde_variables(monkeypatch):
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket-demo")
    monkeypatch.setenv("S3_PARQUET_KEY", "curated/sample.parquet")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    url = s3_service.obtener_url_parquet()

    assert url == "https://bucket-demo.s3.us-east-1.amazonaws.com/curated/sample.parquet"


def test_url_parquet_falla_sin_configuracion(monkeypatch):
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    monkeypatch.delenv("S3_PARQUET_KEY", raising=False)

    with pytest.raises(ValueError):
        s3_service.obtener_url_parquet()


# --- parquet_service -------------------------------------------------------

def test_dataframe_de_respaldo_si_s3_falla(sin_s3):
    df = parquet_service.obtener_dataframe()

    assert len(df) == 100
    for col in ["tripduration", "starttime", "start_station_id", "hour", "age"]:
        assert col in df.columns


def test_resumen_en_modo_prueba_si_s3_falla(sin_s3):
    resumen = parquet_service.obtener_resumen_dashboard()

    assert resumen["estado"].startswith("Modo prueba")
    assert resumen["total_registros"] == len(resumen["preview"])


def test_resumen_con_datos_de_s3(monkeypatch):
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    monkeypatch.setattr(parquet_service, "leer_parquet_desde_s3", lambda: df)

    resumen = parquet_service.obtener_resumen_dashboard()

    assert resumen["estado"] == "Datos cargados desde S3"
    assert resumen["total_registros"] == 3
    assert resumen["columnas"] == ["a", "b"]


def test_agregaciones_cuadran_con_el_total(sin_s3):
    agg = parquet_service.obtener_agregaciones()

    total = agg["kpis"]["total_viajes"]
    assert total == 100
    assert sum(r["count"] for r in agg["viajes_por_hora"]) == total
    assert sum(r["count"] for r in agg["viajes_por_dia"]) == total
    assert sum(r["count"] for r in agg["histograma_duracion"]) == total
    assert len(agg["top_estaciones"]) <= 15


def test_histograma_columna_inexistente():
    assert parquet_service._build_histogram(pd.DataFrame({"x": [1]}), "y", 5) == []


def test_filtros_y_paginacion(sin_s3):
    todo = parquet_service.obtener_datos_filtrados(por_pagina=10)
    assert todo["total"] == 100
    assert todo["total_paginas"] == 10
    assert len(todo["datos"]) == 10

    filtrado = parquet_service.obtener_datos_filtrados(
        hora_min=8, hora_max=18, usertype=["Subscriber"], age_min=18, age_max=40,
        fecha_desde="2026-01-01", fecha_hasta="2026-01-31", is_weekend=0,
        gender=["Male", "Female"], dayofweek=[0, 1, 2, 3, 4],
        start_station_id=[3100, 3200, 3300],
    )
    for fila in filtrado["datos"]:
        assert 8 <= fila["hour"] <= 18
        assert fila["usertype"] == "Subscriber"
        assert 18 <= fila["age"] <= 40
        assert fila["is_weekend"] == 0
        assert fila["start_station_id"] in (3100, 3200, 3300)
    assert filtrado["total"] < todo["total"]


# --- model_service ---------------------------------------------------------

def test_metricas_de_respaldo_sin_bucket(monkeypatch):
    monkeypatch.setattr(model_service, "_METRICAS", None)
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    m = model_service.obtener_metricas()

    tn, fp = m["matriz_confusion"][0]
    fn, tp = m["matriz_confusion"][1]
    assert m["accuracy"] == round((tp + tn) / (tn + fp + fn + tp), 4)
    assert m["gini"] == round(2 * m["roc_auc"] - 1, 4)


def test_metricas_de_s3_sobrescriben_el_respaldo(monkeypatch):
    monkeypatch.setattr(model_service, "_METRICAS", None)
    monkeypatch.setattr(model_service, "_cargar_metricas", lambda: {"roc_auc": 0.8, "accuracy": 0.9})

    m = model_service.obtener_metricas()

    assert m["accuracy"] == 0.9
    assert m["roc_auc"] == 0.8
    assert m["gini"] == 0.6


# --- ml_service ------------------------------------------------------------

class _ModeloFalso:
    def predict_proba(self, X):
        return np.array([[0.2, 0.8]])


class _EscaladorIdentidad:
    def transform(self, X):
        return X.values


class _EncoderFalso:
    classes_ = np.array(["Customer", "Subscriber", "Male", "Female"])

    def transform(self, valores):
        return [list(self.classes_).index(valores[0])]


def _transformers():
    return {
        "station_freq": {3100: 10},
        "label_encoders": {"usertype": _EncoderFalso(), "gender": _EncoderFalso()},
        "feature_cols": ["hour", "usertype", "gender", "start_station_freq"],
        "scaler": _EscaladorIdentidad(),
    }


def test_sin_bucket_el_modelo_no_esta_disponible(monkeypatch):
    monkeypatch.setattr(ml_service, "_modelo", None)
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    assert ml_service.disponible() is False
    assert ml_service.predecir({"hour": 8}) is None


def test_prediccion_con_modelo_cargado(monkeypatch):
    monkeypatch.setattr(ml_service, "_modelo", _ModeloFalso())
    monkeypatch.setattr(ml_service, "_transformers", _transformers())

    r = ml_service.predecir(
        {"hour": 8, "usertype": "Subscriber", "gender": "Male", "start_station_id": 3100}
    )

    assert r == {"probabilidad_largo": 0.8, "prediccion": 1, "etiqueta": "largo"}
