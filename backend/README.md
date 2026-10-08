# Herramientas de video del backend

El worker ejecuta FFmpeg para convertir audio y renderizar clips, y FFprobe
para comprobar las pistas del video. Ambos deben estar instalados en el mismo
entorno donde se ejecuta Python.

## Configuración local

Por defecto, el worker busca `ffmpeg` y `ffprobe` en el `PATH` de su proceso.
Una terminal o aplicación abierta antes de actualizar el `PATH` puede conservar
la lista anterior aunque Windows ya tenga las herramientas instaladas.

Para evitar depender del `PATH`, configura rutas absolutas en `backend/.env`:

```dotenv
FFMPEG_PATH="C:/ruta/a/ffmpeg/bin/ffmpeg.exe"
FFPROBE_PATH="C:/ruta/a/ffmpeg/bin/ffprobe.exe"
```

Usa las rutas reales de tu instalación. Este archivo es local y está ignorado
por Git; no publiques su contenido porque también contiene secretos.
Si una actualización mueve los ejecutables, actualiza ambas rutas.

Reinicia el worker después de cambiar `.env`: lee la configuración al arrancar.
Desde la carpeta `backend`, puedes ejecutarlo en PowerShell con:

```powershell
.\.venv\Scripts\python.exe worker.py
```

En otro equipo o en producción, configura las rutas de ese entorno, o deja
estas variables sin definir si ambos programas están disponibles en el `PATH`.

## Archivos temporales

Los videos originales, subtítulos y clips se conservan durante siete días desde
el último cambio de su carpeta de trabajo. Al iniciar y después cada 24 horas,
el worker elimina únicamente las carpetas vencidas dentro de `storage/jobs`.
Los enlaces de esos trabajos dejan de estar disponibles después de la limpieza.
Cuando se configura R2, el worker aplica el mismo plazo al conjunto de objetos
de cada trabajo, tomando la fecha más reciente de sus objetos. La API entrega
los clips desde R2 usando la clave guardada en PostgreSQL.
