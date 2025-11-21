from botocore.client import Config
from dotenv import load_dotenv
import boto3
import os
import sys

load_dotenv()
S3_API_LINK = os.getenv("S3_API")
PUB_S3_LINK = os.getenv("PUB_S3_API")
ACCESS_KEY = os.getenv("ACCESS_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
BUCKET = os.getenv("BUCKET")

if not S3_API_LINK or not ACCESS_KEY or not SECRET_KEY or not BUCKET or not PUB_S3_LINK:
    sys.exit(f'One or more of the following: ["S3_API", "ACCESS_KEY", "SECRET_KEY", "BUCKET", "PUB_S3_API"] was not present in your .env file') 

s3 = boto3.client(
    "s3",
    endpoint_url = S3_API_LINK,
    aws_access_key_id = ACCESS_KEY,
    aws_secret_access_key = SECRET_KEY,
    config = Config(signature_version="s3v4"),
    region_name="auto"
)

def upload_to_s3(file_bytes, key, content_type):
    s3.put_object(
        Bucket = BUCKET,
        Key = key,
        Body = file_bytes,
        ContentType = content_type
    )
    return f"{PUB_S3_LINK}/{key}"

def delete_from_s3(key):
    try:
        s3.delete_object(
            Bucket=BUCKET,
            Key=key
        )
        return True
    except Exception as e:
        print("S3 delete error:", e)
        return False