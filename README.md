# ClipsGenerator

Aplicación local que recibe un podcast en MP4, lo procesa en segundo plano y
propone clips verticales con subtítulos para revisión y descarga.

## Requisitos

- Docker Desktop en ejecución.
- Python 3.13 o compatible.
- Node.js y npm.
- FFmpeg y FFprobe instalados. Consulta [backend/README.md](backend/README.md)
  si necesitas configurar sus rutas explícitas.
- Una clave de OpenAI para transcribir y seleccionar propuestas reales.

## Configuración inicial

Desde la raíz del proyecto, crea tu configuración local a partir del ejemplo:

```powershell
Copy-Item backend/.env.example backend/.env
```

Edita `backend/.env`. Cambia `POSTGRES_PASSWORD` por una contraseña local y usa
la misma contraseña dentro de `DATABASE_URL`. Añade tu `OPENAI_API_KEY`. No
subas este archivo a Git.

## Iniciar los servicios

Abre tres terminales desde la raíz del proyecto.

### 1. Base de datos y cola

```powershell
docker compose up -d
```

### 2. API y worker

En la primera ejecución, prepara el entorno del backend:

```powershell
Set-Location backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\alembic.exe upgrade head
```

Después inicia la API en una terminal:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload
```

En otra terminal, inicia el worker:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe worker.py
```

El worker procesa la cola y elimina cada 24 horas los trabajos cuyos archivos
lleven más de siete días sin cambios, tanto en el disco local como en R2 cuando
está configurado.

### 3. Interfaz web

```powershell
Set-Location frontend
npm ci
npm run dev
```

Abre [http://localhost:3000](http://localhost:3000).

## Verificación local

Con los servicios iniciados, comprueba salud de API, PostgreSQL y Redis:

```powershell
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/health/database
Invoke-RestMethod http://localhost:8000/health/queue
```

Ejecuta las pruebas del backend:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Y revisa el frontend:

```powershell
Set-Location frontend
npm run lint
```

## Recorrido de producto

1. En la web, selecciona un archivo MP4 de hasta 500 MB y pulsa **Procesar
   video**.
2. La URL conserva `?job=<id>` para volver al trabajo sin repetir la subida.
3. La tarjeta progresa por `uploaded`, `transcribing`, `generating` y `ready`.
   Un error muestra un mensaje para corregir la acción.
4. En `ready`, reproduce una propuesta, acepta o descarta cada clip y ajusta
   inicio y fin dentro del intervalo original si lo necesitas.
5. Espera el estado del ajuste y descarga el MP4 final desde la tarjeta.

Los videos originales, subtítulos y resultados se conservan durante siete días
desde el último cambio de su trabajo. Después, el enlace temporal deja de
entregar el archivo.

## Detener los servicios

Detén la API, el worker y Next.js con `Ctrl+C` en sus terminales. Para detener
PostgreSQL y Redis sin borrar sus datos:

```powershell
docker compose stop
```
