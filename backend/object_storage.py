"""Shared R2 operations for files belonging to a job."""

from datetime import datetime
from pathlib import Path
from typing import Iterator, Literal
from uuid import UUID


def original_video_key(job_id: str) -> str:
    """Return the R2 key for one job's uploaded MP4."""
    normalized_job_id = str(UUID(job_id))
    return f"jobs/{normalized_job_id}/original.mp4"


def clip_object_key(
    job_id: str,
    clip_id: str,
    filename: Literal["clip.mp4", "subtitles.srt"],
    adjustment_id: str | None = None,
) -> str:
    prefix = f"jobs/{UUID(job_id)}/clips/{UUID(clip_id)}"
    if adjustment_id is not None:
        prefix += f"/adjustment/{UUID(adjustment_id)}"
    return f"{prefix}/{filename}"


class R2Storage:
    def __init__(self, bucket_name: str, client: object) -> None:
        self.bucket_name = bucket_name
        self.client = client

    @classmethod
    def connect(
        cls,
        *,
        account_id: str,
        bucket_name: str,
        access_key_id: str,
        secret_access_key: str,
    ) -> "R2Storage":
        import boto3

        client = boto3.client(
            "s3",
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name="auto",
        )
        return cls(bucket_name, client)

    def upload_file(self, local_path: Path, key: str) -> None:
        self.client.upload_file(str(local_path), self.bucket_name, key)

    def download_file(self, key: str, local_path: Path) -> None:
        self.client.download_file(self.bucket_name, key, str(local_path))

    def get_object(self, key: str, byte_range: str | None = None) -> dict:
        request = {"Bucket": self.bucket_name, "Key": key}
        if byte_range is not None:
            request["Range"] = byte_range
        return self.client.get_object(**request)

    def list_job_objects(self) -> Iterator[tuple[str, datetime]]:
        pages = self.client.get_paginator("list_objects_v2").paginate(
            Bucket=self.bucket_name,
            Prefix="jobs/",
        )
        for page in pages:
            for item in page.get("Contents", []):
                yield item["Key"], item["LastModified"]

    def delete_object(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket_name, Key=key)
