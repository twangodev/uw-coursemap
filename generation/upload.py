"""Upload generated data to S3-compatible object storage."""

from __future__ import annotations

import mimetypes
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from logging import getLogger
from pathlib import Path

import boto3
from botocore.config import Config
from tqdm import tqdm

logger = getLogger(__name__)


def get_s3_client(
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    max_pool_connections: int = 100,
):
    """Create an S3 client for S3-compatible object storage."""
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        config=Config(
            retries={"max_attempts": 3, "mode": "adaptive"},
            max_pool_connections=max_pool_connections,
        ),
    )


def get_content_type(file_path: Path) -> str:
    """Determine the content type for a file."""
    content_type, _ = mimetypes.guess_type(str(file_path))
    if content_type is None:
        if file_path.suffix == ".json":
            return "application/json"
        return "application/octet-stream"
    return content_type


def delete_stale_objects(
    client,
    bucket: str,
    uploaded_keys: set[str],
    prefix: str = "",
) -> int:
    """
    Delete objects from S3 that aren't in the uploaded set.

    Args:
        client: S3 client
        bucket: S3 bucket name
        uploaded_keys: Set of keys that were just uploaded
        prefix: Optional prefix to scope deletion (only delete within this prefix)

    Returns:
        Number of deleted objects
    """
    deleted = 0
    paginator = client.get_paginator("list_objects_v2")
    paginate_kwargs = {"Bucket": bucket}
    if prefix:
        paginate_kwargs["Prefix"] = prefix

    stale_keys = []
    for page in paginator.paginate(**paginate_kwargs):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key not in uploaded_keys:
                stale_keys.append(key)

    if not stale_keys:
        logger.info("No stale objects to delete")
        return 0

    logger.info(f"Found {len(stale_keys)} stale objects to delete")

    # Delete in batches of 1000 (S3 limit)
    for i in tqdm(range(0, len(stale_keys), 1000), desc="Deleting stale objects"):
        batch = stale_keys[i : i + 1000]
        delete_request = {"Objects": [{"Key": key} for key in batch], "Quiet": True}
        try:
            client.delete_objects(Bucket=bucket, Delete=delete_request)
            deleted += len(batch)
        except Exception as e:
            logger.error(f"Failed to delete batch: {e}")

    logger.info(f"Deleted {deleted} stale objects")
    return deleted


def upload_file(
    client,
    bucket: str,
    local_path: Path,
    key: str,
    cache_control: str = "public, max-age=604800",
) -> bool:
    """Upload a single file to S3-compatible storage."""
    try:
        content_type = get_content_type(local_path)

        with open(local_path, "rb") as f:
            client.put_object(
                Bucket=bucket,
                Key=key,
                Body=f,
                ContentType=content_type,
                CacheControl=cache_control,
            )
        return True
    except Exception as e:
        logger.error(f"Failed to upload {key}: {e}")
        return False


def upload_directory(
    data_dir: str,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    bucket: str,
    prefix: str = "",
    max_workers: int = 10,
    cache_control: str = "public, max-age=604800",
) -> tuple[int, int]:
    """
    Upload all files from a directory to S3-compatible storage.

    Args:
        data_dir: Local directory containing files to upload
        endpoint_url: S3-compatible endpoint URL
        access_key_id: S3 access key ID
        secret_access_key: S3 secret access key
        bucket: S3 bucket name
        prefix: Optional prefix for all keys (e.g., "v1/")
        max_workers: Number of concurrent upload threads
        cache_control: Cache-Control header value

    Returns:
        Tuple of (successful_uploads, failed_uploads)
    """
    client = get_s3_client(
        endpoint_url, access_key_id, secret_access_key, max_pool_connections=max_workers
    )
    data_path = Path(data_dir)

    # Collect all files to upload
    files_to_upload = []
    for root, _, files in os.walk(data_path):
        for filename in files:
            local_path = Path(root) / filename
            relative_path = local_path.relative_to(data_path)
            key = f"{prefix}{relative_path}" if prefix else str(relative_path)
            key = key.removesuffix(".json")
            key = key.removesuffix("/index")
            files_to_upload.append((local_path, key))

    logger.info(f"Found {len(files_to_upload)} files to upload")

    successful = 0
    failed = 0
    uploaded_keys: set[str] = set()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                upload_file, client, bucket, local_path, key, cache_control
            ): key
            for local_path, key in files_to_upload
        }

        with tqdm(total=len(files_to_upload), desc="Uploading to S3") as pbar:
            for future in as_completed(futures):
                key = futures[future]
                try:
                    if future.result():
                        successful += 1
                        uploaded_keys.add(key)
                    else:
                        failed += 1
                except Exception as e:
                    logger.error(f"Upload failed for {key}: {e}")
                    failed += 1
                pbar.update(1)

    logger.info(f"Upload complete: {successful} succeeded, {failed} failed")

    # Clean up stale objects that are no longer in the dataset
    if uploaded_keys:
        delete_stale_objects(client, bucket, uploaded_keys, prefix)

    return successful, failed
