import os
import tempfile
import boto3
from botocore.exceptions import ClientError
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / '.env')


S3_BUCKET  = os.getenv("S3_BUCKET", "agri-file-upload")
AWS_REGION = os.getenv("AWS_REGION", "eu-north-1")

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def upload_wav(local_path: str, farmer_id: str, recording_id: str) -> str:
    """
    Uploads WAV file to S3.
    Returns the s3_key on success, raises exception on failure.
    Key format: recordings/{farmer_id}/{recording_id}.wav
    """
    s3_key = f"recordings/{farmer_id}/{recording_id}.wav"
    try:
        s3_client.upload_file(
            local_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "audio/wav"}
        )
        print(f"Uploaded to S3: {s3_key}")
        return s3_key
    except ClientError as e:
        print(f"S3 upload failed: {e}")
        raise

def download_wav(s3_key: str) -> str:
    """
    Downloads WAV file from S3 to a temp path.
    Returns the local temp file path.
    Caller is responsible for deleting the temp file.
    """
    try:
        tmp = tempfile.NamedTemporaryFile(
            delete=False,
            suffix='.wav'
        )
        tmp.close()
        s3_client.download_file(S3_BUCKET, s3_key, tmp.name)
        print(f"Downloaded from S3: {s3_key} → {tmp.name}")
        return tmp.name
    except ClientError as e:
        print(f"S3 download failed: {e}")
        raise

def delete_wav(s3_key: str) -> bool:
    """
    Deletes WAV file from S3 after processing.
    Returns True if deleted, False if failed.
    """
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        print(f"Deleted from S3: {s3_key}")
        return True
    except ClientError as e:
        print(f"S3 delete failed: {e}")
        return False