"""Safe, idempotent machinery photo upload utility for FarmConnect -> Supabase Storage.

Uploads local photos from 'app/static/uploads/machinery/' to the Supabase S3-compatible bucket.
- Does NOT delete or alter any local photo files.
- Skips already-uploaded photos if sizes match (idempotent).
- Validates uploaded object count and verifies accessibility.
- Never prints secrets or credentials.
"""

import os
import sys
import getpass
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv

load_dotenv(BASE_DIR / ".env")


def upload_photos():
    print("=" * 72)
    print("FarmConnect — Supabase Storage Photo Migration")
    print("=" * 72)

    photos_dir = BASE_DIR / "app" / "static" / "uploads" / "machinery"
    if not photos_dir.exists():
        print(f"[-] ERROR: Local photos directory not found: {photos_dir}", file=sys.stderr)
        sys.exit(1)

    local_photos = [f for f in photos_dir.iterdir() if f.is_file() and f.suffix.lower() in (".jpg", ".jpeg", ".png")]
    print(f"[*] Found {len(local_photos)} local machinery photo(s) to migrate.")

    bucket_name = (
        os.getenv("S3_BUCKET_NAME")
        or os.getenv("SUPABASE_S3_BUCKET")
        or "machinery-photos"
    )
    endpoint_url = os.getenv("S3_ENDPOINT_URL") or os.getenv("SUPABASE_S3_ENDPOINT")
    region_name = os.getenv("S3_REGION_NAME") or os.getenv("SUPABASE_S3_REGION", "us-east-1")
    access_key = os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("SUPABASE_S3_ACCESS_KEY")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("SUPABASE_S3_SECRET_KEY")
    custom_domain = os.getenv("S3_CUSTOM_DOMAIN")

    if not endpoint_url:
        try:
            endpoint_url = input("Enter Supabase S3 Endpoint URL (e.g. https://<ref>.supabase.co/storage/v1/s3): ").strip()
        except (EOFError, OSError):
            print("[-] ERROR: S3_ENDPOINT_URL not set and non-interactive input unavailable.", file=sys.stderr)
            sys.exit(1)

    if not access_key:
        try:
            access_key = input("Enter Supabase S3 Access Key ID: ").strip()
        except (EOFError, OSError):
            print("[-] ERROR: AWS_ACCESS_KEY_ID not set.", file=sys.stderr)
            sys.exit(1)

    if not secret_key:
        try:
            secret_key = getpass.getpass("Enter Supabase S3 Secret Access Key: ").strip()
        except (EOFError, OSError):
            print("[-] ERROR: AWS_SECRET_ACCESS_KEY not set.", file=sys.stderr)
            sys.exit(1)

    try:
        import boto3
        from botocore.exceptions import ClientError
    except ImportError:
        print("[-] ERROR: boto3 is not installed. Install with: pip install boto3", file=sys.stderr)
        sys.exit(1)

    print(f"[*] Initializing S3 client for bucket '{bucket_name}'...")
    s3 = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=region_name,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )

    # Verify or create bucket
    try:
        s3.head_bucket(Bucket=bucket_name)
        print(f"[+] Bucket '{bucket_name}' exists and is accessible.")
    except ClientError as e:
        error_code = str(e.response.get("Error", {}).get("Code", ""))
        if error_code in ("404", "NoSuchBucket"):
            print(f"[*] Bucket '{bucket_name}' does not exist. Attempting creation...")
            s3.create_bucket(Bucket=bucket_name)
            print(f"[+] Bucket '{bucket_name}' created successfully.")
        else:
            print(f"[!] Warning checking bucket: {e}. Will attempt upload directly.")

    # Upload photos
    uploaded_count = 0
    skipped_count = 0
    failed_count = 0

    print(f"[*] Uploading {len(local_photos)} photos with prefix 'machinery/'...")
    for idx, photo_path in enumerate(local_photos, start=1):
        key = f"machinery/{photo_path.name}"
        local_size = photo_path.stat().st_size

        # Check if already present with same size
        try:
            head = s3.head_object(Bucket=bucket_name, Key=key)
            remote_size = head.get("ContentLength", -1)
            if remote_size == local_size:
                skipped_count += 1
                continue
        except Exception:
            pass  # File doesn't exist yet or head failed, proceed to upload

        try:
            with open(photo_path, "rb") as f:
                s3.put_object(
                    Bucket=bucket_name,
                    Key=key,
                    Body=f,
                    ContentType="image/jpeg",
                )
            uploaded_count += 1
            if idx % 10 == 0 or idx == len(local_photos):
                print(f"  --> Progress: {idx}/{len(local_photos)} photos processed ({uploaded_count} uploaded, {skipped_count} skipped).")
        except Exception as upload_err:
            print(f"  [-] Failed uploading {photo_path.name}: {upload_err}")
            failed_count += 1

    print(f"\n[+] Photo Upload Summary:")
    print(f"    Total Local Photos: {len(local_photos)}")
    print(f"    Uploaded:           {uploaded_count}")
    print(f"    Skipped (Existing): {skipped_count}")
    print(f"    Failed:             {failed_count}")

    if failed_count > 0:
        raise RuntimeError(f"{failed_count} photo(s) failed to upload.")

    # Verify remote count
    print("[*] Verifying remote bucket contents...")
    paginator = s3.get_paginator("list_objects_v2")
    remote_keys = []
    for page in paginator.paginate(Bucket=bucket_name, Prefix="machinery/"):
        for item in page.get("Contents", []):
            remote_keys.append(item["Key"])

    print(f"[+] Total objects found in bucket with prefix 'machinery/': {len(remote_keys)}")
    if len(remote_keys) >= len(local_photos):
        print("[+] SUCCESS: Remote photo count matches or exceeds local photo count.")
    else:
        print(f"[!] Warning: Remote count ({len(remote_keys)}) is less than local count ({len(local_photos)}).")

    print("[+] All local photos remain untouched and safe.")


if __name__ == "__main__":
    try:
        upload_photos()
    except Exception as exc:
        print(f"\n[-] PHOTO MIGRATION FAILED: {exc}", file=sys.stderr)
        sys.exit(1)
