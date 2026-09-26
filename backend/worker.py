from pathlib import Path
import subprocess
from pydantic import BaseModel
from uuid import uuid4

from openai import OpenAI
from redis import Redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config import settings
from models import Job as JobRecord
from models import Transcription as TranscriptionRecord

engine = create_engine(settings.sqlalchemy_database_url)
redis_client = Redis.from_url(settings.redis_url)
MAX_TRANSCRIPTION_BYTES = 25 * 1024 * 1024

class ClipSuggestion(BaseModel):
    title: str
    editorial_reason: str
    start_seconds: float
    end_seconds: float


class ClipSuggestions(BaseModel):
    clips: list[ClipSuggestion]

def ensure_audio_stream(source_video_path: Path) -> None:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "a:0",
                "-show_entries",
                "stream=codec_type",
                "-of",
                "csv=p=0",
                str(source_video_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("FFprobe no está disponible para revisar el video.") from error

    if result.stdout.strip() != "audio":
        raise ValueError("El MP4 no contiene una pista de audio para transcribir.")


def extract_audio(source_video_path: Path) -> Path:
    audio_path = source_video_path.with_name("transcription.mp3")
    audio_path.unlink(missing_ok=True)

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(source_video_path),
                "-map",
                "0:a:0",
                "-vn",
                "-ac",
                "1",
                "-ar",
                "16000",
                "-b:a",
                "64k",
                str(audio_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        audio_path.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg no está disponible para extraer el audio.") from error
    except subprocess.CalledProcessError as error:
        audio_path.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg no pudo extraer el audio del MP4.") from error

    return audio_path


def transcribe_video(source_video_path: str) -> tuple[str, list[dict[str, float | str]]]:
    video_path = Path(source_video_path)

    if not video_path.is_file():
        raise FileNotFoundError("El archivo de video guardado ya no existe.")

    ensure_audio_stream(video_path)
    audio_path = extract_audio(video_path)

    try:
        if audio_path.stat().st_size > MAX_TRANSCRIPTION_BYTES:
            raise ValueError(
                "El audio supera los 25 MB permitidos por la API de transcripción."
            )

        client = OpenAI(api_key=settings.openai_api_key.get_secret_value())

        with audio_path.open("rb") as audio_file:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="es",
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )
    finally:
        audio_path.unlink(missing_ok=True)

    segments = [
        {
            "start_seconds": segment.start,
            "end_seconds": segment.end,
            "text": segment.text.strip(),
        }
        for segment in result.segments or []
    ]
    return result.text, segments


def process_job(job_id: str) -> None:
    try:
        with Session(engine) as session:
            job = session.get(JobRecord, job_id)

            if job is None:
                raise LookupError(f"Job {job_id} no existe")

            job.status = "transcribing"
            filename = job.original_filename
            source_video_path = job.source_video_path
            session.commit()

        if filename == "provocar-error.mp4":
            raise RuntimeError("Error de prueba controlado")

        if source_video_path is None:
            raise FileNotFoundError("El trabajo no tiene una ruta de video.")

        text, segments = transcribe_video(source_video_path)

        with Session(engine) as session:
            job = session.get(JobRecord, job_id)
            transcription = session.scalar(
                select(TranscriptionRecord).where(
                    TranscriptionRecord.job_id == job_id
                )
            )

            if transcription is None:
                transcription = TranscriptionRecord(
                    id=str(uuid4()),
                    job_id=job_id,
                    text=text,
                    segments=segments,
                )
                session.add(transcription)
            else:
                transcription.text = text
                transcription.segments = segments

            job.status = "ready"
            session.commit()

    except Exception as error:
        with Session(engine) as session:
            job = session.get(JobRecord, job_id)

            if job is not None:
                job.status = "error"
                session.commit()

        print(f"El trabajo {job_id} falló: {error}")

def run_worker() -> None:
    while True:
        queued_job = redis_client.blpop("jobs", timeout=1)

        if queued_job is None:
            continue

        _, job_id_as_bytes = queued_job
        job_id = job_id_as_bytes.decode("utf-8")
        process_job(job_id)


if __name__ == "__main__":
    run_worker()
