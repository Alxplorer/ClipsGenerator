# Mapa de archivos — ClipsGenerator

Este documento registra cada elemento existente en el repositorio. Se actualiza
cada vez que se crea, mueve, elimina o se aprende un archivo/carpeta. `known`
solo se usa cuando Alex lo explica con sus propias palabras; `parked` indica una
explicación inicial pendiente de exploración; `generated` identifica salidas que
una herramienta crea y que no se editan manualmente.

| Ruta | Tipo | Estado | Qué es y por qué existe |
| --- | --- | --- | --- |
| `learning/` | Carpeta | parked | Carpeta de documentos vivos que guardan el contexto, plan y aprendizaje del proyecto. |
| `learning/project.md` | Archivo Markdown | parked | Definición del producto, alcance del MVP, v2 y mapa principal; evita desviarse de la meta. |
| `learning/plan.md` | Archivo Markdown | parked | Decisiones técnicas confirmadas y etapas de construcción; ordena el aprendizaje. |
| `learning/knowledge-graph.md` | Archivo Markdown | parked | Registro dinámico de conceptos, estados y evidencia; decide qué debe enseñarse o evaluarse. |
| `learning/file-map.md` | Archivo Markdown | parked | Este índice de archivos y carpetas; impide que la estructura del repositorio sea una caja negra. |
| `learning/data-model.md` | Archivo Markdown | known | Esquema acordado de trabajo, transcripción y clip; Alex definió sus relaciones mediante `job_id` antes de crear PostgreSQL. |
| `/` (raíz del repositorio) | Carpeta | parked | Contenedor principal de todo el código y documentación de ClipsGenerator. |
| `docker-compose.yml` | Configuración Docker | known | Receta creada por Alex para ejecutar PostgreSQL 17 en un contenedor, cargar la configuración local de `backend/.env`, conservar los datos en `postgres_data` y publicar el puerto local 5433 hacia el 5432 interno. |
| `frontend/` | Carpeta | known | Aplicación web de Next.js; Alex explicó que su posición permite distinguirla del futuro backend. |
| `backend/` | Carpeta | parked | Aplicación Python que contendrá la API de FastAPI; hoy solo aloja el servidor de prueba. |
| `backend/main.py` | Archivo Python | known | Punto de entrada de FastAPI; carga y valida `DATABASE_URL` desde `backend/.env`, permite CORS solo para el frontend local y expone `GET /health`, `GET /health/database` y `GET /jobs/demo`. La ruta de base de datos usa `psycopg` y `SELECT 1` para comprobar una conexión real. |
| `backend/config.py` | Archivo Python | known | Intermediario de configuración creado por Alex: lee `backend/.env`, valida `DATABASE_URL` y entrega una variante para SQLAlchemy sin duplicar secretos. |
| `backend/models.py` | Archivo Python | known | Describe mediante SQLAlchemy las tablas `jobs`, `transcriptions` y `clips`, incluidas sus claves primarias, foráneas y la restricción uno a uno de la transcripción. |
| `backend/alembic.ini` | Configuración generada | parked | Configuración base de Alembic; no contiene la URL secreta, que se inyecta temporalmente desde `config.py`. |
| `backend/migrations/` | Carpeta de migraciones | known | Infraestructura de Alembic que conecta la metadata de los modelos con PostgreSQL; guarda migraciones versionadas en `versions/`. |
| `backend/migrations/versions/213902a44b70_create_initial_schema.py` | Migración | known | Primera migración revisada por Alex: crea `jobs`, `clips` y `transcriptions`, y puede deshacerlas en orden seguro. |
| `backend/.env` | Configuración local secreta | known | Archivo local creado por Alex con las credenciales de PostgreSQL y `DATABASE_URL`; no se copia al código fuente ni se versiona. |
| `backend/.gitignore` | Configuración de Git | known | Indica que `backend/.env` y la caché generada `__pycache__/` no deben entrar al historial de Git cuando el backend se versiona. |
| `backend/.venv/` | Entorno Python generado | parked | Copia aislada de Python y sus dependencias para este backend; no se edita manualmente ni se debe versionar. |
| `frontend/src/app/page.tsx` | Archivo TypeScript/React | known | Página inicial (`/`); Alex construyó una simulación completa: selección local de MP4, estados, propuestas, decisiones y revisión con descarga explícitamente simulada. Incluye un bloque que consulta `GET /jobs/demo` y muestra carga, error o el estado real recibido de la API local. |
| `frontend/src/app/layout.tsx` | Archivo TypeScript/React | parked | Marco HTML compartido por las páginas de la aplicación. |
| `frontend/src/app/globals.css` | Archivo CSS | parked | Estilos globales de la aplicación. |
| `frontend/package.json` | Archivo JSON | parked | Declara dependencias y scripts, incluido `npm run dev`. |
| `frontend/package-lock.json` | Archivo JSON generado | parked | Fija las versiones exactas de las dependencias instaladas por npm. |
| `frontend/tsconfig.json` | Archivo JSON | parked | Reglas con las que TypeScript interpreta el proyecto. |
| `frontend/next.config.ts`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs`, `frontend/next-env.d.ts` | Configuración | parked | Ajustes auxiliares generados para Next.js, linting, CSS y tipos. |
| `frontend/public/` y `frontend/src/app/favicon.ico` | Recursos estáticos | parked | Iconos e imágenes de ejemplo que la plantilla muestra o puede servir. |
| `frontend/.gitignore` | Archivo de configuración | known | Indica a Git qué archivos generados o locales no debe seguir; Alex explicó por qué ignora `node_modules/`. |
| `frontend/.git/` | Metadatos de Git generados | parked | Historial local y configuración del remoto `origin`, que apunta a GitHub; contiene el commit inicial y el hito `Personaliza la página inicial`. |
| `frontend/node_modules/` | Dependencias generadas | parked | Copias descargadas de paquetes; no se editan a mano ni se versionan. |
| `frontend/.next/` | Caché generada | parked | Salida temporal creada por Next.js durante el desarrollo. |
| `frontend/README.md`, `frontend/AGENTS.md`, `frontend/CLAUDE.md` | Documentación | parked | Instrucciones y notas generadas que exploraremos solo cuando sean necesarias. |
