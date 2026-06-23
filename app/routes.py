from flask import Blueprint, render_template, jsonify, request
from app.services.parquet_service import (
    obtener_resumen_dashboard,
    obtener_agregaciones,
    obtener_datos_filtrados,
)
from app.services.model_service import obtener_metricas
from app.services.ml_service import predecir, disponible

main = Blueprint("main", __name__)


@main.route("/")
def overview():
    resumen = obtener_resumen_dashboard()
    resumen["page"] = "overview"
    return render_template("overview.html", resumen=resumen)


@main.route("/exploracion")
def exploracion():
    resumen = obtener_resumen_dashboard()
    resumen["page"] = "exploracion"
    return render_template("exploration.html", resumen=resumen)


@main.route("/prediccion")
def prediccion():
    resumen = obtener_resumen_dashboard()
    resumen["page"] = "prediccion"
    return render_template(
        "prediction.html",
        resumen=resumen,
        modelo_disponible=disponible(),
    )


@main.route("/api/resumen")
def api_resumen():
    data = obtener_agregaciones()
    return jsonify(data)


@main.route("/api/modelo/metricas")
def api_modelo_metricas():
    return jsonify(obtener_metricas())


@main.route("/api/datos")
def api_datos():
    pagina = request.args.get("pagina", 1, type=int)
    por_pagina = request.args.get("por_pagina", 50, type=int)
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    hora_min = request.args.get("hora_min", type=int)
    hora_max = request.args.get("hora_max", type=int)
    usertype = request.args.getlist("usertype")
    gender = request.args.getlist("gender")
    age_min = request.args.get("age_min", type=int)
    age_max = request.args.get("age_max", type=int)
    dayofweek = request.args.getlist("dayofweek", type=int)
    is_weekend = request.args.get("is_weekend", type=int)
    start_station_id = request.args.getlist("start_station_id", type=int)

    result = obtener_datos_filtrados(
        fecha_desde=fecha_desde or None,
        fecha_hasta=fecha_hasta or None,
        hora_min=hora_min,
        hora_max=hora_max,
        usertype=usertype or None,
        gender=gender or None,
        age_min=age_min,
        age_max=age_max,
        dayofweek=dayofweek or None,
        is_weekend=is_weekend,
        start_station_id=start_station_id or None,
        pagina=pagina,
        por_pagina=por_pagina,
    )
    return jsonify(result)


@main.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "message": "Flask dashboard funcionando correctamente"
    })


@main.route("/predict", methods=["POST"])
def predict():
    if not disponible():
        return jsonify({"error": "Modelo no disponible"}), 503
    datos = request.get_json()
    resultado = predecir(datos)
    if resultado is None:
        return jsonify({"error": "Error al procesar prediccion"}), 500
    return jsonify(resultado)
