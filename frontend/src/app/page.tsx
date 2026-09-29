'use client';

import { type FormEvent, useEffect, useState } from 'react';

type JobStatus = 'uploaded' | 'transcribing' | 'generating' | 'ready' | 'error';

type ApiJob = {
  id: string;
  status: JobStatus;
};

const statusLabels: Record<JobStatus, string> = {
  uploaded: 'Video subido',
  transcribing: 'Transcribiendo el episodio',
  generating: 'Generando clips',
  ready: 'Clips listos para revisar',
  error: 'Ocurrió un error al procesar el video',
};

type ClipDecision = 'pending' | 'accepted' | 'discarded';
type AdjustmentStatus = 'queued' | 'rendering' | 'ready' | 'error';

const adjustmentLabels: Record<AdjustmentStatus, string> = {
  queued: 'Ajuste en cola',
  rendering: 'Generando el clip ajustado…',
  ready: 'Ajuste listo para reproducir y descargar',
  error: 'El ajuste falló. La versión anterior sigue disponible.',
};

type ApiClip = {
  id: string;
  title: string;
  editorial_reason: string;
  start_seconds: number;
  end_seconds: number;
  decision: ClipDecision;
  adjustment_id: string | null;
  adjustment_status: AdjustmentStatus | null;
};

type ApiJobDetail = ApiJob & {
  clips: ApiClip[];
};

type ClipProposal = {
  id: string;
  title: string;
  duration: string;
  reason: string;
  decision: ClipDecision,
  durationSeconds: number;
  startSeconds: number;
  endSeconds: number;
  adjustmentId: string | null;
  adjustmentStatus: AdjustmentStatus | null;
};

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [apiJob, setApiJob] = useState<ApiJob | null>(null);
  const [apiJobRequestStatus, setApiJobRequestStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [apiJobError, setApiJobError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [clips, setClips] = useState<ClipProposal[]>([]);
  const [reviewClipId, setReviewClipId] = useState<string | null>(null);
  const [savingClipId, setSavingClipId] = useState<string | null>(null);
  const [clipDecisionError, setClipDecisionError] = useState<string | null>(null);
  const [reviewStart, setReviewStart] = useState(0);
  const [reviewEnd, setReviewEnd] = useState(0);
  const [savingAdjustmentId, setSavingAdjustmentId] = useState<string | null>(null);
  const [adjustmentError, setAdjustmentError] = useState<string | null>(null);
  const reviewClip = clips.find((clip) => clip.id === reviewClipId);
  const hasPendingAdjustments = clips.some(
    (clip) => clip.adjustmentStatus === 'queued' || clip.adjustmentStatus === 'rendering',
  );
  const reviewAdjustmentStatus = reviewClip?.adjustmentStatus;
  const isReviewBusy = savingAdjustmentId !== null
    || reviewAdjustmentStatus === 'queued' || reviewAdjustmentStatus === 'rendering';

 async function createRealJob(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();

  const formData = new FormData(event.currentTarget);
  const file = formData.get('file');

  if (!(file instanceof File) || file.size === 0) {
    setApiJobRequestStatus('error');
    setApiJobError('Selecciona un archivo MP4 antes de procesarlo.');
    return;
  }

  const pageUrl = new URL(window.location.href);
  pageUrl.searchParams.delete('job');
  window.history.replaceState(null, '', pageUrl);

  setSelectedFile(file);
  setApiJob(null);
  setJobStatus(null);
  setClips([]);
  setReviewClipId(null);
  setClipDecisionError(null);
  setAdjustmentError(null);
  setApiJobRequestStatus('loading');
  setApiJobError(null);

  try {
    const response = await fetch('http://localhost:8000/jobs/upload', {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorResponse = (await response.json()) as { detail?: string };

      throw new Error(
        errorResponse.detail ?? 'No se pudo subir el video.',
      );
    }

    const job: ApiJob = await response.json();
    pageUrl.searchParams.set('job', job.id);
    window.history.replaceState(null, '', pageUrl);
    setApiJob(job);
    setJobStatus(job.status);
    setApiJobRequestStatus('ready');
  } catch (error) {
    setApiJobRequestStatus('error');
    setApiJobError(
      error instanceof Error ? error.message : 'No se pudo subir el video.',
    );
  }
}

useEffect(() => {
  const jobId = apiJob?.id ?? new URLSearchParams(window.location.search).get('job');
  const status = apiJob?.status;

  if (!jobId || (status === 'ready' && !hasPendingAdjustments) || status === 'error') {
    return;
  }

  let isActive = true;

  async function loadJobStatus() {
    try {
      const response = await fetch(
        `http://localhost:8000/jobs/${jobId}`,
      );

      if (!response.ok) {
        throw new Error('No se pudo consultar el trabajo.');
      }

      const job: ApiJobDetail = await response.json();
      if (!isActive) return;

      setApiJob(job);
      setJobStatus(job.status);
      setApiJobRequestStatus('ready');
      setApiJobError(null);
      setAdjustmentError(null);

      if (job.status === 'ready') {
        const updatedReviewClip = job.clips.find((clip) => clip.id === reviewClipId);
        if (
          (reviewAdjustmentStatus === 'queued' || reviewAdjustmentStatus === 'rendering')
          && updatedReviewClip?.adjustment_status === 'ready'
        ) {
          setReviewStart(0);
          setReviewEnd(updatedReviewClip.end_seconds - updatedReviewClip.start_seconds);
        }

        setClips(job.clips.map((clip) => {
          const durationSeconds = clip.end_seconds - clip.start_seconds;

          return {
            id: clip.id,
            title: clip.title,
            reason: clip.editorial_reason,
            duration: `${durationSeconds.toFixed(1)} s`,
            durationSeconds,
            startSeconds: clip.start_seconds,
            endSeconds: clip.end_seconds,
            adjustmentId: clip.adjustment_id,
            adjustmentStatus: clip.adjustment_status,
            decision: clip.decision,
          };
        }));
      }
    } catch {
      if (!isActive) return;
      if (hasPendingAdjustments) {
        setAdjustmentError('No se pudo consultar el ajuste. Volveremos a intentarlo.');
        return;
      }
      window.clearInterval(intervalId);
      setApiJobRequestStatus('error');
      setApiJobError('No se pudo consultar el trabajo. Comprueba el enlace e inténtalo de nuevo.');
    }
  }

  const intervalId = window.setInterval(() => {
    void loadJobStatus();
  }, 1000);

  void loadJobStatus();

  return () => {
    isActive = false;
    window.clearInterval(intervalId);
  };
}, [apiJob?.id, apiJob?.status, hasPendingAdjustments, reviewClipId, reviewAdjustmentStatus]);

async function setClipDecision(id: string, decision: 'accepted' | 'discarded') {
  if (!apiJob || savingClipId !== null) return;

  setSavingClipId(id);
  setClipDecisionError(null);

  try {
    const response = await fetch(
      `http://localhost:8000/jobs/${apiJob.id}/clips/${id}/decision`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ decision }),
      },
    );

    if (!response.ok) {
      throw new Error('No se pudo guardar la decisión. Inténtalo de nuevo.');
    }

    const saved: { id: string; decision: ClipDecision } = await response.json();
    setClips((currentClips) =>
      currentClips.map((clip) =>
        clip.id === saved.id ? { ...clip, decision: saved.decision } : clip,
      ),
    );
  } catch (error) {
    setClipDecisionError(
      error instanceof Error ? error.message : 'No se pudo guardar la decisión.',
    );
  } finally {
    setSavingClipId(null);
  }
}

async function saveClipAdjustment() {
  if (!apiJob || !reviewClip || isReviewBusy) return;

  const startSeconds = reviewClip.startSeconds + reviewStart;
  const endSeconds = Math.min(
    reviewClip.endSeconds,
    reviewClip.startSeconds + reviewEnd,
  );
  if (endSeconds <= startSeconds) {
    setAdjustmentError('El fin debe quedar después del inicio.');
    return;
  }

  setSavingAdjustmentId(reviewClip.id);
  setAdjustmentError(null);

  try {
    const response = await fetch(
      `http://localhost:8000/jobs/${apiJob.id}/clips/${reviewClip.id}/trim`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          start_seconds: startSeconds,
          end_seconds: endSeconds,
        }),
      },
    );

    if (!response.ok) {
      const errorResponse = (await response.json()) as { detail?: unknown };
      throw new Error(
        typeof errorResponse.detail === 'string'
          ? errorResponse.detail
          : 'No se pudo solicitar el ajuste. Inténtalo de nuevo.',
      );
    }

    const queued: { id: string; adjustment_id: string; status: 'queued' } =
      await response.json();
    setClips((currentClips) => currentClips.map((clip) =>
      clip.id === queued.id
        ? { ...clip, adjustmentId: queued.adjustment_id, adjustmentStatus: queued.status }
        : clip,
    ));
  } catch (error) {
    setAdjustmentError(
      error instanceof Error ? error.message : 'No se pudo solicitar el ajuste.',
    );
  } finally {
    setSavingAdjustmentId(null);
  }
}

function openReview(clip: ClipProposal) {
  setReviewClipId(clip.id);
  setReviewStart(0);
  setReviewEnd(clip.durationSeconds);
  setAdjustmentError(null);
}

  return (
    <main className="min-h-screen bg-zinc-50 px-6 py-16 text-zinc-900">
      <section className="mx-auto max-w-2xl text-center">
        <p className="text-sm font-semibold text-violet-700">ClipsGenerator</p>

        <h1 className="mt-4 text-4xl font-bold tracking-tight">
          Convierte tu podcast en clips listos para compartir.
        </h1>

        <p className="mt-4 text-lg text-zinc-600">
          Sube un episodio en MP4 y recibe propuestas de clips verticales con subtítulos.
        </p>

        <section className="mt-4 rounded-lg bg-violet-50 px-4 py-3 text-sm text-violet-900" aria-live="polite">
          <p className="font-semibold">Trabajo real desde FastAPI</p>
          {apiJobRequestStatus === 'idle' ? (
            <p>Selecciona un MP4 para crear un trabajo real.</p>
          ) : null}
          {apiJobRequestStatus === 'loading' ? <p>Creando trabajo…</p> : null}
          {apiJobRequestStatus === 'error' ? (
            <p>{apiJobError ?? 'No se pudo subir el video.'}</p>
          ) : null}
          {apiJobRequestStatus === 'ready' && apiJob ? (
            <p>Trabajo {apiJob.id}: {statusLabels[apiJob.status]}</p>
          ) : null}

        </section>

        <div className="mt-10 rounded-2xl border-2 border-dashed border-violet-300 bg-white p-10">
          <div className="text-4xl" aria-hidden="true">↑</div>

          <h2 className="mt-4 text-xl font-semibold">
            Sube tu video MP4
          </h2>

          <div className="mt-4 flex gap-3">

</div>

          <p className="mt-2 text-zinc-600">
            Arrastra el archivo aquí o selecciónalo desde tu computadora.
          </p>

          <form className="mt-6" onSubmit={createRealJob}>
            <input
              id="video-upload"
              name="file"
              type="file"
              accept="video/mp4"
              className="block w-full rounded-lg border border-violet-300 bg-white p-3 text-sm"
              onClick={(event) => {
                event.currentTarget.value = '';
              }}
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setSelectedFile(file);
                setApiJob(null);
                setApiJobRequestStatus('idle');
                setApiJobError(null);
                setJobStatus(null);
              }}
            />

            <button
              type="submit"
              disabled={apiJobRequestStatus === 'loading' || savingClipId !== null}
              className="mt-4 rounded-full bg-violet-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-60"
            >
              {apiJobRequestStatus === 'loading'
                ? 'Subiendo video…'
                : 'Procesar video'}
            </button>
          </form>

          {selectedFile ? (
            <p className="mt-4 text-sm text-zinc-700">
              Seleccionaste: {selectedFile.name} (
              {(selectedFile.size / 1024 / 1024).toFixed(1)} MB)
            </p>
          ) : null}

        {jobStatus ? (
        <p className="mt-4 rounded-lg bg-violet-50 px-4 py-3 text-sm font-semibold text-violet-900">
          Estado: {statusLabels[jobStatus]}
        </p>
        ) : null}

        </div>
        {jobStatus === 'ready' ? (
  <section className="mt-10 text-left">
    <h2 className="text-2xl font-bold">Clips propuestos</h2>
    <p className="mt-2 text-zinc-600">
      Revisa cada propuesta y decide cuáles quieres conservar.
    </p>
    {clipDecisionError ? (
      <p role="alert" className="mt-3 text-sm text-red-700">{clipDecisionError}</p>
    ) : null}

    <div className="mt-5 space-y-4">
      {clips.map((clip) => (
        <article
          key={clip.id}
          className="rounded-xl border border-zinc-200 bg-white p-5"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <h3 className="font-semibold">{clip.title}</h3>
              <p className="mt-1 text-sm text-zinc-500">
                Duración: {clip.duration}
              </p>
            </div>

            <span className="rounded-full bg-zinc-100 px-3 py-1 text-xs font-semibold text-zinc-700">
              {clip.decision === 'pending'
  ? 'Pendiente'
  : clip.decision === 'accepted'
    ? 'Aceptado'
    : 'Descartado'}
            </span>
          </div>

          <p className="mt-4 text-sm text-zinc-600">{clip.reason}</p>
          {clip.adjustmentStatus ? (
            <p className="mt-2 text-sm text-violet-700" role="status">
              {adjustmentLabels[clip.adjustmentStatus]}
            </p>
          ) : null}
          <video
            controls
            playsInline
            preload="metadata"
            aria-label={`Vista previa de ${clip.title}`}
            src={`http://localhost:8000/jobs/${apiJob?.id}/clips/${clip.id}/video?version=${clip.startSeconds}-${clip.endSeconds}`}
            className="mx-auto my-4 aspect-[9/16] w-full max-w-xs rounded-lg bg-black"
          >
            Tu navegador no admite la reproducción de video.
          </video>
            <button
    type="button"
    onClick={() => void setClipDecision(clip.id, 'accepted')}
    disabled={savingClipId !== null}
    className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
  >
    Aceptar
  </button>

  <button
    type="button"
    onClick={() => void setClipDecision(clip.id, 'discarded')}
    disabled={savingClipId !== null}
    className="rounded-full border border-red-300 px-4 py-2 text-sm font-semibold text-red-700 disabled:opacity-50"
  >
    Descartar
  </button>
  {savingClipId === clip.id ? (
    <p role="status" className="mt-2 text-sm text-zinc-600">Guardando decisión…</p>
  ) : null}

  {clip.decision === 'accepted' ? (
  <>
  <button
    type="button"
    onClick={() => openReview(clip)}
    className="ml-3 rounded-full bg-violet-700 px-4 py-2 text-sm font-semibold text-white"
  >
    Revisar clip
  </button>
  <a
    href={`http://localhost:8000/jobs/${apiJob?.id}/clips/${clip.id}/video?download=true&version=${clip.startSeconds}-${clip.endSeconds}`}
    className="ml-3 inline-block rounded-full border border-violet-300 px-4 py-2 text-sm font-semibold text-violet-700"
  >
    {clip.adjustmentStatus === 'queued' || clip.adjustmentStatus === 'rendering'
      ? 'Descargar versión actual'
      : 'Descargar clip'}
  </a>
  </>
) : null}
        </article>
      ))}
    </div>
  </section>
) : null}

{reviewClip && reviewClip.decision === 'accepted' ? (
  <section className="mt-10 rounded-xl border border-violet-200 bg-violet-50 p-6 text-left">
    <p className="text-sm font-semibold text-violet-700">Revisión del clip</p>
    <h2 className="mt-2 text-2xl font-bold">{reviewClip.title}</h2>

    <div className="mt-6 space-y-5">
      <label className="block font-semibold">
        Inicio dentro del clip: {reviewStart.toFixed(2)} s
        <input
          type="range"
          min="0"
          max={reviewEnd - 1}
          value={reviewStart}
          step="0.01"
          disabled={isReviewBusy}
          onChange={(event) => setReviewStart(Number(event.target.value))}
          className="mt-2 w-full"
        />
      </label>

      <label className="block font-semibold">
        Fin dentro del clip: {reviewEnd.toFixed(2)} s
        <input
          type="range"
          min={reviewStart + 1}
          max={reviewClip.durationSeconds}
          value={reviewEnd}
          step="0.01"
          disabled={isReviewBusy}
          onChange={(event) => setReviewEnd(Number(event.target.value))}
          className="mt-2 w-full"
        />
      </label>
    </div>

    {reviewClip.adjustmentStatus ? (
      <p className="mt-4 text-sm text-violet-700" role="status">
        {adjustmentLabels[reviewClip.adjustmentStatus]}
      </p>
    ) : null}
    {adjustmentError ? (
      <p className="mt-4 text-sm text-red-700" role="alert">{adjustmentError}</p>
    ) : null}

    <button
      type="button"
      onClick={() => void saveClipAdjustment()}
      disabled={isReviewBusy || (reviewStart === 0 && reviewEnd === reviewClip.durationSeconds)}
      className="mt-6 rounded-full bg-violet-700 px-5 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
    >
      {savingAdjustmentId === reviewClip.id ? 'Enviando ajuste…' : 'Guardar ajuste'}
    </button>

    <a
      href={`http://localhost:8000/jobs/${apiJob?.id}/clips/${reviewClip.id}/video?download=true&version=${reviewClip.startSeconds}-${reviewClip.endSeconds}`}
      className="ml-3 inline-block rounded-full border border-violet-300 px-5 py-3 font-semibold text-violet-700"
    >
      {isReviewBusy ? 'Descargar versión actual' : 'Descargar clip'}
    </a>
  </section>
) : null}

        <p className="mt-4 text-sm text-zinc-500">
          Próximamente definiremos los límites de duración y tamaño.
        </p>
      </section>
    </main>
  );
}
