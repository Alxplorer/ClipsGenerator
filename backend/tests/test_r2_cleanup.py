import unittest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from cleanup import remove_expired_r2_jobs
from object_storage import R2Storage


class FakePaginator:
    def __init__(self, pages: list[dict]) -> None:
        self.pages = pages

    def paginate(self, *, Bucket: str, Prefix: str):
        assert Bucket == "test-bucket"
        assert Prefix == "jobs/"
        yield from self.pages


class FakeClient:
    def __init__(self, objects: dict[str, datetime]) -> None:
        self.objects = objects
        self.deleted: list[str] = []

    def get_paginator(self, operation: str) -> FakePaginator:
        assert operation == "list_objects_v2"
        items = [
            {"Key": key, "LastModified": modified}
            for key, modified in self.objects.items()
            if key.startswith("jobs/")
        ]
        return FakePaginator([
            {"Contents": items[:2]},
            {"Contents": items[2:]},
        ])

    def delete_object(self, *, Bucket: str, Key: str) -> None:
        assert Bucket == "test-bucket"
        self.deleted.append(Key)
        del self.objects[Key]


class R2CleanupTests(unittest.TestCase):
    def test_preserves_recently_changed_job_and_deletes_expired_job(self) -> None:
        now = datetime(2026, 10, 7, tzinfo=timezone.utc)
        recent_job = str(uuid4())
        expired_job = str(uuid4())
        old = now - timedelta(days=8)
        recent = now - timedelta(days=1)
        recent_original = f"jobs/{recent_job}/original.mp4"
        recent_adjustment = f"jobs/{recent_job}/clips/{uuid4()}/adjustment/{uuid4()}/clip.mp4"
        expired_original = f"jobs/{expired_job}/original.mp4"
        expired_clip = f"jobs/{expired_job}/clips/{uuid4()}/clip.mp4"
        invalid_key = "jobs/not-a-uuid/original.mp4"
        client = FakeClient({
            recent_original: old,
            expired_original: old,
            invalid_key: old,
            recent_adjustment: recent,
            expired_clip: old,
        })
        storage = R2Storage("test-bucket", client)

        removed = remove_expired_r2_jobs(storage, now=now)

        self.assertEqual(removed, [expired_job])
        self.assertEqual(client.deleted, [expired_original, expired_clip])
        self.assertIn(recent_original, client.objects)
        self.assertIn(recent_adjustment, client.objects)
        self.assertIn(invalid_key, client.objects)
