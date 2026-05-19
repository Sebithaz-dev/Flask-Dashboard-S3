import pandas as pd
from app.services.s3_service import obtener_url_parquet


def leer_parquet_desde_s3():
    url = obtener_url_parquet()
    df = pd.read_parquet(url)
    return df


def obtener_resumen_dashboard():
    try:
        df = leer_parquet_desde_s3()

        total_registros = len(df)
        total_columnas = len(df.columns)

        columnas = list(df.columns)

        resumen = {
            "estado": "Datos cargados desde S3",
            "total_registros": total_registros,
            "total_columnas": total_columnas,
            "columnas": columnas,
            "preview": df.head(10).to_dict(orient="records")
        }

        return resumen

    except Exception as e:
        resumen = {
            "estado": "Modo prueba: no se pudo cargar el Parquet desde S3",
            "error": str(e),
            "total_registros": 3,
            "total_columnas": 4,
            "columnas": ["id", "categoria", "valor", "fecha"],
            "preview": [
                {"id": 1, "categoria": "A", "valor": 120, "fecha": "2026-01-01"},
                {"id": 2, "categoria": "B", "valor": 90, "fecha": "2026-01-02"},
                {"id": 3, "categoria": "A", "valor": 150, "fecha": "2026-01-03"},
            ]
        }

        return resumen