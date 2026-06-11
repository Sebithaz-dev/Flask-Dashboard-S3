import os
import joblib
import numpy as np
import pandas as pd
import tempfile
from urllib.request import urlopen

_modelo = None
_transformers = None


def _descargar_artefactos():
    bucket = os.getenv("S3_BUCKET_NAME")
    prefix = os.getenv("S3_MODEL_PREFIX", "models/")
    region = os.getenv("AWS_REGION", "us-east-1")
    if not bucket:
        return None, None

    tmp = tempfile.gettempdir()

    def _url(key):
        return f"https://{bucket}.s3.{region}.amazonaws.com/{prefix.rstrip('/')}/{key}"

    try:
        for fname in ["modelo.pkl", "transformers.pkl"]:
            resp = urlopen(_url(fname))
            with open(os.path.join(tmp, fname), "wb") as f:
                f.write(resp.read())
        modelo_path = os.path.join(tmp, "modelo.pkl")
        trans_path = os.path.join(tmp, "transformers.pkl")
        return joblib.load(modelo_path), joblib.load(trans_path)
    except Exception as e:
        print(f"[ml_service] Error descargando modelo desde S3: {e}")
        return None, None