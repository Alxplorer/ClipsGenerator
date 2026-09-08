# Grafo de conocimiento — ClipsGenerator

Este archivo es la fuente de verdad sobre lo que Alex **realmente sabe**. Se
actualiza tras cada lección, práctica, explicación propia o quiz. Una entrada
solo avanza con evidencia concreta: una respuesta de Alex, código escrito o una
prueba realizada. Los conceptos `understood` revisados recientemente no se
evalúan de nuevo salvo que se necesiten como requisito de un concepto nuevo.

**Estados:** `seed` → `introduced` → `practicing` → `understood`.

| Concepto | Estado | Introduced date | Last-reviewed date | Evidencia |
| --- | --- | --- | --- | --- |
| Frontend | introduced | 2026-08-20 | 2026-09-03 | Alex explicó el flujo `input` → `onChange` → `setSelectedFile` → render de React → JSX muestra el nombre del archivo, y que el frontend no procesa clips en ese momento. |
| Backend | introduced | 2026-08-20 | 2026-09-03 | Alex explicó que crea trabajos con id y estado, puede persistirlos, proteger claves privadas y continuar el procesamiento aunque se cierre el navegador. |
| Cola de trabajos | introduced | 2026-08-20 | 2026-09-03 | Alex explicó que la cola guarda la tarea de un trabajo creado para que el worker la procese después de que el usuario ya recibió respuesta. |
| Worker de procesamiento | introduced | 2026-08-20 | 2026-09-03 | Alex explicó que el worker toma una tarea de la cola, transcribe el episodio y actualiza el trabajo a `transcribing` mientras lo ejecuta. |
| TypeScript | introduced | 2026-08-20 | 2026-09-03 | Alex explicó que `JobStatus` impide valores arbitrarios y que TypeScript detecta un estado no permitido antes de ejecutar o compilar. |
| Arquitectura de dos lenguajes | introduced | 2026-08-20 | 2026-08-20 | Alex explicó: TypeScript para frontend y Python para backend. |
| Next.js | introduced | 2026-08-20 | 2026-09-03 | Alex explicó la convención del App Router: `src/app/page.tsx` corresponde a `/` y `src/app/clips/page.tsx` correspondería a `/clips`. |
| FastAPI | introduced | 2026-08-20 | 2026-09-03 | Alex explicó que `GET /jobs/demo` es una ruta conectada con `get_demo_job`, que devuelve el JSON `{\"id\": \"demo-job\", \"status\": \"uploaded\"}`. |
| PostgreSQL | practicing | 2026-08-20 | 2026-09-07 | Alex explicó el recorrido de `GET /health/database`: FastAPI usa `DATABASE_URL`, `psycopg` conecta por `localhost:5433`, Docker redirige al PostgreSQL interno en 5432 y `SELECT 1` confirma la conexión antes de devolver JSON. |
| Almacenamiento de archivos | introduced | 2026-08-20 | 2026-08-20 | Alex explicó que los MP4 no van a la base de datos por su peso. |
| Hosting | introduced | 2026-08-20 | 2026-08-20 | Alex explicó que Render aloja la infraestructura sin separarla. |
| Despliegue desde GitHub | introduced | 2026-08-20 | 2026-08-20 | Alex explicó que Render se conecta a GitHub y despliega automáticamente. |
| Terminal | seed | — | — | Pendiente de primera lección. |
| Sistema de archivos, rutas y carpetas | introduced | 2026-08-24 | 2026-08-24 | Alex explicó que la posición de cada carpeta permite saber a qué se dedica. |
| Comandos de terminal | seed | — | — | Pendiente de primera lección. |
| Repositorio Git | introduced | 2026-08-25 | 2026-08-25 | Alex revisó el repositorio local de frontend y confirmó sus dos commits. |
| Git: estado, add y commit | introduced | 2026-08-25 | 2026-08-25 | Alex revisó el estado, preparó `page.tsx` y `.gitignore`, y eligió el mensaje del commit `Personaliza la página inicial`. |
| Git: historial y revertir cambios | seed | — | — | Pendiente de primera lección práctica. |
| Git: ramas y pull requests | seed | — | — | Pendiente de primera lección práctica. |
| Repositorio remoto y GitHub | introduced | 2026-08-25 | 2026-08-25 | Alex distinguió el repositorio local del publicado en GitHub, explicó `git push origin master` y conectó/publicó el historial inicial. |
| Diff de código | introduced | 2026-08-25 | 2026-08-25 | Alex predijo y revisó el diff de `page.tsx` y `.gitignore` antes de aceptarlo. |
| `.gitignore` | introduced | 2026-08-25 | 2026-08-25 | Alex escribió que `node_modules/` se genera automáticamente y no debe guardarse en Git. |
| Python: intérprete y ejecución de archivos | seed | — | — | Pendiente de primera lección de Python. |
| Python: variables y tipos básicos | seed | — | — | Pendiente de primera lección de Python. |
| Python: cadenas, números y booleanos | seed | — | — | Pendiente de primera lección de Python. |
| Python: listas y diccionarios | seed | — | — | Pendiente de primera lección de Python. |
| Python: condicionales | seed | — | — | Pendiente de primera lección de Python. |
| Python: bucles | seed | — | — | Pendiente de primera lección de Python. |
| Python: funciones, parámetros y retorno | seed | — | — | Pendiente de primera lección de Python. |
| Python: módulos e imports | seed | — | — | Pendiente de primera lección de Python. |
| Python: errores y excepciones | seed | — | — | Pendiente de primera lección de Python. |
| Entorno virtual y dependencias de Python | seed | — | — | Pendiente de primera configuración del backend. |
| TypeScript: variables, tipos y funciones | practicing | 2026-08-26 | 2026-08-26 | Alex aplicó el tipo unión `JobStatus`, una función que avanza el estado y comprobó las rutas normal y de error. |
| TypeScript: objetos, arrays e interfaces | practicing | 2026-08-26 | 2026-08-26 | Alex modeló propuestas con `ClipProposal`, las recorrió con `map` y explicó que los clips no coincidentes conservan su decisión. |
| TypeScript: módulos e imports | seed | — | — | Pendiente de primera lección de TypeScript. |
| JavaScript asíncrono, promesas y `async/await` | introduced | 2026-08-27 | 2026-08-27 | Se introdujo que `await` espera la respuesta de la API sin congelar la interfaz; se profundizará al ampliar la conexión. |
| Node.js, npm y `package.json` | introduced | 2026-08-24 | 2026-08-24 | Alex identificó que npm es la herramienta que se debía reparar para descargar React y Next.js. |
| Dependencias y bloqueo de versiones | seed | — | — | Pendiente de crear el proyecto frontend. |
| HTML semántico | introduced | 2026-08-25 | 2026-08-25 | Alex creó una estructura con `main`, `section`, encabezados y un botón para comunicar la pantalla de subida. |
| CSS, layout responsive y accesibilidad básica | introduced | 2026-08-25 | 2026-08-25 | Alex aplicó clases de Tailwind al panel y reconoció que un botón comunica una acción; queda pendiente profundizar en accesibilidad. |
| React: componentes | practicing | 2026-08-24 | 2026-08-25 | Alex personalizó el contenido que devuelve Home y verificó el resultado en el navegador. |
| React: props, estado y eventos | practicing | 2026-08-25 | 2026-08-28 | Alex añadió estado para propuestas simuladas, comprobó aceptar/descartar y explicó cómo se conservan y actualizan los tiempos locales de revisión. También distinguió el estado de una petición del dato `apiJob` recibido. |
| Formularios y carga de archivos en el navegador | practicing | 2026-08-25 | 2026-08-26 | Alex usó controles de rango para ajustar inicio y fin de un clip aceptado y verificó que ambos valores se mantienen localmente. |
| Renderizado y rutas de Next.js | introduced | 2026-08-25 | 2026-08-25 | Alex explicó que `src/app/page.tsx` muestra la interfaz principal porque corresponde a la ruta `/`. |
| Arquitectura de carpetas y comunicación entre archivos | seed | — | — | Pendiente de construir la primera estructura. |
| Cliente, servidor y ciclo solicitud-respuesta | practicing | 2026-08-27 | 2026-08-28 | Alex recorrió con apoyo el flujo `page.tsx` → GET `/jobs/demo` → `get_demo_job` → JSON → `setApiJob(job)` → recuadro de la interfaz. |
| API, endpoint y contrato de datos | practicing | 2026-08-27 | 2026-08-27 | Alex explicó que `Job` es el contrato que define qué se espera y se mostrará en pantalla; verificó `GET /jobs/demo` y su JSON. |
| HTTP: métodos, códigos de estado y JSON | introduced | 2026-08-27 | 2026-08-27 | Alex identificó que la solicitud usa GET y que la API responde JSON; los códigos de estado se verán al manejar fallos. |
| CORS | practicing | 2026-08-27 | 2026-08-28 | Alex verificó el encabezado `Access-Control-Allow-Origin: http://localhost:3000` y explicó que un origen no incluido en CORS no puede leer la respuesta desde su JavaScript; conectó CORS con el permiso para que la página local lea el JSON. |
| FastAPI: rutas, modelos y validación | practicing | 2026-08-27 | 2026-09-07 | Alex explicó que `GET /health` devuelve `{"status":"ok"}` para comprobar que el backend responde y predijo que el servidor permanece esperando solicitudes; verificó la respuesta local. También identificó que `get_demo_job` devuelve el identificador y estado del trabajo. Construyó y recorrió `GET /health/database`, que devuelve JSON tras comprobar PostgreSQL. |
| Pydantic | introduced | 2026-08-27 | 2026-08-27 | Alex ubicó `Job` como el contrato que define los datos esperados; se introdujo que Pydantic valida y da forma al JSON. |
| SQL y modelo relacional | introduced | 2026-09-02 | 2026-09-02 | Alex separó los datos mínimos en trabajo, transcripción y clip antes de crear tablas. |
| Tablas, filas, claves primarias y relaciones | introduced | 2026-09-02 | 2026-09-02 | Alex identificó que un clip guarda inicio/fin y que transcripción y clips usan `job_id` para pertenecer a un trabajo. |
| ORM y migraciones de base de datos | seed | — | — | Pendiente de conectar FastAPI y PostgreSQL. |
| Transacciones y consultas | seed | — | — | Pendiente de conectar FastAPI y PostgreSQL. |
| Almacenamiento de objetos y URLs temporales | seed | — | — | Pendiente de implementar subida de MP4. |
| Redis y cola de trabajos | seed | — | — | Pendiente de implementar el worker. |
| Estados de trabajo, reintentos e idempotencia | introduced | 2026-08-26 | 2026-08-26 | Alex modeló localmente los estados subido, transcribiendo, generando, listo y error; queda pendiente aprender reintentos e idempotencia con un worker real. |
| Procesamiento de video con FFmpeg | seed | — | — | Pendiente de flujo real de video. |
| Transcripción con timestamps | seed | — | — | Pendiente de flujo real de video. |
| Selección de clips mediante IA | seed | — | — | Pendiente de flujo real de video. |
| Subtítulos y renderizado vertical 9:16 | seed | — | — | Pendiente de flujo real de video. |
| Validación de archivos y límites de uso | seed | — | — | Pendiente de endurecer el MVP. |
| Variables de entorno y secretos | introduced | 2026-09-07 | 2026-09-07 | Alex explicó que `DATABASE_URL` debe leerse desde `.env` para no exponer credenciales en `main.py`; configuró Pydantic para exigirla al iniciar. |
| Pruebas unitarias | seed | — | — | Pendiente de sección de calidad. |
| Pruebas de integración y de extremo a extremo | seed | — | — | Pendiente de sección de calidad. |
| Linting, formateo y comprobación de tipos | seed | — | — | Pendiente de primera configuración de calidad. |
| Registro de errores y observabilidad | seed | — | — | Pendiente de sección de operación. |
| HTTPS, seguridad básica y manejo de errores | seed | — | — | Pendiente de despliegue. |
| Docker y configuración reproducible | practicing | 2026-09-07 | 2026-09-07 | Alex explicó que PostgreSQL corre en un contenedor para no instalarlo directamente en Windows y que el backend accede a él mediante puertos distintos: 5433 en la computadora y 5432 dentro del contenedor. También distinguió un contenedor de PostgreSQL de su puerto y de una base de datos lógica. |
| Despliegue en Render y servicios administrados | seed | — | — | Pendiente de despliegue. |
| Integración y despliegue continuo desde GitHub | seed | — | — | Pendiente de despliegue. |
| Definir alcance de un MVP | seed | — | — | Pendiente de lección explícita y práctica. |
| Plan de construcción por capas | seed | — | — | Pendiente de lección explícita y práctica. |
| Especificaciones y criterios de aceptación | seed | — | — | Pendiente de primera funcionalidad. |
| Revisión de un diff antes de aceptar cambios | seed | — | — | Pendiente de primera revisión de código. |
| Uso de IA como colaborador: instrucciones y contexto | seed | — | — | Pendiente de primera práctica explícita. |
| Archivos de memoria del agente | seed | — | — | Pendiente de primera práctica explícita. |
| Verificación independiente de resultados de IA | seed | — | — | Pendiente de primera práctica explícita. |
| Documentación técnica y explicación de arquitectura | seed | — | — | Pendiente de primera práctica explícita. |
