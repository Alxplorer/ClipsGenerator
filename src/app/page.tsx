// devuelve como una bienvenida a next  y dice que para iniciar editees  page.txs
export default function Home() {
  return (
    <div className="flex flex-col flex-1 items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex flex-1 w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <p className="text-sm font-semibold tracking-wide text-zinc-600">
          ClipsGenerator
        </p>
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-md text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            Convierte tu podcast en clips verticales listos para compartir.
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Con ClipsGenerator, ahorra tiempo y esfuerzo al crear clips de tus podcasts simplemente subiendo el archivo...
          </p>
        </div>
        <div className="flex flex-col gap-4 text-base font-medium sm:flex-row">
          <span className="rounded-full bg-zinc-100 px-5 py-3 text-zinc-800 dark:bg-zinc-900 dark:text-zinc-100">
            Podcasts en español
          </span>
          <span className="rounded-full border border-zinc-200 px-5 py-3 text-zinc-700 dark:border-zinc-800 dark:text-zinc-200">
            Clips 9:16 con subtítulos
          </span>
        </div>
      </main>
    </div>
  );
}
