import os
import unittest
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from starlette.datastructures import Headers, UploadFile

from models import Base, Job


with patch.dict(
    os.environ,
    {
        "DATABASE_URL": "postgresql://test:test@localhost:5433/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "test-key",
    },
):
    from main import upload_job


class FakeR2:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}

    def upload_file(self, local_path: Path, key: str) -> None:
        self.objects[key] = local_path.read_bytes()

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)


class FakeRedis:
    def __init__(self, engine, storage: FakeR2) -> None:
        self.engine = engine
        self.storage = storage
        self.messages: list[tuple[str, str]] = []

    def rpush(self, queue: str, job_id: str) -> None:
        with Session(self.engine) as session:
            job = session.get(Job, job_id)
            assert job is not None
            assert job.source_video_key in self.storage.objects
        self.messages.append((queue, job_id))


class R2UploadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.storage = FakeR2()
        self.redis = FakeRedis(self.engine, self.storage)

    def tearDown(self) -> None:
        self.engine.dispose()

    @staticmethod
    def video() -> UploadFile:
        return UploadFile(
            file=BytesIO(b"MP4 de prueba"),
            filename="episodio.mp4",
            headers=Headers({"content-type": "video/mp4"}),
        )

    async def test_uploads_before_saving_and_queueing_job(self) -> None:
        with TemporaryDirectory() as temporary_directory:
            with (
                patch("main.STORAGE_DIRECTORY", Path(temporary_directory)),
                patch("main.engine", self.engine),
                patch("main.redis_client", self.redis),
                patch("main.r2_storage", self.storage),
            ):
                response = await upload_job(self.video())

            with Session(self.engine) as session:
                job = session.get(Job, response.id)
                self.assertIsNotNone(job)
                self.assertEqual(job.source_video_key, f"jobs/{response.id}/original.mp4")
                self.assertEqual(self.storage.objects[job.source_video_key], b"MP4 de prueba")
            self.assertEqual(self.redis.messages, [("jobs", response.id)])

    async def test_failed_r2_upload_does_not_save_or_queue_job(self) -> None:
        def fail_upload(local_path: Path, key: str) -> None:
            self.storage.objects[key] = local_path.read_bytes()
            raise RuntimeError("fallo simulado")

        self.storage.upload_file = fail_upload
        with TemporaryDirectory() as temporary_directory:
            with (
                patch("main.STORAGE_DIRECTORY", Path(temporary_directory)),
                patch("main.engine", self.engine),
                patch("main.redis_client", self.redis),
                patch("main.r2_storage", self.storage),
            ):
                with self.assertRaises(HTTPException) as error:
                    await upload_job(self.video())

            self.assertEqual(error.exception.status_code, 503)
            self.assertEqual(list(Path(temporary_directory).iterdir()), [])
            with Session(self.engine) as session:
                self.assertEqual(session.scalars(select(Job)).all(), [])
            self.assertEqual(self.redis.messages, [])
            self.assertEqual(self.storage.objects, {})


if __name__ == "__main__":
    unittest.main()
