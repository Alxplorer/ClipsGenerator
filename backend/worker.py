import time

from redis import Redis
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config import settings
from models import Job as JobRecord

engine = create_engine(settings.sqlalchemy_database_url)
redis_client = Redis.from_url(settings.redis_url)


def process_job(job_id: str) -> None:
    try:
        with Session(engine) as session:
            job = session.get(JobRecord, job_id)

            if job is None:
                raise LookupError(f"Job {job_id} no existe")

            job.status = "transcribing"
            filename = job.original_filename
            session.commit()

        if filename == "provocar-error.mp4":
            raise RuntimeError("Error de prueba controlado")

        time.sleep(5)

        with Session(engine) as session:
            job = session.get(JobRecord, job_id)
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
