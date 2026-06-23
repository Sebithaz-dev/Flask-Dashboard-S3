import pandas as pd
import numpy as np
from app.services.s3_service import obtener_url_parquet


def leer_parquet_desde_s3():
    url = obtener_url_parquet()
    df = pd.read_parquet(url)
    return df


def obtener_dataframe():
    try:
        return leer_parquet_desde_s3()
    except Exception as e:
        rng = np.random.default_rng(42)
        n = 100
        df = pd.DataFrame({
            "tripduration": rng.exponential(900, n).astype(int),
            "starttime": pd.date_range("2026-01-01", periods=n, freq="h"),
            "start_station_id": rng.choice([3100, 3200, 3300, 3400, 3500], n),
            "usertype": rng.choice(["Subscriber", "Customer"], n, p=[0.7, 0.3]),
            "gender": rng.choice(["Male", "Female", "Unknown"], n, p=[0.6, 0.3, 0.1]),
            "birth_year": rng.integers(1950, 2005, n),
            "year": 2026,
            "hour": rng.integers(0, 24, n),
            "month": rng.integers(1, 13, n),
            "dayofweek": rng.integers(0, 7, n),
            "is_weekend": rng.choice([0, 1], n, p=[0.7, 0.3]),
            "age": rng.integers(18, 70, n),
        })
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


def obtener_agregaciones():
    df = obtener_dataframe()

    kpis = {
        "total_viajes": len(df),
        "duracion_promedio_seg": round(float(df["tripduration"].mean()), 1),
        "estaciones_unicas": int(df["start_station_id"].nunique()),
    }
    if "starttime" in df.columns and not df["starttime"].isna().all():
        kpis["fecha_min"] = df["starttime"].min().strftime("%Y-%m-%d")
        kpis["fecha_max"] = df["starttime"].max().strftime("%Y-%m-%d")

    viajes_por_hora = (
        df.groupby("hour").size().reset_index(name="count")
        .to_dict(orient="records")
    )
    viajes_por_dia = (
        df.groupby("dayofweek").size().reset_index(name="count")
        .to_dict(orient="records")
    )
    if "usertype" in df.columns:
        dist_usertype = (
            df.groupby("usertype").size().reset_index(name="count")
            .to_dict(orient="records")
        )
    else:
        dist_usertype = []

    if "gender" in df.columns:
        dist_genero = (
            df.groupby("gender").size().reset_index(name="count")
            .to_dict(orient="records")
        )
    else:
        dist_genero = []

    top_estaciones = (
        df.groupby("start_station_id").size().reset_index(name="count")
        .sort_values("count", ascending=False).head(15)
        .to_dict(orient="records")
    )

    hist_duracion = _build_histogram(df, "tripduration", 30)
    hist_edad = _build_histogram(df, "age", 20)

    viajes_por_mes = (
        df.groupby("month").size().reset_index(name="count")
        .to_dict(orient="records")
    )

    return {
        "kpis": kpis,
        "viajes_por_hora": viajes_por_hora,
        "viajes_por_dia": viajes_por_dia,
        "viajes_por_mes": viajes_por_mes,
        "distribucion_usertype": dist_usertype,
        "distribucion_genero": dist_genero,
        "top_estaciones": top_estaciones,
        "histograma_duracion": hist_duracion,
        "histograma_edad": hist_edad,
    }


def _build_histogram(df, column, bins):
    if column not in df.columns:
        return []
    counts, edges = np.histogram(df[column].dropna(), bins=bins)
    return [
        {"min": round(float(edges[i]), 1), "max": round(float(edges[i + 1]), 1), "count": int(counts[i])}
        for i in range(len(counts))
    ]


def obtener_datos_filtrados(
    fecha_desde=None,
    fecha_hasta=None,
    hora_min=None,
    hora_max=None,
    usertype=None,
    gender=None,
    age_min=None,
    age_max=None,
    dayofweek=None,
    is_weekend=None,
    start_station_id=None,
    pagina=1,
    por_pagina=50,
):
    df = obtener_dataframe()

    if fecha_desde and "starttime" in df.columns:
        df = df[df["starttime"] >= pd.to_datetime(fecha_desde)]
    if fecha_hasta and "starttime" in df.columns:
        df = df[df["starttime"] <= pd.to_datetime(fecha_hasta)]
    if hora_min is not None and "hour" in df.columns:
        df = df[df["hour"] >= hora_min]
    if hora_max is not None and "hour" in df.columns:
        df = df[df["hour"] <= hora_max]
    if usertype and "usertype" in df.columns:
        if isinstance(usertype, list):
            df = df[df["usertype"].isin(usertype)]
        else:
            df = df[df["usertype"] == usertype]
    if gender and "gender" in df.columns:
        if isinstance(gender, list):
            df = df[df["gender"].isin(gender)]
        else:
            df = df[df["gender"] == gender]
    if age_min is not None and "age" in df.columns:
        df = df[df["age"] >= age_min]
    if age_max is not None and "age" in df.columns:
        df = df[df["age"] <= age_max]
    if dayofweek is not None and "dayofweek" in df.columns:
        df = df[df["dayofweek"].isin(dayofweek)] if isinstance(dayofweek, list) else df[df["dayofweek"] == dayofweek]
    if is_weekend is not None and "is_weekend" in df.columns:
        df = df[df["is_weekend"] == is_weekend]
    if start_station_id and "start_station_id" in df.columns:
        ids = [int(x) for x in (start_station_id if isinstance(start_station_id, list) else [start_station_id])]
        df = df[df["start_station_id"].isin(ids)]

    total = len(df)
    inicio = (pagina - 1) * por_pagina
    datos = df.iloc[inicio:inicio + por_pagina].to_dict(orient="records")

    return {
        "datos": datos,
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": max(1, (total + por_pagina - 1) // por_pagina),
    }