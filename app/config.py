import os
from dotenv import load_dotenv

class Config():
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
    S3_PARQUET_KEY = os.getenv("S3_PARQUET_KEY")
    S3_MODEL_PREFIX = os.getenv("S3_MODEL_PREFIX", "models/")

    FLASK_ENV = os.getenv("FLASK_ENV", "development")