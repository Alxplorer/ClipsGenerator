from typing import Literal, Self

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, model_validator
import json
import psycopg
import shutil
from config import settings
from uuid import uuid4
from redis import Redis
from redis.exceptions import RedisError

from sqlalchemy import create_engine, select, update
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
    adjustment_id: str | None = None
    adjustment_status: Literal["queued", "rendering", "ready", "error"] | None = None


class ClipDecisionRequest(BaseModel):
    decision: Literal["accepted", "discarded"]


class ClipTrimRequest(BaseModel):
    start_seconds: float = Field(ge=0, allow_inf_nan=False)
    end_seconds: float = Field(ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def validate_interval(self) -> Self:
        if self.end_seconds <= self.start_seconds:
            raise ValueError("El fin debe ser mayor que el inicio.")
        return self


class ClipTrimValidationResponse(BaseModel):
    id: str
    start_seconds: float
    end_seconds: float


class ClipTrimQueuedResponse(BaseModel):
    id: str
    adjustment_id: str
    status: Literal["queued"]
    start_seconds: float
    end_seconds: float


class ClipDecisionResponse(BaseModel):
    id: str
    decision: Literal["accepted", "discarded"]


class JobDetail(BaseModel):
    id: str
    original_filename: str
    status: Literal["uploaded", "transcribing", "generating", "ready", "error"]
    transcription: TranscriptionResponse | None
    clips: list[ClipResponse]


def validate_clip_trim(clip: ClipRecord, request: ClipTrimRequest) -> None:
    if (
        request.start_seconds < clip.start_seconds
        or request.end_seconds > clip.end_seconds
    ):
        raise HTTPException(
            status_code=400,
            detail="El ajuste debe quedar dentro del intervalo actual del clip.",
        )


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
                    adjustment_id=clip_record.adjustment_id,
                    adjustment_status=clip_record.adjustment_status,
                )
            )

        return JobDetail(
            id=job.id,
            original_filename=job.original_filename,
            status=job.status,
            transcription=transcription,
            clips=clips,
        )

@app.get("/jobs/{job_id}/clips/{clip_id}/video", response_class=FileResponse)
def get_clip_video(job_id: str, clip_id: str, download: bool = False) -> FileResponse:
    with Session(engine) as session:
        job = session.get(JobRecord, job_id)
        clip = session.get(ClipRecord, clip_id)

        if job is None or clip is None or clip.job_id != job_id:
            raise HTTPException(status_code=404, detail="No se encontró el clip.")

        if clip.rendered_video_path is not None:
            video_path = Path(clip.rendered_video_path)
        elif job.source_video_path is not None:
            video_path = Path(job.source_video_path).parent / "clips" / clip.id / "clip.mp4"
        else:
            raise HTTPException(status_code=404, detail="El video no está disponible.")

    if not video_path.is_file():
        raise HTTPException(status_code=404, detail="El video no está disponible.")

    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"clip-{clip_id}.mp4" if download else None,
        headers={"Cache-Control": "no-store"},
    )


@app.post(
    "/jobs/{job_id}/clips/{clip_id}/decision",
    response_model=ClipDecisionResponse,
)
def save_clip_decision(
    job_id: str,
    clip_id: str,
    request: ClipDecisionRequest,
) -> ClipDecisionResponse:
    with Session(engine) as session:
        clip = session.get(ClipRecord, clip_id)

        if clip is None or clip.job_id != job_id:
            raise HTTPException(status_code=404, detail="No se encontró el clip.")

        clip.decision = request.decision
        session.commit()

    return ClipDecisionResponse(id=clip_id, decision=request.decision)


@app.post(
    "/jobs/{job_id}/clips/{clip_id}/trim/validate",
    response_model=ClipTrimValidationResponse,
)
def validate_clip_trim_request(
    job_id: str,
    clip_id: str,
    request: ClipTrimRequest,
) -> ClipTrimValidationResponse:
    with Session(engine) as session:
        clip = session.get(ClipRecord, clip_id)

        if clip is None or clip.job_id != job_id:
            raise HTTPException(status_code=404, detail="No se encontró el clip.")

        validate_clip_trim(clip, request)

    return ClipTrimValidationResponse(
        id=clip_id,
        start_seconds=request.start_seconds,
        end_seconds=request.end_seconds,
    )


@app.post(
    "/jobs/{job_id}/clips/{clip_id}/trim",
    response_model=ClipTrimQueuedResponse,
    status_code=202,
)
def enqueue_clip_trim(
    job_id: str,
    clip_id: str,
    request: ClipTrimRequest,
) -> ClipTrimQueuedResponse:
    with Session(engine) as session:
        job = session.get(JobRecord, job_id)
        clip = session.get(ClipRecord, clip_id, with_for_update=True)

        if job is None or clip is None or clip.job_id != job_id:
            raise HTTPException(status_code=404, detail="No se encontró el clip.")

        if job.status != "ready" or clip.decision != "accepted":
            raise HTTPException(
                status_code=409,
                detail="Solo puedes ajustar un clip aceptado de un trabajo listo.",
            )

        validate_clip_trim(clip, request)

        if clip.adjustment_status in ("queued", "rendering"):
            raise HTTPException(
                status_code=409,
                detail="Este clip ya tiene un ajuste en curso.",
            )

        adjustment_id = str(uuid4())
        clip.adjustment_id = adjustment_id
        clip.adjustment_status = "queued"
        session.commit()

    task = {
        "type": "trim_clip",
        "job_id": job_id,
        "clip_id": clip_id,
        "adjustment_id": adjustment_id,
        **request.model_dump(),
    }
    try:
        redis_client.rpush("clip_adjustments", json.dumps(task))
    except RedisError as error:
        with Session(engine) as session:
            session.execute(
                update(ClipRecord)
                .where(
                    ClipRecord.id == clip_id,
                    ClipRecord.adjustment_id == adjustment_id,
                    ClipRecord.adjustment_status == "queued",
                )
                .values(adjustment_status="error")
            )
            session.commit()
        raise HTTPException(
            status_code=503,
            detail="No se pudo encolar el ajuste. Inténtalo de nuevo.",
        ) from error

    return ClipTrimQueuedResponse(
        id=clip_id,
        adjustment_id=adjustment_id,
        status="queued",
        start_seconds=request.start_seconds,
        end_seconds=request.end_seconds,
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
