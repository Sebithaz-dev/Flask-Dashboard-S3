# Flask-Dashboard-S3

[![CI/CD](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/workflows/ci-cd.yml)
[![Security & Quality](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/workflows/security.yml/badge.svg)](https://github.com/Sebithaz-dev/Flask-Dashboard-S3/actions/workflows/security.yml)
[![Quality Gate](https://sonarcloud.io/api/project_badges/measure?project=Sebithaz-dev_Flask-Dashboard-S3&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Sebithaz-dev_Flask-Dashboard-S3)

Dashboard web interactivo construido con **Flask + Chart.js** que consume un dataset Parquet curado desde Amazon S3, como etapa final de un pipeline DataOps sobre el dataset público **NYC Citi Bike Trips**.

Incluye CI/CD con GitHub Actions, contenedorización con Docker, despliegue automático en Render e integración con un modelo de clasificación ML entrenado externamente.

## ¿Qué hace?

- **Tres páginas interactivas**: Vista General (KPIs + métricas del modelo), Exploración (filtros + charts + tabla), Predicción ML (formulario con validación)
- **Gráficos en el cliente**: Chart.js renderiza en el navegador — Flask solo envía JSON liviano
- **API REST**: Endpoints JSON para consumir datos, filtros y predicciones desde cualquier frontend
- **Modelo ML**: Integración con modelo Logistic Regression entrenado en pipeline separado ([Model-Training-S3](https://github.com/Sebithaz-dev/Model-Training-S3))
- **Despliegue automático**: CI/CD con GitHub Actions + Render (autoDeploy)

## Dashboard Interactivo

| Página | Ruta | Contenido |
|--------|------|-----------|
| **Vista General** | `/` | KPIs (viajes, duración, estaciones), charts de distribución (tiempo, usuario, género, duración), métricas del modelo ML (accuracy, recall, F1, ROC AUC, Gini) y matriz de confusión |
| **Exploración** | `/exploracion` | Panel de filtros (fecha, hora, día, usuario, género, edad, estación), 5 charts interactivos (hora, día, duración, edad, top estaciones), tabla paginada con descarga CSV |
| **Predicción ML** | `/prediccion` | Formulario con validación para predecir duración de viaje (larga > 15 min / corta) usando el modelo entrenado |

## Estructura

```
Flask-Dashboard-S3/
├── app/
│   ├── __init__.py                 # Flask app factory
│   ├── config.py                   # Config desde variables de entorno
│   ├── routes.py                   # Rutas de páginas HTML + API REST
│   ├── services/
│   │   ├── s3_service.py           # URL pública desde S3
│   │   ├── parquet_service.py      # Lectura Parquet + agregaciones + filtros
│   │   ├── ml_service.py           # Carga del modelo y predicción
│   │   └── model_service.py        # Métricas del modelo (S3 + fallback)
│   ├── templates/
│   │   ├── base.html               # Layout con Chart.js CDN
│   │   ├── overview.html           # Vista General
│   │   ├── exploration.html        # Exploración con filtros
│   │   └── prediction.html         # Formulario de predicción
│   └── static/
│       ├── css/styles.css          # Estilos con glassmorphism
│       └── js/dashboard.js         # Lógica: fetch API, Chart.js, filtros, tabla, paginación
├── tests/
│   └── test_routes.py              # Pytest para rutas principales
├── .github/workflows/
│   ├── ci-cd.yml                   # Pipeline CI: test → docker → healthcheck → deploy
│   └── security.yml                # Snyk + SonarCloud (PR/push/semanal)
├── .env.example
├── Dockerfile                      # Incluye HEALTHCHECK contra /health
├── docker-compose.yml
├── render.yaml                     # healthCheckPath: /health
├── requirements.txt
├── requirements-dev.txt            # Dependencias de test + cobertura
├── sonar-project.properties        # Config de SonarCloud
└── run.py
```

## Requisitos

- Python 3.11+
- Docker (opcional para desarrollo local)
- Bucket S3 público con archivo Parquet curado

```bash
pip install -r requirements.txt        # runtime
pip install -r requirements-dev.txt    # runtime + pytest + cobertura
```

## Configuración

Copia `.env.example` a `.env`:

```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=citibike-datalake-seb-690247773624
S3_PARQUET_KEY=curated/citibike_trips/citibike_dashboard_sample.parquet
S3_MODEL_PREFIX=models/
```

> **Nota**: No se requieren credenciales AWS (`AWS_ACCESS_KEY_ID`, etc.). El dashboard lee el Parquet desde una URL pública. Si el bucket no es público, el modelo ML intenta boto3 como fallback.

### Datos en S3

Bucket demo: `citibike-datalake-seb-690247773624` (público, solo lectura).

| Key | Uso |
|-----|-----|
| `curated/citibike_trips/citibike_dashboard_sample.parquet` | Dataset del dashboard (50k filas) |
| `curated/citibike_trips/citibike_curated.snappy.parquet` | Dataset completo para entrenamiento (473k filas) |
| `models/modelo.pkl`, `models/transformers.pkl`, `models/metricas.json` | Artefactos del modelo |

El dashboard usa el sample para responder rápido y el pipeline de entrenamiento
usa el dataset completo. Como el bucket es público, Render no necesita
credenciales AWS.

## Uso local

```bash
# Sin Docker
python run.py

# Con Docker
docker compose up --build
```

La app queda disponible en `http://localhost:5000`.

## Endpoints API

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Página Vista General |
| GET | `/exploracion` | Página Exploración |
| GET | `/prediccion` | Página Predicción ML |
| GET | `/health` | Health check (`{"status": "ok"}`), usado por Docker y Render |
| GET | `/api/resumen` | KPIs + agregaciones para charts |
| GET | `/api/datos?filtros=...` | Datos filtrados con paginación |
| GET | `/api/modelo/metricas` | Accuracy, Recall, F1, ROC AUC, Gini, Matriz de Confusión |
| POST | `/predict` | Predicción ML (recibe JSON con features, devuelve probabilidad) |

### Ejemplo `POST /predict`

Predicción viaje largo:

```json
{
  "start_station_id": 519,
  "usertype": "Customer",
  "gender": "Unknown",
  "hour": 15,
  "month": 8,
  "dayofweek": 6,
  "is_weekend": 1,
  "age": 24
}
```

Predicción viaje corto:

```json
{
  "start_station_id": 3160,
  "usertype": "Subscriber",
  "gender": "Male",
  "hour": 7,
  "month": 2,
  "dayofweek": 1,
  "is_weekend": 0,
  "age": 45
}
```

## Modelo ML

El modelo se entrena en un repositorio independiente: [Model-Training-S3](https://github.com/Sebithaz-dev/Model-Training-S3)

- Algoritmo: **Logistic Regression** con `class_weight="balanced"`
- Umbral de clasificación: **0.65**
- Objetivo: predecir si un viaje dura más de **15 minutos** (900 segundos)
- Artefactos (`modelo.pkl`, `transformers.pkl`, `metricas.json`) se suben a S3 y el dashboard los descarga automáticamente

### Últimas métricas del modelo

| Métrica | Valor |
|---------|-------|
| Accuracy | 0.7281 |
| Recall (largo) | 0.0528 |
| Precision (largo) | 0.5679 |
| F1 Score (largo) | 0.0966 |
| ROC AUC | 0.5890 |
| Gini | 0.178 |

> Las métricas se cargan desde `metricas.json` en S3. Si no está disponible, se usan valores de fallback.

## CI/CD

- **GitHub Actions `ci-cd.yml`**: ejecuta tests con cobertura, construye la imagen Docker, valida `/health` dentro del contenedor y despliega en Render.
- **GitHub Actions `security.yml`**: analiza dependencias y código con Snyk, y publica métricas de calidad/cobertura en SonarCloud.
- **Render**: `render.yaml` con `autoDeploy: true` y `healthCheckPath: /health`.
- **Docker**: imagen basada en `python:3.11-slim`, servida con Gunicorn (multi-thread) y con `HEALTHCHECK` contra `/health`.
- **Contenedor único**: Flask como único proceso (sin Streamlit).

## Seguridad y calidad

### Health check

- `GET /health` responde `{"status": "ok", "message": "Flask dashboard funcionando correctamente"}`.
- Docker ejecuta `HEALTHCHECK` cada 30s contra `/health`.
- Render usa `healthCheckPath: /health` antes de enrutar tráfico.
- `ci-cd.yml` levanta el contenedor y valida `/health` antes del deploy.

### Snyk

1. Crear una cuenta en [Snyk](https://app.snyk.io) y habilitar **Snyk Code**.
2. Generar un API token y cargarlo como secret `SNYK_TOKEN`.
3. `security.yml` ejecuta `snyk test` sobre `requirements.txt` y `requirements-dev.txt`, y `snyk code test` sobre el código. Los resultados se suben como SARIF a GitHub Security. Es informativo al inicio (`continue-on-error`).

### SonarCloud

1. Importar el repositorio en [SonarCloud](https://sonarcloud.io) bajo la organización `sebithaz-dev`.
2. Desactivar **Automatic Analysis** en *Administration → Analysis Method*.
3. Generar un token en *My Account → Security* y cargarlo como secret `SONAR_TOKEN`.
4. La cobertura se genera con `pytest --cov=app` y se publica mediante `sonar-project.properties`.

### Secretos y variables

- **Secrets:** `SNYK_TOKEN`, `SONAR_TOKEN`, `RENDER_DEPLOY_HOOK_URL`.
- **Variables:** `SONAR_ORGANIZATION`, `SONAR_PROJECT_KEY`.

### Buenas prácticas ya aplicadas

- Las variables de S3 (`S3_BUCKET_NAME`, `S3_PARQUET_KEY`, `S3_MODEL_PREFIX`) se definen en `render.yaml` y `.env`.
- El bucket S3 es público de solo lectura (no se requieren credenciales AWS en el dashboard).
- `.gitignore` excluye `.env`, `__pycache__`, cobertura y artefactos SARIF.
- Los endpoints `/health` y `/api/*` no exponen datos sensibles.
