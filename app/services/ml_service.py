import os
import sys
import joblib
import numpy as np
import pandas as pd
import urllib.request
import tempfile

_modelo = None
_transformers = None


def _descargar_artefactos():
    bucket = os.getenv("S3_BUCKET_NAME")
    prefix = os.getenv("S3_MODEL_PREFIX", "models/")
    region = os.getenv("AWS_REGION", "us-east-1")
    tmp = tempfile.gettempdir()

    if not bucket:
        print("[ml_service] FALLA: variable S3_BUCKET_NAME no configurada", flush=True)
        return None, None

    def _url(key):
        return f"https://{bucket}.s3.{region}.amazonaws.com/{prefix.rstrip('/')}/{key}"

    # --- Método 1: URL pública directa ---
    print(f"[ml_service] Metodo 1: URL publica directa", flush=True)
    try:
        for fname in ["modelo.pkl", "transformers.pkl"]:
            url = _url(fname)
            print(f"[ml_service]   Descargando {url}", flush=True)
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as h:
                print(f"[ml_service]   HEAD -> HTTP {h.status}", flush=True)
            resp = urllib.request.urlopen(url, timeout=30)
            path = os.path.join(tmp, fname)
            with open(path, "wb") as f:
                f.write(resp.read())
            print(f"[ml_service]   OK ({os.path.getsize(path)} bytes)", flush=True)
            resp.close()

        modelo = joblib.load(os.path.join(tmp, "modelo.pkl"))
        transformers = joblib.load(os.path.join(tmp, "transformers.pkl"))
        print("[ml_service] Modelo cargado OK (metodo 1)", flush=True)
        return modelo, transformers

    except Exception as e1:
        print(f"[ml_service] Metodo 1 fallo: {e1}", flush=True)

    # --- Método 2: boto3 (credenciales en entorno) ---
    print(f"[ml_service] Metodo 2: boto3 con credenciales de entorno", flush=True)
    try:
        import boto3
        s3 = boto3.client("s3", region_name=region)
        for fname in ["modelo.pkl", "transformers.pkl"]:
            key = f"{prefix.rstrip('/')}/{fname}"
            path = os.path.join(tmp, fname)
            print(f"[ml_service]   Descargando s3://{bucket}/{key}", flush=True)
            s3.download_file(bucket, key, path)
            print(f"[ml_service]   OK ({os.path.getsize(path)} bytes)", flush=True)

        modelo = joblib.load(os.path.join(tmp, "modelo.pkl"))
        transformers = joblib.load(os.path.join(tmp, "transformers.pkl"))
        print("[ml_service] Modelo cargado OK (metodo 2)", flush=True)
        return modelo, transformers

    except Exception as e2:
        print(f"[ml_service] Metodo 2 fallo: {e2}", flush=True)

    print("[ml_service] Ambos metodos fallaron, modelo NO disponible", flush=True)
    return None, None


def cargar_modelo():
    global _modelo, _transformers
    _modelo, _transformers = _descargar_artefactos()


def predecir(datos):
    global _modelo, _transformers
    if _modelo is None:
        cargar_modelo()
        if _modelo is None:
            return None

    t = _transformers
    df = pd.DataFrame([datos])
    df["start_station_freq"] = np.log1p(
        df["start_station_id"].map(t["station_freq"]).fillna(0)
    )
    for col in ["usertype", "gender"]:
        le = t["label_encoders"][col]
        df[col] = (
            df[col]
            .astype(str)
            .map(lambda x: le.transform([x])[0] if x in le.classes_ else -1)
        )
    X = df[t["feature_cols"]].astype(float)
    X_s = t["scaler"].transform(X)
    prob = _modelo.predict_proba(X_s)[0, 1]
    pred = int(prob >= 0.65)
    return {
        "probabilidad_largo": round(float(prob), 4),
        "prediccion": pred,
        "etiqueta": "largo" if pred else "corto",
    }


def disponible():
    if _modelo is None:
        cargar_modelo()
    return _modelo is not None