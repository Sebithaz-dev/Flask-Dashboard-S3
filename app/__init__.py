"""Application factory del dashboard Citi Bike.

Incluye observabilidad base para la EP3:
- endpoint Prometheus ``/metrics``
- ``X-Request-ID`` para correlacionar logs y trazas
- logs JSON a stdout (compatibles con CloudWatch Logs)
- contador de errores no controlados
"""
from __future__ import annotations

import json
import logging
import os
import time
import uuid

from flask import Flask, g, jsonify, request
from prometheus_client import Counter
from prometheus_flask_exporter import PrometheusMetrics

from app.config import Config

SERVICE_NAME = "flask-dashboard-s3"
VERSION = os.getenv("APP_VERSION", "0.1.0")
COMMIT = os.getenv("GIT_SHA", "local")

# Contador de errores no controlados. Se registra una sola vez por proceso.
ERRORS = Counter(
    "citibike_errors_total",
    "Errores no controlados del dashboard Citi Bike",
    ["type"],
)

# El registry de prometheus_client es global: la metrica informativa solo se
# registra una vez aunque se creen varias apps (tests, workers de gunicorn).
_INFO_REGISTERED = False


class JsonFormatter(logging.Formatter):
    """Formatea cada registro como una linea JSON."""

    _EXTRA_FIELDS = (
        "request_id",
        "method",
        "path",
        "status",
        "duration_ms",
        "service",
        "version",
        "commit",
    )

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in self._EXTRA_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def _configure_logging(app: Flask) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    app.logger.handlers = [handler]
    app.logger.setLevel(logging.INFO)
    app.logger.propagate = False


def _log_extra(**kwargs) -> dict:
    base = {
        "request_id": getattr(g, "request_id", None),
        "service": SERVICE_NAME,
        "version": VERSION,
        "commit": COMMIT,
    }
    base.update(kwargs)
    return base


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    _configure_logging(app)

    # Expone /metrics en formato Prometheus y mide latencia/errores por endpoint.
    metrics = PrometheusMetrics(app, group_by="endpoint")
    global _INFO_REGISTERED
    if not _INFO_REGISTERED:
        metrics.info(
            "citibike_dashboard_info",
            "Dashboard Citi Bike",
            version=VERSION,
            commit=COMMIT,
        )
        _INFO_REGISTERED = True

    @app.before_request
    def _start_request() -> None:
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.request_started = time.perf_counter()

    @app.after_request
    def _finish_request(response):
        request_id = getattr(g, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id

        started = getattr(g, "request_started", None)
        duration_ms = round((time.perf_counter() - started) * 1000, 2) if started else None
        app.logger.info(
            "request",
            extra=_log_extra(
                method=request.method,
                path=request.path,
                status=response.status_code,
                duration_ms=duration_ms,
            ),
        )
        return response

    # Handlers explicitos por codigo: Sonar exige un status literal y, de
    # paso, conservan las paginas de error HTML de Werkzeug.
    @app.errorhandler(400)
    def _handle_bad_request(exc):
        return exc.get_response(), 400

    @app.errorhandler(404)
    def _handle_not_found(exc):
        return exc.get_response(), 404

    @app.errorhandler(405)
    def _handle_method_not_allowed(exc):
        return exc.get_response(), 405

    @app.errorhandler(Exception)
    def _handle_unexpected_error(exc):
        ERRORS.labels(type=type(exc).__name__).inc()
        app.logger.exception("unhandled_exception", extra=_log_extra())
        response = jsonify(
            {
                "error": "Error interno",
                "request_id": getattr(g, "request_id", None),
            }
        )
        return response, 500

    from app.routes import main

    app.register_blueprint(main)
    return app
