from typing import Literal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg
from config import settings

app = FastAPI()

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
 

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

@app.get("/health/database")
def database_health() -> dict[str, str]:
    with psycopg.connect(settings.database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

    return {"status": "ok"}

@app.get("/jobs/demo", response_model=Job)
def get_demo_job() -> Job:
    return Job(id="demo-job", status="uploaded")
