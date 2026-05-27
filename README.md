# Flask-Dashboard-S3

Dashboard web en Flask que consume un dataset Parquet curado desde Amazon S3, como etapa final de un pipeline DataOps sobre el dataset público **NYC Citi Bike Trips**.

Incluye CI/CD con GitHub Actions, contenedorización con Docker y despliegue automático en Render.

## ¿Qué hace?

- Lee el archivo Parquet curado desde S3 usando una URL presignada (sin exponer credenciales)
- Expone un dashboard HTML con resumen del dataset: total de registros, columnas y preview de 10 filas
- Endpoint `/health` para monitoreo del estado del servicio
- Se despliega automáticamente en Render ante cada push a `main`

## Estructura

```
Flask-Dashboard-S3/
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── routes.py
│   ├── services/
│   │   ├── s3_service.py       # Genera URL presignada desde S3
│   │   └── parquet_service.py  # Lee Parquet y construye resumen
│   └── templates/
│       └── dashboard.html
├── tests/
├── .github/workflows/          # Pipeline CI con pytest
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── render.yaml
├── requirements.txt
└── run.py
```

## Requisitos

- Python 3.11+
- Docker (opcional para desarrollo local)
- Credenciales AWS con acceso de lectura al bucket S3

```bash
pip install -r requirements.txt
```

## Configuración

Copia `.env.example` a `.env`:

```env
FLASK_ENV=development
SECRET_KEY=dev-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=nombre-de-tu-bucket
S3_PARQUET_KEY=landing/archivo.parquet
```

## Uso local

```bash
# Sin Docker
python run.py

# Con Docker
docker compose up
```

La app queda disponible en `http://localhost:5000`.

## Endpoints

| Ruta | Descripción |
|---|---|
| `GET /` | Dashboard HTML con resumen del dataset |
| `GET /health` | Estado del servicio (`{"status": "ok"}`) |

## CI/CD

- **GitHub Actions**: ejecuta `pytest` automáticamente en cada push
- **Render**: `render.yaml` con `autoDeploy: true` → despliegue automático al pasar los tests
- **Docker**: imagen basada en `python:3.11-slim`, servida con Gunicorn en el puerto 5000

## Seguridad

- Las credenciales AWS se configuran en Render como secretos (`sync: false`)
- La URL presignada de S3 tiene tiempo de expiración, sin acceso permanente al Parquet
- El endpoint `/health` no expone datos del dataset
- `.gitignore` excluye `.env` y archivos de credenciales
