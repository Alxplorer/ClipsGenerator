import os
import unittest
from io import BytesIO
from unittest.mock import patch
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from models import Base, Clip, Job


with patch.dict(
    os.environ,
    {
        "DATABASE_URL": "postgresql://test:test@localhost:5433/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "test-key",
    },
):
    from main import app


class FakeBody:
    def __init__(self, data: bytes) -> None:
        self.stream = BytesIO(data)
        self.closed = False

    def iter_chunks(self, chunk_size: int):
        while chunk := self.stream.read(chunk_size):
            yield chunk

    def close(self) -> None:
        self.closed = True
        self.stream.close()


class FakeR2:
    def __init__(self, key: str, data: bytes) -> None:
        self.key = key
        self.data = data
        self.requests: list[tuple[str, str | None]] = []
        self.last_body: FakeBody | None = None

    def get_object(self, key: str, byte_range: str | None = None) -> dict:
        self.requests.append((key, byte_range))
        assert key == self.key
        data = self.data
        response = {}
        if byte_range is not None:
            start, end = (int(value) for value in byte_range.removeprefix("bytes=").split("-"))
            data = data[start : end + 1]
            response["ContentRange"] = f"bytes {start}-{end}/{len(self.data)}"
        self.last_body = FakeBody(data)
        return {"Body": self.last_body, "ContentLength": len(data), **response}


class R2VideoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.job_id = str(uuid4())
        self.clip_id = str(uuid4())
        self.key = f"jobs/{self.job_id}/clips/{self.clip_id}/clip.mp4"
        self.storage = FakeR2(self.key, b"0123456789")
        with Session(self.engine) as session:
            session.add(Job(id=self.job_id, original_filename="episodio.mp4", status="ready"))
            session.add(Clip(
                id=self.clip_id,
                job_id=self.job_id,
                title="Ejemplo",
                editorial_reason="Ejemplo",
                start_seconds=0,
                end_seconds=30,
                decision="accepted",
                rendered_video_path="C:/api-only/clip.mp4",
                rendered_video_key=self.key,
            ))
            session.commit()
        self.engine_patch = patch("main.engine", self.engine)
        self.r2_patch = patch("main.r2_storage", self.storage)
        self.engine_patch.start()
        self.r2_patch.start()
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        self.r2_patch.stop()
        self.engine_patch.stop()
        self.engine.dispose()

    def test_streams_r2_clip_and_downloads_it(self) -> None:
        url = f"/jobs/{self.job_id}/clips/{self.clip_id}/video"
        playback = self.client.get(url)
        download = self.client.get(f"{url}?download=true")

        self.assertEqual(playback.status_code, 200)
        self.assertEqual(playback.content, b"0123456789")
        self.assertEqual(playback.headers["accept-ranges"], "bytes")
        self.assertEqual(download.content, b"0123456789")
        self.assertEqual(
            download.headers["content-disposition"],
            f'attachment; filename="clip-{self.clip_id}.mp4"',
        )
        self.assertEqual(self.storage.requests, [(self.key, None), (self.key, None)])
        self.assertTrue(self.storage.last_body.closed)

    def test_forwards_requested_range_to_r2(self) -> None:
        response = self.client.get(
            f"/jobs/{self.job_id}/clips/{self.clip_id}/video",
            headers={"Range": "bytes=2-5"},
        )

        self.assertEqual(response.status_code, 206)
        self.assertEqual(response.content, b"2345")
        self.assertEqual(response.headers["content-range"], "bytes 2-5/10")
        self.assertEqual(self.storage.requests, [(self.key, "bytes=2-5")])
        self.assertTrue(self.storage.last_body.closed)

    def test_missing_r2_object_returns_404(self) -> None:
        def missing_object(key: str, byte_range: str | None = None) -> dict:
            raise ClientError(
                {"Error": {"Code": "NoSuchKey", "Message": "missing"}},
                "GetObject",
            )

        self.storage.get_object = missing_object

        response = self.client.get(f"/jobs/{self.job_id}/clips/{self.clip_id}/video")

        self.assertEqual(response.status_code, 404)
