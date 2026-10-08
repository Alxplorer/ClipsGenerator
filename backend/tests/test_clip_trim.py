import os
import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import HTTPException
from pydantic import ValidationError
from starlette.datastructures import Headers, UploadFile

from models import Clip, Job
from cleanup import remove_expired_job_directories


# Importar main crea clientes, pero estas pruebas no se conectan a los servicios.
# Los valores ficticios evitan depender de las credenciales locales de .env.
with patch.dict(
    os.environ,
    {
        "DATABASE_URL": "postgresql://test:test@localhost:5433/test",
        "REDIS_URL": "redis://localhost:6379/0",
        "OPENAI_API_KEY": "test-key",
    },
):
    from main import (
        ClipTrimRequest,
        get_job,
        retry_job,
        save_uploaded_video,
        validate_clip_trim,
        validate_uploaded_video,
    )
    from worker import error_kind


class ClipTrimTests(unittest.TestCase):
    def setUp(self) -> None:
        self.clip = Clip(
            id="clip-1",
            job_id="job-1",
            title="Ejemplo",
            editorial_reason="Ejemplo",
            start_seconds=120,
            end_seconds=155,
            decision="accepted",
        )

    def test_accepts_adjustment_inside_clip(self) -> None:
        request = ClipTrimRequest(start_seconds=125, end_seconds=150)

        self.assertIsNone(validate_clip_trim(self.clip, request))

    def test_rejects_start_before_clip(self) -> None:
        request = ClipTrimRequest(start_seconds=110, end_seconds=150)

        with self.assertRaises(HTTPException) as error:
            validate_clip_trim(self.clip, request)

        self.assertEqual(error.exception.status_code, 400)

    def test_rejects_end_after_clip(self) -> None:
        request = ClipTrimRequest(start_seconds=130, end_seconds=180)

        with self.assertRaises(HTTPException) as error:
            validate_clip_trim(self.clip, request)

        self.assertEqual(error.exception.status_code, 400)

    def test_rejects_end_equal_to_or_before_start(self) -> None:
        for end_seconds in (140, 130):
            with self.subTest(end_seconds=end_seconds):
                with self.assertRaises(ValidationError):
                    ClipTrimRequest(start_seconds=140, end_seconds=end_seconds)


class JobErrorTests(unittest.TestCase):
    def test_rejects_missing_job_with_localized_404(self) -> None:
        with patch("main.Session") as session:
            session.return_value.__enter__.return_value.get.return_value = None

            with self.assertRaises(HTTPException) as error:
                get_job("job-does-not-exist")

        self.assertEqual(error.exception.status_code, 404)
        self.assertEqual(error.exception.detail, "No se encontró el trabajo.")

    def test_rejects_retry_for_job_that_did_not_fail(self) -> None:
        job = Job(
            id="job-ready",
            original_filename="episodio.mp4",
            status="ready",
        )

        with patch("main.Session") as session:
            session.return_value.__enter__.return_value.get.return_value = job

            with self.assertRaises(HTTPException) as error:
                retry_job(job.id)

        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(
            error.exception.detail,
            "Solo se pueden reintentar trabajos que terminaron con error.",
        )


class ErrorLoggingTests(unittest.TestCase):
    def test_error_kind_omits_exception_message(self) -> None:
        error = RuntimeError("api-key-sk-test-key-must-not-be-logged")

        self.assertEqual(error_kind(error), "RuntimeError")
        self.assertNotIn("sk-test-key", error_kind(error))


class StorageCleanupTests(unittest.TestCase):
    def test_removes_expired_job_and_keeps_recent_job(self) -> None:
        now = datetime(2026, 9, 29, tzinfo=timezone.utc)

        with TemporaryDirectory() as temporary_directory:
            storage_directory = Path(temporary_directory)
            expired_job = storage_directory / "expired-job"
            recent_job = storage_directory / "recent-job"
            expired_job.mkdir()
            recent_job.mkdir()
            expired_timestamp = (now - timedelta(days=8)).timestamp()
            os.utime(expired_job, (expired_timestamp, expired_timestamp))

            removed_directories = remove_expired_job_directories(
                storage_directory,
                now=now,
            )

            self.assertEqual(removed_directories, [expired_job])
            self.assertFalse(expired_job.exists())
            self.assertTrue(recent_job.exists())


class UploadValidationTests(unittest.TestCase):
    @staticmethod
    def upload_file(filename: str, content_type: str) -> UploadFile:
        return UploadFile(
            filename=filename,
            file=BytesIO(),
            headers=Headers({"content-type": content_type}),
        )

    def test_accepts_mp4_extension_regardless_of_case(self) -> None:
        file = self.upload_file("episodio.MP4", "video/mp4")

        self.assertIsNone(validate_uploaded_video(file))

    def test_rejects_filename_without_mp4_extension(self) -> None:
        file = self.upload_file("episodio.mov", "video/mp4")

        with self.assertRaises(HTTPException) as error:
            validate_uploaded_video(file)

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "Selecciona un archivo MP4.")

    def test_rejects_non_mp4_content_type(self) -> None:
        file = self.upload_file("episodio.mp4", "application/octet-stream")

        with self.assertRaises(HTTPException) as error:
            validate_uploaded_video(file)

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "El archivo debe tener tipo video/mp4.")


class UploadStorageTests(unittest.IsolatedAsyncioTestCase):
    async def test_saves_valid_upload_with_original_content(self) -> None:
        file = UploadValidationTests.upload_file("episodio.mp4", "video/mp4")
        expected_content = b"abcd"
        file.file.write(expected_content)
        file.file.seek(0)

        with TemporaryDirectory() as temporary_directory:
            storage_directory = Path(temporary_directory)

            with (
                patch("main.STORAGE_DIRECTORY", storage_directory),
                patch("main.MAX_UPLOAD_BYTES", 10),
                patch("main.UPLOAD_CHUNK_BYTES", 2),
            ):
                source_video_path, file_size_bytes = await save_uploaded_video(
                    file,
                    "job-valid-upload",
                )

            self.assertEqual(
                source_video_path,
                storage_directory / "job-valid-upload" / "original.mp4",
            )
            self.assertEqual(file_size_bytes, len(expected_content))
            self.assertEqual(source_video_path.read_bytes(), expected_content)

    async def test_removes_partial_upload_when_size_limit_is_exceeded(self) -> None:
        file = UploadValidationTests.upload_file("episodio.mp4", "video/mp4")
        file.file.write(b"abcd")
        file.file.seek(0)

        with TemporaryDirectory() as temporary_directory:
            storage_directory = Path(temporary_directory)

            with (
                patch("main.STORAGE_DIRECTORY", storage_directory),
                patch("main.MAX_UPLOAD_BYTES", 3),
                patch("main.UPLOAD_CHUNK_BYTES", 2),
            ):
                with self.assertRaises(HTTPException) as error:
                    await save_uploaded_video(file, "job-exceeds-limit")

            self.assertEqual(error.exception.status_code, 413)
            self.assertFalse((storage_directory / "job-exceeds-limit").exists())


if __name__ == "__main__":
    unittest.main()
