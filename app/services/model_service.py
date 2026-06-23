import os
import json
import urllib.request

_METRICAS = None


def _cargar_metricas():
    bucket = os.getenv("S3_BUCKET_NAME")
    prefix = os.getenv("S3_MODEL_PREFIX", "models/")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not bucket:
        return None

    url = f"https://{bucket}.s3.{region}.amazonaws.com/{prefix.rstrip('/')}/metricas.json"
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=5):
            pass
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def _fallback_metricas():
    tn, fp = 67564, 1047
    fn, tp = 24699, 1376
    total = tn + fp + fn + tp
    return {
        "accuracy": round((tp + tn) / total, 4),
        "recall": round(tp / (tp + fn), 4),
        "precision": round(tp / (tp + fp), 4),
        "f1_score": round(2 * tp / (2 * tp + fp + fn), 4),
        "roc_auc": 0.5890,
        "gini": round(2 * 0.5890 - 1, 4),
        "umbral": 900,
        "umbral_minutos": 15,
        "matriz_confusion": [[tn, fp], [fn, tp]],
        "clases": ["corto", "largo"],
        "proporcion_largos": 0.275,
        "train_size": 378744,
        "test_size": 94686,
        "nota": "Métricas del último entrenamiento (Logistic Regression, 473k registros)",
    }


def obtener_metricas():
    global _METRICAS
    if _METRICAS is None:
        _METRICAS = _cargar_metricas()

    base = _fallback_metricas()

    if _METRICAS:
        base.update(_METRICAS)
        if "gini" not in _METRICAS and "roc_auc" in base:
            base["gini"] = round(2 * base["roc_auc"] - 1, 4)

    return base
