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

type ClipProposal = {
  id: number;
  title: string;
  duration: string;
  reason: string;
  decision: ClipDecision,
  durationSeconds: number;
};

const initialClips: ClipProposal[] = [
  {
    id: 1,
    title: 'El hábito que cambió nuestra audiencia',
    duration: '00:42',
    reason: 'Una idea práctica y fácil de compartir.',
    decision: 'pending',
    durationSeconds: 42,
  },
  {
    id: 2,
    title: 'Por qué dejamos de perseguir viralidad',
    duration: '00:31',
    reason: 'Una opinión clara que abre conversación.',
    decision: 'pending',
    durationSeconds: 31,
  },
  {
    id: 3,
    title: 'La pregunta que mejora cada entrevista',
    duration: '00:55',
    reason: 'Un consejo concreto para otros podcasters.',
    decision: 'pending',
    durationSeconds: 55,
  },
];

export default function Home() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [apiJob, setApiJob] = useState<ApiJob | null>(null);
  const [apiJobRequestStatus, setApiJobRequestStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle');
  const [apiJobError, setApiJobError] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [clips, setClips] = useState(initialClips);
  const [reviewClipId, setReviewClipId] = useState<number | null>(null);
  const [reviewStart, setReviewStart] = useState(0);
  const [reviewEnd, setReviewEnd] = useState(0);
  const [downloadMessage, setDownloadMessage] = useState<string | null>(null);
  const reviewClip = clips.find((clip) => clip.id === reviewClipId);

 async function createRealJob(event: FormEvent<HTMLFormElement>) {
  event.preventDefault();

  const formData = new FormData(event.currentTarget);
  const file = formData.get('file');

  if (!(file instanceof File) || file.size === 0) {
    setApiJobRequestStatus('error');
    setApiJobError('Selecciona un archivo MP4 antes de procesarlo.');
    return;
  }

  setSelectedFile(file);
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
  const jobId = apiJob?.id;
  const status = apiJob?.status;

  if (!jobId || status === 'ready' || status === 'error') {
    return;
  }

  async function loadJobStatus() {
    try {
      const response = await fetch(
        `http://localhost:8000/jobs/${jobId}`,
      );

      if (!response.ok) {
        throw new Error('No se pudo consultar el trabajo.');
      }

      const job: ApiJob = await response.json();
      setApiJob(job);
      setJobStatus(job.status);
    } catch {
      setApiJobRequestStatus('error');
    }
  }

  const intervalId = window.setInterval(() => {
    void loadJobStatus();
  }, 1000);

  return () => window.clearInterval(intervalId);
}, [apiJob?.id, apiJob?.status]);

function setClipDecision(id: number, decision: ClipDecision) {
  setClips((currentClips) =>
    currentClips.map((clip) =>
      clip.id === id ? { ...clip, decision } : clip,
    ),
  );
}

function openReview(clip: ClipProposal) {
  setReviewClipId(clip.id);
  setReviewStart(0);
  setReviewEnd(clip.durationSeconds);
  setDownloadMessage(null);
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
              disabled={apiJobRequestStatus === 'loading'}
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
            <button
    type="button"
    onClick={() => setClipDecision(clip.id, 'accepted')}
    className="rounded-full bg-emerald-600 px-4 py-2 text-sm font-semibold text-white"
  >
    Aceptar
  </button>

  <button
    type="button"
    onClick={() => setClipDecision(clip.id, 'discarded')}
    className="rounded-full border border-red-300 px-4 py-2 text-sm font-semibold text-red-700"
  >
    Descartar
  </button>

  {clip.decision === 'accepted' ? (
  <button
    type="button"
    onClick={() => openReview(clip)}
    className="ml-3 rounded-full bg-violet-700 px-4 py-2 text-sm font-semibold text-white"
  >
    Revisar clip
  </button>
) : null}
        </article>
      ))}
    </div>
  </section>
) : null}

{reviewClip && reviewClip.decision === 'accepted' ? (
  <section className="mt-10 rounded-xl border border-violet-200 bg-violet-50 p-6 text-left">
    <p className="text-sm font-semibold text-violet-700">Revisión simulada</p>
    <h2 className="mt-2 text-2xl font-bold">{reviewClip.title}</h2>

    <div className="mt-6 space-y-5">
      <label className="block font-semibold">
        Inicio: {reviewStart}s
        <input
          type="range"
          min="0"
          max={reviewEnd - 1}
          value={reviewStart}
          onChange={(event) => setReviewStart(Number(event.target.value))}
          className="mt-2 w-full"
        />
      </label>

      <label className="block font-semibold">
        Fin: {reviewEnd}s
        <input
          type="range"
          min={reviewStart + 1}
          max={reviewClip.durationSeconds}
          value={reviewEnd}
          onChange={(event) => setReviewEnd(Number(event.target.value))}
          className="mt-2 w-full"
        />
      </label>
    </div>

    <button
      type="button"
      onClick={() =>
        setDownloadMessage(
          'Simulación: el MP4 final todavía no se generó ni se descargó.',
        )
      }
      className="mt-6 rounded-full bg-violet-700 px-5 py-3 font-semibold text-white"
    >
      Descargar clip (simulado)
    </button>

    {downloadMessage ? (
      <p className="mt-4 text-sm text-violet-900" role="status">
        {downloadMessage}
      </p>
    ) : null}
  </section>
) : null}

        <p className="mt-4 text-sm text-zinc-500">
          Próximamente definiremos los límites de duración y tamaño.
        </p>
      </section>
    </main>
  );
}
