# ClipsGenerator

Aplicación web que recibe un podcast en MP4, lo procesa en segundo plano y
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

## Preparación para Render

Para las demostraciones se publicarán frontend y API en Render, PostgreSQL en
Neon y la cola en Render Key Value. El worker se ejecutará en la PC del creador,
con FFmpeg y acceso a los mismos datos y archivos en R2. La PC debe estar
encendida y el worker activo para procesar videos y ejecutar la limpieza.
El despliegue público completo todavía está pendiente.

Cada comando se ejecuta desde
la **carpeta raíz del servicio** indicada aquí, no desde la raíz del repositorio.

| Servicio | Tipo y carpeta raíz | Build | Antes de iniciar | Arranque o publicación |
| --- | --- | --- | --- | --- |
| Frontend | Static Site, `frontend` | `npm ci && npm run build` | — | Publicar `out`; no usa `npm start` |
| API | Web Service Python, `backend` | `pip install -r requirements.txt` | `alembic upgrade head` | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Worker | Proceso local Python, `backend` | Instalar dependencias en `.venv` según la guía local | — | `.\.venv\Scripts\python.exe worker.py` |

Configura `NODE_VERSION=22.18.0` para el build del frontend y
`PYTHON_VERSION=3.13.2` en la API; el worker usa Python local. Son las versiones usadas en la
verificación local; fijarlas evita depender de los valores por defecto de Render.

Configura `NEXT_PUBLIC_API_BASE_URL` en el **build del frontend** con la URL HTTPS
real de la API, sin barra final. Next.js incorpora su valor en los archivos
generados; al cambiarlo hay que volver a construir el sitio. Para la API,
configura `FRONTEND_ORIGIN` con el origen HTTPS real del frontend, también sin
barra final, para CORS. Son direcciones distintas: la primera es el destino de
las peticiones; la segunda identifica la página que las envía.

La API necesita `DATABASE_URL`, `REDIS_URL`, `FRONTEND_ORIGIN` y las cuatro
variables R2 (`R2_ACCOUNT_ID`, `R2_BUCKET_NAME`, `R2_ACCESS_KEY_ID`,
`R2_SECRET_ACCESS_KEY`). El worker necesita `DATABASE_URL`, `REDIS_URL`,
`OPENAI_API_KEY` y las mismas variables R2. Ambas piezas deben usar el mismo
PostgreSQL de Neon, instancia Key Value y bucket R2. La API usará la URL interna
de Key Value en Oregon; el worker de la PC usa la URL externa `rediss://` con
TLS y contraseña, permitiendo su IP pública en las reglas de acceso. Si cambia
esa IP, actualiza la regla. Guarda los secretos de la API en Render y los del
worker en `backend/.env`, ignorado por Git. La URL de Neon incluye sus parámetros
de conexión cifrada. `NEON_DATABASE_URL`, si existe en el .env, es solo auxiliar:
la aplicación lee `DATABASE_URL`.

Con el plan Free de la API, ejecuta las migraciones desde la PC antes de publicar
código que necesite cambios de esquema, usando `DATABASE_URL` de Neon:
`.\.venv\Scripts\python.exe -m alembic upgrade head` desde `backend`.
El worker usa FFmpeg y FFprobe instalados en la PC, según `PATH` o las variables
`FFMPEG_PATH` y `FFPROBE_PATH`.

Los planes gratuitos tienen límites: Key Value pierde la cola al reiniciarse,
la API Free se duerme por inactividad y Render limita transferencia y builds.
Neon y R2 tienen cuotas; R2 cobra excedentes. Ejecutar el worker localmente evita
su costo de hosting, pero OpenAI sigue facturando por uso.

### Comprobación previa al despliegue

Render define `RENDER=true` automáticamente. En ese entorno, API y worker
rechazan el arranque si falta R2 o si `DATABASE_URL` o `REDIS_URL` apuntan a
`localhost`; la API exige `FRONTEND_ORIGIN` HTTPS y el worker exige
`OPENAI_API_KEY`. El build del frontend también exige una
`NEXT_PUBLIC_API_BASE_URL` HTTPS pública. En local se conservan los valores por
defecto para desarrollar sin Render.

Una subida con R2 usa el disco de la API solo como archivo temporal: tras subir
el original, la API borra esa copia y guarda únicamente `source_video_key` en
PostgreSQL. El worker descarga el video desde R2 a su propio temporal. Las
pruebas del backend simulan esos servicios separados, además de rechazar rutas
locales al simular Render:

```powershell
Set-Location backend
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Para repetir la exportación estática con valores ficticios, usa una terminal de
PowerShell nueva desde `frontend` y ciérrala después de la prueba:

```powershell
$env:RENDER = 'true'
$env:NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com'
npm run build
```

El resultado debe incluir `out/index.html`. Si se omite la URL pública al
simular Render, el build debe fallar. Estos comandos no conectan con R2 ni
crean servicios; las credenciales y la conectividad reales se comprobarán al
desplegar.

## Detener los servicios

Detén la API, el worker y Next.js con `Ctrl+C` en sus terminales. Para detener
PostgreSQL y Redis sin borrar sus datos:

```powershell
docker compose stop
```
