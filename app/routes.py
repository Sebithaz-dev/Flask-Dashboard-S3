from flask import Blueprint, render_template, jsonify
from app.services.parquet_service import obtener_resumen_dashboard

main = Blueprint("main", __name__)


@main.route("/")
def dashboard():
    resumen = obtener_resumen_dashboard()

    return render_template(
        "dashboard.html",
        resumen=resumen
    )


@main.route("/status")
def health():
    return jsonify({
        "status": "ok",
        "message": "Flask dashboard funcionando correctamente"
    })