from pathlib import Path
import subprocess
import json
from pydantic import BaseModel
from uuid import uuid4

from openai import OpenAI
from redis import Redis
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from config import settings
from models import Job as JobRecord
from models import Transcription as TranscriptionRecord
from models import Clip as ClipRecord

engine = create_engine(settings.sqlalchemy_database_url)
redis_client = Redis.from_url(settings.redis_url)
MAX_TRANSCRIPTION_BYTES = 25 * 1024 * 1024
MIN_CLIP_SECONDS = 20
TARGET_CLIP_SECONDS = 35
MAX_CLIP_SECONDS = 60
MAX_CANDIDATES = 60

class ClipSuggestion(BaseModel):
    candidate_id: str
    title: str
    editorial_reason: str

class ClipSuggestions(BaseModel):
    clips: list[ClipSuggestion]

class ClipCandidate(BaseModel):
    id: str
    start_seconds: float
    end_seconds: float
    text: str

def build_clip_candidates(
    segments: list[dict[str, float | str]],
) -> list[ClipCandidate]:
    if not segments:
        raise ValueError("No hay segmentos para construir candidatas.")

    step = max(1, (len(segments) + MAX_CANDIDATES - 1) // MAX_CANDIDATES)
    candidates = []

    for start_index in range(0, len(segments), step):
        start_seconds = float(segments[start_index]["start_seconds"])
        end_seconds = start_seconds
        candidate_text_parts = []

        for segment in segments[start_index:]:
            end_seconds = float(segment["end_seconds"])
            candidate_text_parts.append(str(segment["text"]).strip())

            if end_seconds - start_seconds >= TARGET_CLIP_SECONDS:
                break

        duration = end_seconds - start_seconds
        text = " ".join(part for part in candidate_text_parts if part)

        if (
            MIN_CLIP_SECONDS <= duration <= MAX_CLIP_SECONDS
            and text
        ):
            candidates.append(
                ClipCandidate(
                    id=f"candidate-{start_index}",
                    start_seconds=start_seconds,
                    end_seconds=end_seconds,
                    text=text,
                )
            )

        if len(candidates) == MAX_CANDIDATES:
            break

    return candidates

def select_clip_suggestions(
    candidates: list[ClipCandidate],
) -> list[ClipSuggestion]:
    client = OpenAI(api_key=settings.openai_api_key.get_secret_value())

    completion = client.chat.completions.parse(
        model="gpt-5.6-terra",
        messages=[
            {
                "role": "system",
                "content": (
                    "Selecciona entre 3 y 8 candidatas de clips para un podcast "
                    "en español. Elige momentos interesantes y comprensibles por "
                    "sí mismos. Evita saludos, despedidas y anuncios. "
                    "Devuelve el candidate_id exactamente como aparece en la lista. "
                    "No inventes candidate_id ni devuelvas tiempos."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "candidates": [
                            candidate.model_dump()
                            for candidate in candidates
                        ]
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        response_format=ClipSuggestions,
    )

    suggestions = completion.choices[0].message.parsed

    if suggestions is None:
        raise RuntimeError("OpenAI no devolvió propuestas de clips.")

    return suggestions.clips

def filter_clip_suggestions(
    suggestions: list[ClipSuggestion],
    candidates: list[ClipCandidate],
) -> list[ClipSuggestion]:
    candidate_ids = {candidate.id for candidate in candidates}
    selected_candidate_ids = set()
    valid_suggestions = []

    for suggestion in suggestions:
        has_known_candidate = suggestion.candidate_id in candidate_ids
        is_not_duplicate = suggestion.candidate_id not in selected_candidate_ids
        has_required_text = (
            bool(suggestion.title.strip())
            and bool(suggestion.editorial_reason.strip())
        )

        if has_known_candidate and is_not_duplicate and has_required_text:
            valid_suggestions.append(suggestion)
            selected_candidate_ids.add(suggestion.candidate_id)

    if len(valid_suggestions) < 3:
        raise ValueError("No quedaron al menos 3 propuestas válidas.")

    return valid_suggestions[:8]

def format_srt_timestamp(seconds: float) -> str:
    total_milliseconds = round(seconds * 1000)
    hours = total_milliseconds // 3_600_000
    minutes = (total_milliseconds // 60_000) % 60
    whole_seconds = (total_milliseconds // 1000) % 60
    milliseconds = total_milliseconds % 1000

    return f"{hours:02d}:{minutes:02d}:{whole_seconds:02d},{milliseconds:03d}"


def build_clip_subtitle_segments(
    segments: list[dict[str, float | str]],
    clip_start: float,
    clip_end: float,
) -> list[dict[str, float | str]]:
    clip_segments = []

    for segment in segments:
        start = max(float(segment["start_seconds"]), clip_start)
        end = min(float(segment["end_seconds"]), clip_end)

        if start >= end:
            continue

        clip_segments.append(
            {
                "start_seconds": start - clip_start,
                "end_seconds": end - clip_start,
                "text": str(segment["text"]).strip(),
            }
        )

    return clip_segments


def write_clip_subtitles(
    segments: list[dict[str, float | str]],
    clip_start: float,
    clip_end: float,
    subtitle_path: Path,
) -> None:
    clip_segments = build_clip_subtitle_segments(segments, clip_start, clip_end)
    entries = []

    for index, segment in enumerate(clip_segments, start=1):
        start = format_srt_timestamp(float(segment["start_seconds"]))
        end = format_srt_timestamp(float(segment["end_seconds"]))
        entries.append(f"{index}\n{start} --> {end}\n{segment['text']}\n\n")

    subtitle_path.write_text("".join(entries), encoding="utf-8")


def render_clip(
    source_video_path: Path,
    segments: list[dict[str, float | str]],
    clip_start: float,
    clip_end: float,
    output_directory: Path,
) -> Path:
    if clip_start < 0 or clip_end <= clip_start:
        raise ValueError("El intervalo del clip no es válido.")

    source_video_path = source_video_path.resolve()
    output_directory = output_directory.resolve()
    output_directory.mkdir(parents=True, exist_ok=True)
    subtitle_path = output_directory / "subtitles.srt"
    output_path = output_directory / "clip.mp4"
    write_clip_subtitles(segments, clip_start, clip_end, subtitle_path)

    video_filters = (
        "scale=1080:1920:force_original_aspect_ratio=increase:force_divisible_by=2,"
        "crop=1080:1920,setsar=1,"
        "subtitles=filename=subtitles.srt:force_style='"
        "PlayResX=1080,PlayResY=1920,FontName=Arial,FontSize=56,"
        "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
        "Outline=3,Shadow=0,Alignment=2,MarginV=140,MarginL=80,MarginR=80'"
    )

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-hide_banner",
                "-loglevel", "error",
                "-y",
                "-ss", str(clip_start),
                "-i", str(source_video_path),
                "-t", str(clip_end - clip_start),
                "-map", "0:v:0",
                "-map", "0:a:0",
                "-vf", video_filters,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-movflags", "+faststart",
                str(output_path),
            ],
            cwd=output_directory,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError("FFmpeg no está disponible para renderizar el clip.") from error
    except subprocess.CalledProcessError as error:
        output_path.unlink(missing_ok=True)
        raise RuntimeError("FFmpeg no pudo renderizar el clip.") from error

    return output_path


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

            job.status = "generating"
            session.commit()

        candidates = build_clip_candidates(segments)
        suggestions = select_clip_suggestions(candidates)
        suggestions = filter_clip_suggestions(suggestions, candidates)
        candidates_by_id = {
            candidate.id: candidate
            for candidate in candidates
        }

        clips = []
        for suggestion in suggestions:
            candidate = candidates_by_id[suggestion.candidate_id]
            clip = ClipRecord(
                id=str(uuid4()),
                job_id=job_id,
                title=suggestion.title,
                editorial_reason=suggestion.editorial_reason,
                start_seconds=candidate.start_seconds,
                end_seconds=candidate.end_seconds,
                decision="pending",
            )
            render_clip(
                source_video_path=Path(source_video_path),
                segments=segments,
                clip_start=clip.start_seconds,
                clip_end=clip.end_seconds,
                output_directory=Path(source_video_path).parent / "clips" / clip.id,
            )
            clips.append(clip)

        with Session(engine) as session:
            job = session.get(JobRecord, job_id)
            session.add_all(clips)
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
