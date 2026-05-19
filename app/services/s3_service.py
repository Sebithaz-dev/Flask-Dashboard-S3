import os

def obtener_url_parquet():
    bucket = os.getenv("S3_BUCKET_NAME")
    key = os.getenv("S3_PARQUET_KEY")
    region = os.getenv("AWS_REGION", "us-east-1")

    if not bucket or not key:
        raise ValueError("Faltan variables S3_BUCKET_NAME o S3_PARQUET_KEY")

    return f"https://{bucket}.s3.{region}.amazonaws.com/{key}"