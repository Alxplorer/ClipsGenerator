from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
from config import settings
from uuid import uuid4

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from models import Clip as ClipRecord
from models import Job as JobRecord
from models import Transcription as TranscriptionRecord

app = FastAPI()
engine = create_engine(settings.sqlalchemy_database_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=[],
    )


class Job(BaseModel):
    id: str
    status: Literal["uploaded", "transcribing", "generating", "ready", "error"]

class CreateJobRequest(BaseModel):
    original_filename: str
 
class TranscriptionResponse(BaseModel):
    text: str


class ClipResponse(BaseModel):
    id: str
    title: str
    start_seconds: float
    end_seconds: float
    decision: str


class JobDetail(BaseModel):
    id: str
    original_filename: str
    status: Literal["uploaded", "transcribing", "generating", "ready", "error"]
    transcription: TranscriptionResponse | None
    clips: list[ClipResponse]

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
    job = JobRecord(
        id=str(uuid4()),
        original_filename=request.original_filename,
        status="uploaded",
    )

    with Session(engine) as session:
        session.add(job)
        session.commit()
        return Job(id=job.id, status=job.status)

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
                text=transcription_record.text
            )

        clips = []
        for clip_record in clip_records:
            clips.append(
                ClipResponse(
                    id=clip_record.id,
                    title=clip_record.title,
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
