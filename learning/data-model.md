# Modelo de datos inicial — ClipsGenerator

Este esquema define la información mínima que PostgreSQL guardará para que un
trabajo no se pierda al reiniciar el backend. Aún no crea tablas ni almacena
videos.

```text
Trabajo (1) ── tiene una ──> (1) Transcripción
Trabajo (1) ── tiene varios ──> (N) Clips
```

## Trabajo

Representa un episodio de podcast que el usuario pidió procesar.

| Campo | Para qué sirve |
| --- | --- |
| `id` | Identificador único del trabajo. |
| `original_filename` | Nombre del MP4 seleccionado por el usuario. |
| `status` | Etapa del flujo: subido, transcribiendo, generando, listo o error. |

## Transcripción

Representa el texto con tiempos generado para un trabajo.

| Campo | Para qué sirve |
| --- | --- |
| `id` | Identificador único de la transcripción. |
| `job_id` | Indica a qué trabajo pertenece. |
| `text` | Texto transcrito; los tiempos detallados se añadirán cuando el procesamiento real lo necesite. |

## Clip

Representa una propuesta de fragmento derivada de un trabajo.

| Campo | Para qué sirve |
| --- | --- |
| `id` | Identificador único del clip. |
| `job_id` | Indica a qué trabajo pertenece. |
| `title` | Título sugerido para el clip. |
| `start_seconds` | Segundo en el que comienza el clip. |
| `end_seconds` | Segundo en el que termina el clip. |
| `decision` | Revisión del usuario: pendiente, aceptado o descartado. |

## Relaciones

- Una transcripción pertenece a un único trabajo mediante `job_id`.
- Un clip pertenece a un único trabajo mediante `job_id`.
- Un trabajo puede tener muchos clips.
