from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
import shutil
from config import settings
from uuid import uuid4
from redis import Redis

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import Clip as ClipRecord
from models import Job as JobRecord
from models import Transcription as TranscriptionRecord
from pathlib import Path


MAX_UPLOAD_BYTES = 500 * 1024 * 1024
UPLOAD_CHUNK_BYTES = 1024 * 1024
STORAGE_DIRECTORY = Path(__file__).parent / "storage" / "jobs"

app = FastAPI()
engine = create_engine(settings.sqlalchemy_database_url)
redis_client = Redis.from_url(settings.redis_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=[],
    )

class Job(BaseModel):
    id: str
    status: Literal["uploaded", "transcribing", "generating", "ready", "error"]

class CreateJobRequest(BaseModel):
    original_filename: str
 
class TranscriptionResponse(BaseModel):
    text: str
    segments: list["TranscriptionSegment"]


class TranscriptionSegment(BaseModel):
    start_seconds: float
    end_seconds: float
    text: str


class ClipResponse(BaseModel):
    id: str
    title: str
    editorial_reason: str
    start_seconds: float
    end_seconds: float
    decision: str


class JobDetail(BaseModel):
    id: str
    original_filename: str
    status: Literal["uploaded", "transcribing", "generating", "ready", "error"]
    transcription: TranscriptionResponse | None
    clips: list[ClipResponse]

def validate_uploaded_video(file: UploadFile) -> None:
    if not file.filename or not file.filename.lower().endswith(".mp4"):
        raise HTTPException(
            status_code=400,
            detail="Selecciona un archivo MP4.",
        )

    if file.content_type != "video/mp4":
        raise HTTPException(
            status_code=400,
            detail="El archivo debe tener tipo video/mp4.",
        )

async def save_uploaded_video(
    file: UploadFile,
    job_id: str,
) -> tuple[Path, int]:
    job_directory = STORAGE_DIRECTORY / job_id
    source_video_path = job_directory / "original.mp4"
    job_directory.mkdir(parents=True, exist_ok=False)

    file_size_bytes = 0

    try:
        with source_video_path.open("wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                file_size_bytes += len(chunk)

                if file_size_bytes > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail="El archivo supera el límite de 500 MB.",
                    )

                destination.write(chunk)
    except Exception:
        shutil.rmtree(job_directory)
        raise

    return source_video_path, file_size_bytes

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/database")
def database_health() -> dict[str, str]:
    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

    return {"status": "ok"}

@app.post("/jobs", response_model=Job, status_code=201)
def create_job(request: CreateJobRequest) -> Job:
    job_id = str(uuid4())
    job = JobRecord(
        id=job_id,
        original_filename=request.original_filename,
        status="uploaded",
    )

    with Session(engine) as session:
        session.add(job)
        session.commit()

    redis_client.rpush("jobs", job_id)
    return Job(id=job_id, status="uploaded")

@app.get("/jobs/{job_id}", response_model=JobDetail)
def get_job(job_id: str) -> JobDetail:
    with Session(engine) as session:
        job = session.get(JobRecord, job_id)

        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        transcription_record = session.scalar(
            select(TranscriptionRecord).where(
                TranscriptionRecord.job_id == job_id
            )
        )
        clip_records = session.scalars(
            select(ClipRecord).where(ClipRecord.job_id == job_id)
        ).all()

        if transcription_record is None:
            transcription = None
        else:
            transcription = TranscriptionResponse(
                text=transcription_record.text,
                segments=[
                    TranscriptionSegment(**segment)
                    for segment in transcription_record.segments or []
                ],
            )

        clips = []
        for clip_record in clip_records:
            clips.append(
                ClipResponse(
                    id=clip_record.id,
                    title=clip_record.title,
                    editorial_reason=clip_record.editorial_reason,
                    start_seconds=clip_record.start_seconds,
                    end_seconds=clip_record.end_seconds,
                    decision=clip_record.decision,
                )
            )

        return JobDetail(
            id=job.id,
            original_filename=job.original_filename,
            status=job.status,
            transcription=transcription,
            clips=clips,
        )

@app.get("/health/queue")
def queue_health() -> dict[str, str]:
    redis_client.ping()
    return {"status": "ok"}

@app.post("/jobs/{job_id}/retry", response_model=Job)
def retry_job(job_id: str) -> Job:
    with Session(engine) as session:
        job = session.get(JobRecord, job_id)

        if job is None:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != "error":
            raise HTTPException(
                status_code=409,
                detail="Only failed jobs can be retried",
            )

        job.status = "uploaded"
        session.commit()

    redis_client.rpush("jobs", job_id)
    return Job(id=job_id, status="uploaded")

@app.post("/jobs/upload", response_model=Job, status_code=201)
async def upload_job(file: UploadFile = File(...)) -> Job:
    validate_uploaded_video(file)

    job_id = str(uuid4())
    source_video_path, file_size_bytes = await save_uploaded_video(
        file,
        job_id,
    )

    job = JobRecord(
        id=job_id,
        original_filename=file.filename,
        status="uploaded",
        source_video_path=str(source_video_path),
        file_size_bytes=file_size_bytes,
    )

    with Session(engine) as session:
        session.add(job)
        session.commit()

    redis_client.rpush("jobs", job_id)
    return Job(id=job_id, status="uploaded")
