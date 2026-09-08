# ClipsGenerator — definición del proyecto

> **Instrucción para sesiones futuras:** antes de proponer, diseñar o implementar
> cualquier cambio en este proyecto, leer este archivo completo. El alcance del
> MVP es intencionalmente estrecho; toda función no incluida aquí pertenece a v2
> hasta que se decida explícitamente cambiar esta definición.

## Quién soy

- **Nombre:** Alex *(inferido del entorno; confirmar si prefieres otro nombre)*.
- **Rol:** creador del proyecto y futuro usuario/validador del producto.
- **Objetivo:** lanzar una herramienta web útil para podcasters, no solo un
  prototipo local.

## Nivel de experiencia

- **Por confirmar.** No se debe asumir experiencia previa de desarrollo,
  infraestructura, IA o edición de video. Las decisiones y la documentación
  deben explicar los pasos sin ocultar complejidad importante.

## Idea del proyecto

Una aplicación web para podcasters de habla hispana. El usuario sube un episodio
de video y recibe varios clips verticales cortos, con subtítulos, que puede
revisar y descargar para publicar en Reels, TikTok o YouTube Shorts.

La promesa inicial es ahorrar el tiempo de buscar y preparar clips, no sustituir
por completo el criterio editorial del podcaster.

## En el MVP

El producto mínimo debe estar desplegado en internet mediante HTTPS y permitir
completar este flujo de punta a punta sin intervención manual del creador:

1. Una página web donde una persona pueda subir un archivo de podcast en video
   (MP4) y ver los límites claros del servicio.
2. Procesamiento asíncrono con estados visibles: subido, transcribiendo,
   generando clips, listo o error. El trabajo debe sobrevivir a que el usuario
   cierre la página.
3. Transcripción automática en español con timestamps por frase.
4. Selección automática de **3 a 8** momentos potencialmente interesantes de
   aproximadamente **20 a 60 segundos**, descartando de forma básica silencios,
   introducciones, despedidas y anuncios cuando se puedan identificar.
5. Para cada propuesta: título breve sugerido, razón editorial corta y vista
   previa reproducible.
6. Una revisión mínima: aceptar o descartar cada clip y ajustar su inicio y fin
   desde la transcripción o controles equivalentes.
7. Generación de un MP4 vertical 9:16, 1080x1920, con un encuadre centrado
   consistente y **un único estilo de subtítulos legible** en español.
8. Descarga del MP4 final, listo para publicar.
9. Manejo mínimo de producto real: límites de duración/tamaño definidos,
   mensajes de error comprensibles, almacenamiento temporal y borrado automático
   de archivos/resultados tras un periodo claramente indicado.

### Decisiones de alcance del MVP

- El primer caso de uso es un podcast de video de hasta dos personas, en español.
- No se requiere cuenta: una sesión anónima con enlace temporal es suficiente para
  validar el flujo y evita construir autenticación, facturación y recuperación de
  cuenta antes de probar valor.
- El encuadre será centrado y fiable, no seguimiento inteligente del hablante.
- Antes de crecer, la métrica a validar es cuántos clips se aprueban y descargan
  con cambios mínimos.

## Lista de espera (v2)

Estas funciones son valiosas, pero quedan fuera hasta que el flujo anterior esté
publicado y sea usado:

- Cuentas, inicio de sesión, historial permanente, equipos y roles.
- Pagos, suscripciones, créditos y facturación.
- Importar episodios desde YouTube, RSS, Drive u otras URLs.
- Más idiomas, traducción y doblaje.
- Detección de hablantes, seguimiento de rostro/hablante activo y cambio de
  encuadre automático.
- Pantalla dividida para anfitrión e invitado.
- Múltiples plantillas, fuentes, colores, logos, branding guardado y animaciones
  avanzadas de subtítulos.
- Edición completa de texto, video, audio, música, B-roll, transiciones o efectos.
- Generación automática de B-roll, imágenes, avatares o voces sintéticas.
- Publicación directa y programación en TikTok, Instagram, YouTube u otras redes.
- Copys, hashtags, miniaturas y calendarios de contenido generados por IA.
- Ranking sofisticado de viralidad, analítica de rendimiento e integración con
  métricas de redes.
- Podcasts de más de dos personas, multicámara, transmisión en vivo o episodios
  extremadamente largos.
- Procesamiento prioritario, GPU dedicada, colaboración en equipo, API pública y
  webhooks.

## Regla contra la expansión de alcance

Si aparece una función nueva, debe ir a **Lista de espera (v2)** por defecto. Solo
puede entrar al MVP si es indispensable para que un podcaster suba un video,
obtenga clips útiles, haga una corrección mínima y descargue el resultado. Si el
flujo ya funciona sin ella, se pospone.

## Trunk: mapa principal de aprendizaje y construcción

Este es el conjunto de piezas fundamentales. Se construyen como un sistema, no
como funciones aisladas:

1. **Producto y flujo de usuario:** definir las pantallas y el recorrido desde
   subir un MP4 hasta descargar un clip. Es la guía para no construir funciones
   que no resuelven el problema del podcaster.
2. **Control de versiones (Git):** sistema que guarda el historial de cambios
   del código y permite volver atrás con seguridad. El proyecto debe usarlo desde
   el primer día, con cambios pequeños y mensajes claros; un repositorio remoto
   sirve además como copia de seguridad y colaboración.
3. **Frontend:** la parte visual de la web que se abre en el navegador. Muestra
   la carga del video, el progreso, las propuestas y la descarga.
4. **Backend y API:** el programa que se ejecuta en el servidor. Recibe las
   solicitudes del frontend y coordina el trabajo; una API es el canal acordado
   por el que frontend y backend se comunican.
5. **Datos y archivos:** almacenamiento de los videos originales, clips finales
   y una base de datos, que es un lugar organizado para guardar el estado del
   trabajo y sus metadatos. Se necesita para recuperar una tarea aunque se cierre
   la página y para borrar archivos temporales a tiempo.
6. **Trabajos en segundo plano:** una cola de trabajos, es decir, una lista de
   tareas pendientes atendida por procesos separados, realiza la transcripción y
   renderización sin congelar la web. Es esencial porque procesar video tarda.
7. **Motor de IA y video:** servicios o programas que transcriben el audio,
   proponen momentos, generan subtítulos y renderizan el MP4 vertical. Es el
   núcleo que convierte un episodio en clips publicables.
8. **Despliegue, calidad y operación:** despliegue significa publicar la
   aplicación en servidores accesibles por internet; incluye HTTPS, variables
   secretas, pruebas automáticas, registro de errores y límites de uso. Hace que
   el producto sea confiable y seguro para usuarios reales.
