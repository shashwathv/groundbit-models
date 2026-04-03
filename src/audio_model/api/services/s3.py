# services/s3.py

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
    Upload WAV to S3. Returns s3_key on success.
    Raises exception on failure — caller must handle.

    Key format: recordings/{farmer_id}/{recording_id}.wav

    S3 UPLOAD VERIFICATION:
    After upload we call head_object to confirm the file actually
    exists in the bucket before returning. This catches silent
    upload failures where boto3 doesn't raise but file isn't there.
    """
    s3_key = f"recordings/{farmer_id}/{recording_id}.wav"

    try:
        # ── Step 1: upload ─────────────────────────────────────────
        s3_client.upload_file(
            local_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "audio/wav"}
        )
        print(f"S3 upload sent: s3://{S3_BUCKET}/{s3_key}")

        # ── Step 2: verify file exists in bucket ───────────────────
        # head_object returns metadata if file exists, raises 404 if not
        response = s3_client.head_object(Bucket=S3_BUCKET, Key=s3_key)
        file_size = response.get("ContentLength", 0)

        if file_size == 0:
            raise ValueError(f"S3 upload verified but file size is 0 bytes — something went wrong")

        print(f"S3 upload verified: {s3_key} ({file_size} bytes)")
        return s3_key

    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            raise FileNotFoundError(
                f"S3 upload verification failed — file not found after upload: {s3_key}"
            )
        raise RuntimeError(f"S3 error ({error_code}): {e}")

    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}")


def download_wav(s3_key: str) -> str:
    """
    Download WAV from S3 to a temp file.
    Returns local temp path. Caller must delete after use.
    """
    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        tmp.close()
        s3_client.download_file(S3_BUCKET, s3_key, tmp.name)
        print(f"S3 download: {s3_key} → {tmp.name}")
        return tmp.name
    except ClientError as e:
        raise RuntimeError(f"S3 download failed: {e}")


def delete_wav(s3_key: str) -> bool:
    """Delete WAV from S3 after processing."""
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        print(f"S3 deleted: {s3_key}")
        return True
    except ClientError as e:
        print(f"S3 delete failed: {e}")
        return False


def check_bucket_access() -> bool:
    """
    Health check — verify we can reach the S3 bucket.
    Called at startup to catch credential issues early.
    """
    try:
        s3_client.head_bucket(Bucket=S3_BUCKET)
        print(f"S3 bucket accessible: {S3_BUCKET}")
        return True
    except ClientError as e:
        error_code = e.response['Error']['Code']
        print(f"S3 bucket check failed ({error_code}): {S3_BUCKET}")
        return False