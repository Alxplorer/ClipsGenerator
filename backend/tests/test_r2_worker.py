import os
import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from models import Base, Clip, Job, Transcription


with patch.dict(
    os.environ,
    {
        "DATABASE_URL": "postgresql://test:test@localhost:5433/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "test-key",
    },
):
    from worker import ClipCandidate, ClipSuggestion, process_job, process_clip_adjustment


class FakeR2:
    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.downloaded_path: Path | None = None

    def download_file(self, key: str, local_path: Path) -> None:
        self.downloaded_path = local_path
        local_path.write_bytes(self.objects[key])

    def upload_file(self, local_path: Path, key: str) -> None:
        self.objects[key] = local_path.read_bytes()

    def delete_object(self, key: str) -> None:
        self.objects.pop(key, None)


class R2WorkerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        self.storage = FakeR2()
        self.job_id = str(uuid4())
        self.original_key = f"jobs/{self.job_id}/original.mp4"
        self.storage.objects[self.original_key] = b"MP4 original"
        with Session(self.engine) as session:
            session.add(Job(
                id=self.job_id,
                original_filename="episodio.mp4",
                status="uploaded",
                source_video_path="C:/api-only/original.mp4",
                source_video_key=self.original_key,
            ))
            session.commit()

    def tearDown(self) -> None:
        self.engine.dispose()

    def test_processes_from_r2_without_shared_disk(self) -> None:
        segments = [{"start_seconds": 0.0, "end_seconds": 30.0, "text": "Ejemplo"}]
        candidates = [
            ClipCandidate(
                id=f"candidate-{index}",
                start_seconds=index * 30,
                end_seconds=(index + 1) * 30,
                text="Ejemplo",
            )
            for index in range(3)
        ]
        suggestions = [
            ClipSuggestion(
                candidate_id=candidate.id,
                title=f"Título {index}",
                editorial_reason="Razón",
            )
            for index, candidate in enumerate(candidates)
        ]

        def fake_transcribe(path: str):
            self.assertEqual(Path(path).read_bytes(), b"MP4 original")
            return "Ejemplo", segments

        def fake_render(*, source_video_path, output_directory, **kwargs):
            self.assertEqual(source_video_path.read_bytes(), b"MP4 original")
            output_directory.mkdir(parents=True)
            (output_directory / "subtitles.srt").write_bytes(b"SRT")
            output = output_directory / "clip.mp4"
            output.write_bytes(b"MP4 vertical")
            return output

        with (
            patch("worker.engine", self.engine),
            patch("worker.r2_storage", self.storage),
            patch("worker.transcribe_video", side_effect=fake_transcribe),
            patch("worker.build_clip_candidates", return_value=candidates),
            patch("worker.select_clip_suggestions", return_value=suggestions),
            patch("worker.render_clip", side_effect=fake_render),
        ):
            process_job(self.job_id)

        with Session(self.engine) as session:
            job = session.get(Job, self.job_id)
            transcription = session.scalar(select(Transcription))
            clips = session.scalars(select(Clip)).all()
            self.assertEqual(job.status, "ready")
            self.assertEqual(transcription.text, "Ejemplo")
            self.assertEqual(len(clips), 3)
            for clip in clips:
                self.assertIsNotNone(clip.rendered_video_key)
                self.assertEqual(self.storage.objects[clip.rendered_video_key], b"MP4 vertical")
                subtitle_key = clip.rendered_video_key.replace("clip.mp4", "subtitles.srt")
                self.assertEqual(self.storage.objects[subtitle_key], b"SRT")
        self.assertFalse(self.storage.downloaded_path.exists())

    def prepare_adjustment(self) -> tuple[str, str, bytes]:
        clip_id = str(uuid4())
        adjustment_id = str(uuid4())
        previous_key = f"jobs/{self.job_id}/clips/{clip_id}/clip.mp4"
        self.storage.objects[previous_key] = b"MP4 anterior"
        with Session(self.engine) as session:
            session.add(Transcription(
                id=str(uuid4()),
                job_id=self.job_id,
                text="Ejemplo",
                segments=[{"start_seconds": 120.0, "end_seconds": 155.0, "text": "Ejemplo"}],
            ))
            session.add(Clip(
                id=clip_id,
                job_id=self.job_id,
                title="Título",
                editorial_reason="Razón",
                start_seconds=120.0,
                end_seconds=155.0,
                decision="accepted",
                adjustment_id=adjustment_id,
                adjustment_status="queued",
                rendered_video_key=previous_key,
            ))
            session.commit()
        payload = json.dumps({
            "type": "trim_clip",
            "job_id": self.job_id,
            "clip_id": clip_id,
            "adjustment_id": adjustment_id,
            "start_seconds": 125.0,
            "end_seconds": 150.0,
        }).encode("utf-8")
        return clip_id, previous_key, payload

    def render_adjustment(self, *, source_video_path, output_directory, **kwargs):
        self.assertEqual(source_video_path.read_bytes(), b"MP4 original")
        output_directory.mkdir(parents=True)
        (output_directory / "subtitles.srt").write_bytes(b"SRT nuevo")
        output = output_directory / "clip.mp4"
        output.write_bytes(b"MP4 ajustado")
        return output

    def test_publishes_adjustment_after_both_assets_exist(self) -> None:
        clip_id, previous_key, payload = self.prepare_adjustment()
        with (
            patch("worker.engine", self.engine),
            patch("worker.r2_storage", self.storage),
            patch("worker.render_clip", side_effect=self.render_adjustment),
        ):
            process_clip_adjustment(payload)

        with Session(self.engine) as session:
            clip = session.get(Clip, clip_id)
            self.assertEqual(clip.adjustment_status, "ready")
            self.assertEqual((clip.start_seconds, clip.end_seconds), (125.0, 150.0))
            self.assertNotEqual(clip.rendered_video_key, previous_key)
            self.assertEqual(self.storage.objects[previous_key], b"MP4 anterior")
            self.assertEqual(self.storage.objects[clip.rendered_video_key], b"MP4 ajustado")
            subtitle_key = clip.rendered_video_key.replace("clip.mp4", "subtitles.srt")
            self.assertEqual(self.storage.objects[subtitle_key], b"SRT nuevo")
            self.assertIsNone(clip.rendered_video_path)
        self.assertFalse(self.storage.downloaded_path.exists())

    def test_failed_adjustment_keeps_previous_publication(self) -> None:
        clip_id, previous_key, payload = self.prepare_adjustment()
        original_upload = self.storage.upload_file

        def fail_after_upload(local_path: Path, key: str) -> None:
            original_upload(local_path, key)
            if key.endswith("clip.mp4"):
                raise RuntimeError("fallo simulado")

        self.storage.upload_file = fail_after_upload
        with (
            patch("worker.engine", self.engine),
            patch("worker.r2_storage", self.storage),
            patch("worker.render_clip", side_effect=self.render_adjustment),
        ):
            process_clip_adjustment(payload)

        with Session(self.engine) as session:
            clip = session.get(Clip, clip_id)
            self.assertEqual(clip.adjustment_status, "error")
            self.assertEqual((clip.start_seconds, clip.end_seconds), (120.0, 155.0))
            self.assertEqual(clip.rendered_video_key, previous_key)
        self.assertEqual(self.storage.objects[previous_key], b"MP4 anterior")
        self.assertEqual(set(self.storage.objects), {self.original_key, previous_key})

    def test_local_adjustment_keeps_published_file(self) -> None:
        clip_id, _, payload = self.prepare_adjustment()
        with TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "original.mp4"
            source_path.write_bytes(b"MP4 original")
            with Session(self.engine) as session:
                job = session.get(Job, self.job_id)
                job.source_video_key = None
                job.source_video_path = str(source_path)
                clip = session.get(Clip, clip_id)
                clip.rendered_video_key = None
                session.commit()

            with (
                patch("worker.engine", self.engine),
                patch("worker.r2_storage", None),
                patch("worker.render_clip", side_effect=self.render_adjustment),
            ):
                process_clip_adjustment(payload)

            with Session(self.engine) as session:
                clip = session.get(Clip, clip_id)
                self.assertEqual(clip.adjustment_status, "ready")
                self.assertIsNone(clip.rendered_video_key)
                self.assertEqual(Path(clip.rendered_video_path).read_bytes(), b"MP4 ajustado")


if __name__ == "__main__":
    unittest.main()
