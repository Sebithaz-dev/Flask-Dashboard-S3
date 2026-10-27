FROM python:3.11-slim

ARG GIT_SHA=local
LABEL org.opencontainers.image.source="https://github.com/Sebithaz-dev/Flask-Dashboard-S3" \
      org.opencontainers.image.description="Dashboard Flask de Citi Bike con modelo ML" \
      org.opencontainers.image.revision="${GIT_SHA}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    GIT_SHA=${GIT_SHA} \
    # Parametros de escalabilidad de gunicorn, sobrescribibles por entorno
    GUNICORN_CMD_ARGS="--workers=1 --threads=4 --worker-class=gthread --timeout=60"

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app ./app
COPY run.py .

# Usuario sin privilegios
RUN useradd --create-home --uid 10001 appuser \
    && chown -R appuser:appuser /app
USER 10001

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=3)"]

CMD ["gunicorn", "-b", "0.0.0.0:5000", "run:app"]
