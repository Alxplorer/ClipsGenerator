# Plan de aprendizaje y construcción — ClipsGenerator

> Antes de trabajar, leer también `learning/project.md`. Este plan prioriza
> comprender cada capa y ver resultados pequeños funcionando; no optimizar la
> velocidad de entrega.

## Decisiones de diseño confirmadas

| Área | Decisión | Motivo principal |
| --- | --- | --- |
| Lenguaje | TypeScript y Python | TypeScript se usa en la web; Python se usa para aprender y para el backend/procesamiento de IA y video. |
| Frontend | Next.js con React y TypeScript | Ecosistema muy grande y estructura clara para construir la interfaz web. |
| Backend | FastAPI con Python | API clara y un ecosistema adecuado para procesamiento de IA, audio y video. |
| Base de datos | PostgreSQL | Base relacional estable para guardar trabajos, estados, transcripciones y clips. Los MP4 no se guardan aquí. |
| Hosting | Render | Un lugar principal para el frontend, API, worker, PostgreSQL y cola de trabajos, conectado al repositorio Git para desplegar cambios. |

## Plan por secciones

### 1. Fundamentos, entorno y control de versiones

Aprender lo esencial de terminal, Git, GitHub, TypeScript, Python y la estructura
del repositorio. Crear el frontend de Next.js y hacer commits pequeños y claros
desde el primer día.

- [x] **1.1 Crear el frontend base de Next.js.** Generar el proyecto, identificar
  sus archivos esenciales y abrir la página inicial localmente.
  **Resultado visible:** la página de bienvenida de Next.js aparece en el navegador.
- [x] **1.2 Entender y personalizar la página inicial.** Cambiar texto y estructura
  de la página para que se presente como ClipsGenerator.
  **Resultado visible:** una página inicial propia de ClipsGenerator aparece al recargar.
- [x] **1.3 Conocer el control de versiones local.** Inicializar o revisar Git,
  inspeccionar el estado y configurar qué archivos no se deben versionar.
  **Resultado visible:** `git status` muestra claramente qué se guardará y qué se ignorará.
- [x] **1.4 Guardar el primer hito en Git.** Revisar el diff y crear un commit con
  un mensaje que describa el frontend inicial.
  **Resultado visible:** `git log` muestra el primer hito del proyecto.
- [x] **1.5 Conectar el historial con GitHub.** Crear o asociar el remoto y publicar
  el commit, si la cuenta y el repositorio remoto están disponibles.
  **Resultado visible:** el commit inicial se puede ver en GitHub.

**Resultado visible:** una página inicial de ClipsGenerator abierta localmente en
el navegador y el código respaldado con historial de commits en GitHub.

### 2. Interfaz del flujo del podcaster

Construir las pantallas y estados de la experiencia: subida de MP4, límites,
progreso, lista de clips, revisión y descarga. Al inicio puede usar datos falsos
para concentrarse en entender la interfaz y sus interacciones.

- [x] **2.1 Diseñar la pantalla de inicio y subida.** Sustituir la bienvenida
  actual por el punto de entrada del podcaster: propuesta de valor, límites del
  MVP y zona visual para seleccionar un MP4, todavía sin comportamiento real.
  **Resultado visible:** la página comunica claramente qué hace el producto y
  dónde empezaría la subida.
- [x] **2.2 Seleccionar un archivo en el navegador.** Convertir la zona de subida
  en un control accesible que permita elegir un MP4 y muestre su nombre y tamaño
  localmente, sin enviarlo aún a un servidor.
  **Resultado visible:** al elegir un video, la pantalla confirma cuál archivo
  fue seleccionado.
- [x] **2.3 Simular el progreso de un trabajo.** Modelar los estados visibles
  subido, transcribiendo, generando clips, listo y error con datos locales.
  **Resultado visible:** la interfaz puede mostrar el avance de un trabajo de
  ejemplo sin backend.
- [x] **2.4 Mostrar y decidir sobre clips simulados.** Presentar propuestas con
  título, duración y razón editorial; permitir aceptar o descartar cada una.
  **Resultado visible:** el usuario recorre una lista de clips y sus decisiones
  cambian la pantalla.
- [x] **2.5 Simular revisión y descarga.** Añadir una vista mínima de revisión
  para un clip aceptado, con controles de inicio/fin simulados y una descarga de
  ejemplo claramente identificada como no real.
  **Resultado visible:** se puede recorrer el flujo completo simulado desde un
  MP4 seleccionado hasta un clip aprobado.

**Resultado visible:** se puede recorrer en el navegador una simulación completa
del producto, desde elegir un video hasta ver y aprobar clips simulados.

### 3. API local con FastAPI y conexión frontend-backend

Crear el servidor de Python, aprender sus rutas HTTP y sustituir una parte de los
datos falsos por respuestas reales de la API. Mantener responsabilidades claras:
Next.js presenta la interfaz y FastAPI coordina los datos y trabajos.

- [x] **3.1 Crear y ejecutar el backend FastAPI.** Preparar un entorno aislado
  de Python y una ruta de salud que responda desde el navegador.
  **Resultado visible:** `GET /health` devuelve una confirmación JSON desde
  FastAPI local.
- [x] **3.2 Definir el contrato de un trabajo.** Modelar en Python los datos
  mínimos de un trabajo de ClipsGenerator y devolver un ejemplo fijo.
  **Resultado visible:** `GET /jobs/demo` devuelve un trabajo con su identificador
  y estado en JSON.
- [x] **3.3 Conocer solicitud, respuesta y contrato.** Inspeccionar la petición
  de la web a la API e identificar qué datos viajan en cada dirección.
  **Resultado visible:** se puede explicar por qué frontend y backend coinciden
  en la forma de un trabajo.
- [x] **3.4 Permitir la comunicación local entre orígenes.** Configurar CORS
  exclusivamente para el frontend local y comprobar la petición desde el navegador.
  **Resultado visible:** el navegador puede consultar FastAPI sin bloquear la
  respuesta por una política de origen.
- [x] **3.5 Mostrar un estado real en Next.js.** Sustituir uno de los estados
  simulados por el trabajo que devuelve FastAPI, incluyendo carga y error básicos.
  **Resultado visible:** la interfaz muestra el estado obtenido de la API local.
- [x] **3.6 Recorrer la conexión de punta a punta.** Verificar ambos servidores
  y explicar el recorrido desde abrir la página hasta visualizar el estado.
  **Resultado visible:** una demostración local conecta Next.js → FastAPI → JSON
  → interfaz.

**Resultado visible:** la página obtiene desde FastAPI un estado real de trabajo
y lo muestra en pantalla.

### 4. Persistencia con PostgreSQL

Diseñar las entidades mínimas: trabajo, transcripción y clip. Conectar FastAPI a
PostgreSQL para que los trabajos y sus estados no se pierdan al reiniciar el
servidor.

- [x] **4.1 Diseñar los datos persistentes mínimos.** Identificar qué información
  pertenece a un trabajo, una transcripción y un clip, además de cómo se
  relacionan entre sí.
  **Resultado visible:** un esquema sencillo explica las tres entidades y sus
  relaciones antes de crear la base de datos.
- [x] **4.2 Ejecutar PostgreSQL localmente y configurar la conexión.** Crear una
  instancia local aislada y una configuración sin secretos en el código fuente.
  **Resultado visible:** FastAPI puede conectarse a una base de datos PostgreSQL
  local.
- [x] **4.3 Crear el esquema inicial mediante migraciones.** Traducir el diseño a
  tablas y versionar los cambios de estructura.
  **Resultado visible:** las tablas de trabajo, transcripción y clip aparecen en
  PostgreSQL después de ejecutar una migración.
- [x] **4.4 Guardar un trabajo real desde FastAPI.** Sustituir el ejemplo fijo por
  una ruta que cree un trabajo y lo persista.
  **Resultado visible:** una solicitud crea un trabajo con identificador y estado
  en PostgreSQL.
- [x] **4.5 Recuperar trabajos y sus datos relacionados.** Consultar un trabajo
  por identificador y devolver su estado, transcripción y clips cuando existan.
  **Resultado visible:** FastAPI devuelve datos almacenados en vez de un ejemplo
  escrito en código.
- [x] **4.6 Verificar persistencia tras reiniciar.** Crear un trabajo, reiniciar
  FastAPI y recuperarlo de nuevo.
  **Resultado visible:** el mismo trabajo sigue existiendo tras reiniciar el
  backend.

**Resultado visible:** crear un trabajo desde la web, reiniciar el backend y ver
que el trabajo y su estado siguen existiendo.

### 5. Cola y worker de procesamiento

Incorporar una cola de trabajos y un worker de Python. Primero procesará una
tarea de prueba lenta para entender los estados, reintentos y errores antes de
usar video real.

- [ ] **5.1 Dibujar el recorrido asíncrono de un trabajo.** Decidir qué registra
  la API, qué espera en la cola y qué actualiza el worker, incluyendo el caso de
  error y la consulta posterior desde la web.
  **Resultado visible:** un esquema breve permite seguir un trabajo desde
  `POST /jobs` hasta el estado que devuelve `GET /jobs/{job_id}`.
- [ ] **5.2 Levantar una cola local.** Elegir la herramienta mínima para la cola
  y ejecutarla junto a PostgreSQL, separando su función de la base de datos.
  **Resultado visible:** la API y un proceso Python pueden conectarse a la cola.
- [ ] **5.3 Encolar un trabajo al crearlo.** Hacer que `POST /jobs` guarde el
  trabajo y solicite su procesamiento sin esperar a que termine.
  **Resultado visible:** la API responde enseguida y la tarea queda pendiente
  para el worker.
- [ ] **5.4 Procesar una tarea de prueba con un worker.** Ejecutar un proceso
  separado que tome el trabajo, espere de forma simulada y actualice su estado
  en PostgreSQL.
  **Resultado visible:** el mismo `job_id` pasa de `uploaded` a un estado de
  procesamiento y después a `ready`.
- [ ] **5.5 Tratar fallos y reintentos básicos.** Provocar un error controlado y
  definir qué sucede si el worker se interrumpe o recibe de nuevo el trabajo.
  **Resultado visible:** un fallo deja un estado consultable y un reintento no
  crea un segundo trabajo.
- [ ] **5.6 Mostrar el progreso real en la web.** Conectar la creación y las
  consultas periódicas del trabajo desde Next.js.
  **Resultado visible:** la web muestra cómo cambia un trabajo real mientras
  el procesamiento de prueba ocurre en segundo plano.

**Resultado visible:** un trabajo creado en la web cambia de “pendiente” a
“procesando” y luego a “listo” sin bloquear la aplicación.

### 6. Flujo real de video e IA

Implementar por etapas la subida y almacenamiento temporal del MP4, transcripción
en español con tiempos, selección de 3 a 8 momentos, generación de subtítulos y
renderizado vertical 9:16. Integrar cada parte en el worker, conservando la
revisión mínima de inicio/fin en la web.

**Resultado visible:** un podcast real se transforma localmente en al menos un
clip vertical descargable con subtítulos.

### 7. Calidad, seguridad y operación local

Agregar pruebas automatizadas para las reglas importantes, validación de archivos
y límites, manejo claro de errores, configuración segura de secretos y borrado
programado de archivos temporales. Documentar cómo ejecutar y entender el sistema
completo.

**Resultado visible:** las pruebas pasan, los errores esperables se comunican en
la interfaz y el sistema rechaza entradas inválidas sin exponer claves privadas.

### 8. Despliegue y validación en producción

Conectar el repositorio a Render, configurar los servicios de frontend, API,
worker, base de datos y cola, además del almacenamiento temporal de archivos y
HTTPS. Verificar el flujo con videos reales desde una URL pública.

**Resultado visible:** una persona puede abrir la URL pública, subir un MP4,
esperar el procesamiento y descargar un clip final sin usar tu computadora.

## Principio de aprendizaje

No se avanza a una sección solo porque “falta menos”; se avanza cuando se pueda
explicar con palabras propias qué se construyó, qué datos entran y salen, y cómo
se conecta con la capa anterior.
