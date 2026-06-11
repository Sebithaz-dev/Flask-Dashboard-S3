from flask import Blueprint, render_template, jsonify, request
from app.services.parquet_service import obtener_resumen_dashboard
from app.services.ml_service import predecir, disponible

main = Blueprint("main", __name__)


@main.route("/")
def dashboard():
    resumen = obtener_resumen_dashboard()

    return render_template(
        "dashboard.html",
        resumen=resumen
    )


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