from datetime import datetime, timedelta, timezone
from pathlib import Path
import shutil
from uuid import UUID

from object_storage import R2Storage


STORAGE_DIRECTORY = Path(__file__).parent / "storage" / "jobs"
RETENTION_DAYS = 7


def remove_expired_job_directories(
    storage_directory: Path = STORAGE_DIRECTORY,
    *,
    now: datetime | None = None,
) -> list[Path]:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(days=RETENTION_DAYS)
    removed_directories: list[Path] = []

    if not storage_directory.exists():
        return removed_directories

    for job_directory in storage_directory.iterdir():
        if not job_directory.is_dir() or job_directory.is_symlink():
            continue

        last_updated = datetime.fromtimestamp(
            job_directory.stat().st_mtime,
            tz=timezone.utc,
        )
        if last_updated < cutoff:
            shutil.rmtree(job_directory)
            removed_directories.append(job_directory)

    return removed_directories


def remove_expired_r2_jobs(
    storage: R2Storage,
    *,
    now: datetime | None = None,
) -> list[str]:
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time - timedelta(days=RETENTION_DAYS)
    objects_by_job: dict[str, list[str]] = {}
    latest_change_by_job: dict[str, datetime] = {}

    for key, last_modified in storage.list_job_objects():
        parts = key.split("/", 2)
        if len(parts) != 3 or parts[0] != "jobs" or not parts[2]:
            continue
        try:
            job_id = str(UUID(parts[1]))
        except ValueError:
            continue
        if job_id != parts[1]:
            continue

        objects_by_job.setdefault(job_id, []).append(key)
        previous_change = latest_change_by_job.get(job_id)
        if previous_change is None or last_modified > previous_change:
            latest_change_by_job[job_id] = last_modified

    removed_jobs: list[str] = []
    for job_id, keys in objects_by_job.items():
        if latest_change_by_job[job_id] >= cutoff:
            continue
        for key in keys:
            storage.delete_object(key)
        removed_jobs.append(job_id)

    return removed_jobs
