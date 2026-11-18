# PLAN — Concello de Batalla

Generador automático de vídeos verticales (9:16) en los que los concellos de Galicia se invaden entre sí. Cada batalla se decide con dados y un multiplicador basado en el número de vacas. Los vídeos se publican solos en YouTube Shorts, Instagram Reels y TikTok.

**Leyenda de estado:** `[ ]` pendiente · `[~]` en curso · `[x]` completado

Cada paso indica **Qué** se hace, **Archivos** que se tocan y **Hecho cuando** (criterio de verificación).

---

## FASE 0 — Decisiones previas

### [x] 0.1 Resolver las dudas abiertas de las reglas
- **Qué:** Responder las preguntas de la sección «Dudas abiertas» (al final del plan) y fijar las reglas definitivas.
- **Archivos:** `docs/DECISIONES.md`.
- **Hecho cuando:** `docs/DECISIONES.md` recoge todas las reglas, cada duda tiene una respuesta del usuario. ✅ Completado el 2026-11-18: las 7 fases del vídeo, la mecánica de dados/multiplicador/empate, el cálculo del porcentaje de vacas, las vacas de territorio combinado, el final de la serie, el valor por defecto sin vacas, el idioma (gallego) y la duración/frecuencia (vídeo diario de 80–90 s) quedan todos resueltos y documentados.

### [x] 0.2 Elegir el stack técnico
- **Qué:** Decidir entre las opciones propuestas.
- **Archivos:** `docs/DECISIONES.md`.
- **Hecho cuando:** la decisión y su motivo están en `docs/DECISIONES.md`, aprobados por el usuario. ✅ Completado el 2026-11-18: **Python 3.11+** con geopandas/shapely (geometría), Pillow/pycairo (fotogramas) y ffmpeg (montaje de vídeo y audio). Se descarta Remotion por ser más pesado de ejecutar en un entorno gratuito.

### [x] 0.3 Elegir el hosting gratuito y el programador de tareas
- **Qué:** Comparar las opciones y elegir una.
- **Archivos:** `docs/DECISIONES.md`.
- **Hecho cuando:** la opción elegida está documentada con sus límites confirmados y el usuario la ha aprobado (o, si no respondió, con la asunción tomada explicada). ✅ Completado el 2026-11-18: **GitHub + GitHub Actions con cron**. Vercel descartado (confirmado: sus funciones serverless tienen límite de tiempo pensado para peticiones web, no para renderizar vídeo con ffmpeg). El repositorio real creado por el usuario (`XurxoGafas/concello-de-batalla-videos`) es público, lo cual da minutos de Actions ilimitados (el plan original asumía uno privado; ver nota en `docs/DECISIONES.md`). GitHub Actions elegido en vez de una VM de Oracle Cloud porque no exige mantener un servidor. El estado de la partida se persiste haciendo commit al propio repo en cada ejecución.

---

## FASE 1 — Estructura del proyecto

### [x] 1.1 Crear el repositorio y la estructura de carpetas
- **Qué:** Iniciar git y crear la estructura base.
- **Archivos:** `README.md`, `.gitignore`, `.env.example`, `requirements.txt` (o `package.json`), carpetas `src/`, `data/raw/`, `data/processed/`, `assets/audio/`, `assets/fonts/`, `output/`, `tests/`, `docs/`.
- **Hecho cuando:** `git status` está limpio tras el primer commit, `.gitignore` excluye `output/`, `.env` y `data/raw/`, y el README explica en 5 líneas qué es el proyecto. ✅ Completado el 2026-11-18 sobre el repositorio real `XurxoGafas/concello-de-batalla-videos` (el intento anterior, en un repositorio distinto, no llegó a hacer push y se perdió al terminar esa sesión — ver `PROGRESO.md`).

### [x] 1.2 Preparar el entorno y comprobar dependencias
- **Qué:** Crear el entorno virtual, instalar las dependencias y comprobar que ffmpeg está disponible.
- **Archivos:** `requirements.txt`, `scripts/check_env.py`.
- **Hecho cuando:** `python scripts/check_env.py` imprime las versiones de Python, ffmpeg y las librerías clave sin errores. ✅ Completado el 2026-11-18: con la red activada, `pip install -r requirements.txt` funcionó en un entorno virtual y `check_env.py` terminó con «Entorno correcto».

---

## FASE 2 — Datos

### [x] 2.1 Conseguir los límites geográficos de los concellos
- **Qué:** Descargar los polígonos oficiales de los concellos de Galicia (fuentes candidatas: IGN / Centro de Descargas del CNIG, Xunta / IET). Registrar la fuente, la fecha y la licencia.
- **Archivos:** `data/raw/concellos.*` (shapefile/GeoJSON), `docs/FUENTES.md`.
- **Hecho cuando:** el archivo carga con geopandas, el número de concellos coincide con el número oficial actual y `docs/FUENTES.md` recoge la fuente y la licencia. ✅ Completado el 2026-11-18: fuente IGN (CC BY 4.0), 313 concellos, descarga reproducible con `scripts/descargar_concellos.py`.

### [x] 2.2 Simplificar la geometría y calcular las adyacencias
- **Qué:** Simplificar los polígonos para dibujar rápido y calcular qué concellos son colindantes: se tocan por una línea **o solo por una esquina (un punto)**, según decidió el usuario el 2026-11-18. Los concellos sin contacto físico (la isla de A Illa de Arousa) se conectan a mano en `data/vecindades_manuales.json`.
- **Archivos:** `src/datos/geometria.py`, `data/vecindades_manuales.json`, `data/processed/concellos.geojson`, `data/processed/adyacencias.json`, `tests/test_geometria.py`.
- **Hecho cuando:** existe un test que comprueba 3 parejas conocidas de vecinos (p. ej. Ordes–Cerceda) y 3 parejas que no lo son, todo concello tiene al menos un vecino y la relación es simétrica. ✅ Completado el 2026-11-18: 313 concellos, 827 parejas de vecinos (826 por contacto + 1 manual), 18 tests en verde.

### [x] 2.3 Conseguir el censo de vacas por concello
- **Qué:** Localizar datos oficiales de cabezas de ganado bovino por concello (candidatas: Xunta – Consellería do Medio Rural, IGE, INE). Si un concello tiene oficialmente 0 vacas, se usa 1 vaca (para evitar divisiones por cero). Si falta el dato de algún concello en la fuente, listar esos concellos y preguntar al usuario cómo resolverlos (no inventar un valor).
- **Archivos:** `data/raw/vacas.*`, `data/processed/vacas.json`, `docs/FUENTES.md`.
- **Hecho cuando:** todos los concellos del GeoJSON tienen un valor de vacas ≥ 1, los concellos sin dato en la fuente original están listados y resueltos con el usuario, y el total cuadra con el total gallego publicado por la fuente. ✅ Completado el 2026-11-18: fuente IGE (tabla 62, variable «Número de vacas», año 2025), 313 concellos con dato, total 511.138 = total oficial, 7 concellos con 0 vacas ajustados a 1, ninguno sin dato. Scripts: `scripts/descargar_vacas.py`, `src/datos/vacas.py`; tests en `tests/test_vacas.py`.

### [x] 2.4 Unir los datos en un estado inicial
- **Qué:** Generar el estado inicial del juego: cada concello con su id, nombre, vecinos, vacas, **color (los colores de su bandera)** y «dueño» (él mismo). La geometría no se copia al estado: queda en `data/processed/concellos.geojson` y se referencia por id (el estado se guardará con un commit en cada ejecución diaria y la geometría es estática y pesa 2,5 MB). Los colores se extraen de las imágenes de las banderas (`scripts/descargar_banderas.py`, `src/datos/colores.py`) como una paleta de hasta 4 colores con su peso. Cada dueño arranca con un contador de **victorias acumuladas en la serie = 0** (lo usará el ranking de la fase 8).
- **Archivos:** `src/datos/construir_estado.py`, `src/datos/colores.py`, `scripts/descargar_banderas.py`, `data/processed/colores_bandera.json`, `data/processed/estado_inicial.json`, `tests/test_estado_inicial.py`, `tests/test_colores.py`.
- **Hecho cuando:** el script se ejecuta sin errores y un test valida que los ids de las adyacencias, las vacas y las geometrías coinciden, y que cada dueño tiene su contador de victorias inicializado a 0. ✅ Completado el 2026-11-18 con colores **provisionales** (313 distintos entre sí, marcados `"fonte": "provisional"`): 313 concellos, cada uno dueño de sí mismo, vacas, vecinos, victorias a 0, episodio 0; 40 tests en verde. Los colores reales de las banderas pasan al paso 2.5.

### [ ] 2.5 Colores de las banderas de los concellos
- **Qué:** El usuario enviará las banderas (imágenes). Para cada concello se extrae una paleta de hasta 4 colores con su peso (`src/datos/colores.py`, ya hecho y probado con imágenes sintéticas) y se sustituyen los colores provisionales del estado inicial. Los concellos de los que no llegue bandera conservan el color provisional. (La descarga automática desde Wikidata/Commons, `scripts/descargar_banderas.py`, está bloqueada por el límite de peticiones de Wikimedia desde la red de la sesión; solo hay lista de 142 banderas en Wikidata.)
- **Archivos:** `data/raw/banderas/<código INE>.<ext>` (o el nombre que acuerde con el usuario), `data/processed/colores_bandera.json`, `data/processed/estado_inicial.json`, `docs/FUENTES.md`.
- **Hecho cuando:** cada concello con bandera tiene su paleta en el estado, el usuario revisa una imagen de muestra con los 313 concellos coloreados y aprueba los colores, y `docs/FUENTES.md` registra de dónde vienen las imágenes.

---

## FASE 3 — Motor del juego (sin gráficos)

### [x] 3.1 Función del multiplicador
- **Qué:** Implementar el cálculo del multiplicador según la diferencia porcentual de vacas: `(vacas_mayor − vacas_menor) / vacas_menor`, redondear a la decena (unidad ≤5 → hacia abajo, ≥6 → hacia arriba) con un tope del 50 %. Ejemplos: 25 % → 1,2 · 30 % → 1,3 · 35 % → 1,3 · 36 % → 1,4 · 70 % → 1,5. Las «vacas» de cada bando son las de **todo su territorio** (suma de todos los concellos que posee), no solo las del concello que combate directamente.
- **Archivos:** `src/motor/multiplicador.py`, `tests/test_multiplicador.py`.
- **Hecho cuando:** pasan los tests con el ejemplo Arteixo/A Coruña, el resto de ejemplos del enunciado y los bordes (0 %, 5 %, 6 %, 45 %, 46 %, 50 %, 200 %), y un caso con un dueño de 2+ concellos que usa la suma correcta de vacas. ✅ Completado el 2026-11-18: `src/motor/multiplicador.py` (cálculo con fracciones exactas, sin errores de coma flotante) y 27 tests en verde.

### [x] 3.2 Tirada de dados y puntuación de una batalla
- **Qué:** 3 tiradas de dados por bando. En cada tirada, la diferencia (dado propio − dado rival) se suma a favor de quien saque más; se acumulan las 3 diferencias por bando. El bando con **más vacas** multiplica su total acumulado por el bonus (ver 3.1); el otro bando no multiplica. Si tras aplicar el bonus hay empate, se entra en muerte súbita: 1 dado por bando, se repite hasta desempatar. Generador aleatorio con **semilla** para que cualquier batalla se pueda reproducir. Reglas completas en `docs/DECISIONES.md`.
- **Archivos:** `src/motor/batalla.py`, `tests/test_batalla.py`.
- **Hecho cuando:** el ejemplo del enunciado (6-1→+5, y los otros 2 dados) da la suma correcta, el multiplicador se aplica solo al bando con más vacas, la muerte súbita desempata correctamente en un caso simulado, y la misma semilla da siempre el mismo resultado. ✅ Completado el 2026-11-18: `src/motor/batalla.py`, 21 tests en verde. Las puntuaciones se comparan **con decimales** (un decimal, exacto, sin redondear), decisión del usuario.

### [x] 3.3 Selección de atacante y defensor
- **Qué:** Elegir al atacante al azar entre los dueños vivos y, después, un defensor al azar entre los vecinos de todo su territorio que pertenezcan a otro dueño.
- **Archivos:** `src/motor/seleccion.py`, `tests/test_seleccion.py`.
- **Hecho cuando:** los tests comprueban que el defensor siempre es colindante y de otro dueño, y que nunca se elige un atacante sin vecinos enemigos. ✅ Completado el 2026-11-18: `src/motor/seleccion.py`, 16 tests en verde (104 en total).

### [x] 3.4 Conquista y actualización del estado
- **Qué:** Aplicar el resultado de la batalla: el ganador absorbe el territorio y las vacas del perdedor; esa región pasa a mostrarse con el nombre y la bandera/color del ganador. Eliminar a los dueños sin territorio y detectar el final de la partida (un único dueño).
- **Archivos:** `src/motor/estado.py`, `tests/test_estado.py`.
- **Hecho cuando:** el total de vacas se conserva tras cada batalla, el territorio conquistado queda con el color del ganador, y una simulación completa con semilla fija termina siempre con un único ganador. ✅ Completado el 2026-11-18: `src/motor/estado.py`, 14 tests en verde (118 en total); la simulación completa de Galicia (313 dueños, semilla 42) termina en 312 conquistas con un único ganador.

### [ ] 3.5 Persistencia de la partida
- **Qué:** Guardar y cargar el estado entre ejecuciones (si la partida continúa de vídeo en vídeo), con un histórico de batallas y el número de episodio actual. El estado de cada dueño incluye su contador de **victorias acumuladas** (se incrementa en 1 cada vez que gana una batalla, se transfiere al ganador cuando se funden territorios).
- **Archivos:** `src/motor/persistencia.py`, `data/partida/estado_actual.json`, `data/partida/historial.jsonl`.
- **Hecho cuando:** ejecutar 5 batallas seguidas en 5 procesos distintos da el mismo resultado que 5 batallas en un solo proceso con la misma semilla, y el contador de victorias de cada dueño es correcto tras la secuencia.

### [ ] 3.6 Simulación por consola
- **Qué:** Un comando que simula N batallas e imprime el resultado en texto.
- **Archivos:** `src/cli.py`.
- **Hecho cuando:** `python -m src.cli simular --batallas 10 --semilla 42` imprime 10 batallas legibles, siempre iguales con la misma semilla.

---

## FASE 4 — Gráficos

Las 7 fases de un vídeo están fijadas en `docs/DECISIONES.md`. Un vídeo = fase 1 (intro) + 3 repeticiones de las fases 2–6 (fase 7) + cierre.

### [ ] 4.1 Definir la guía visual
- **Qué:** Fijar la resolución (1080×1920), los fps (30 o 60), la paleta, las tipografías (con licencia libre, que soporten caracteres del gallego: ñ, á, é, í, ó, ú, ü), las zonas seguras (que la interfaz de TikTok/IG no tape nada) y el estilo de los dados, las siluetas de concello y los marcadores de vacas. Todos los textos en pantalla van en gallego.
- **Archivos:** `docs/ESTILO.md`, `src/render/estilo.py`, `assets/fonts/`.
- **Hecho cuando:** el usuario aprueba un fotograma de muestra estático (`output/muestras/estilo.png`) con texto en gallego.

### [ ] 4.2 Renderizar el mapa
- **Qué:** Dibujar el mapa de Galicia coloreado por dueño/bandera, con nombres, y una vista con zoom centrada en un concello que muestre sus fronteras (fase 2).
- **Archivos:** `src/render/mapa.py`.
- **Hecho cuando:** se generan `output/muestras/mapa_inicial.png` y `output/muestras/mapa_zoom_atacante.png`, legibles en un móvil.

### [ ] 4.3 Pantalla de enfrentamiento (fase 3)
- **Qué:** Mostrar las siluetas de atacante y defensor, cada una con su nombre y, debajo, su número de vacas.
- **Archivos:** `src/render/enfrentamiento.py`.
- **Hecho cuando:** se genera `output/muestras/enfrentamiento.png` con ambas siluetas y datos legibles.

### [ ] 4.4 Animación de dados y marcador (fases 4–5)
- **Qué:** Icono de espadas cruzadas antes de la tirada; dados que ruedan y se paran, la diferencia de cada tirada («+1», «+2», «=» en empate) sumándose al marcador en pantalla, el multiplicador resaltado en dorado sobre el bando que lo recibe, y la muerte súbita si hace falta desempatar.
- **Archivos:** `src/render/dados.py`, `src/render/marcador.py`.
- **Hecho cuando:** se genera una secuencia de fotogramas de una batalla completa (incluido un caso con empate/muerte súbita) y su vista previa `output/muestras/batalla_sin_audio.mp4` se ve fluida, sin saltos.

### [ ] 4.5 Animación de conquista (fase 6)
- **Qué:** Pantalla «PERDEDOR» / «GAÑADOR» (gallego) con icono de espada apuntando hacia el ganador, y el color/bandera del ganador extendiéndose sobre el territorio del perdedor en el mapa.
- **Archivos:** `src/render/animaciones.py`.
- **Hecho cuando:** `output/muestras/conquista.mp4` muestra el cambio de color de forma clara.

### [ ] 4.6 Escenas de intro, encadenado de 3 batallas y cierre con ranking
- **Qué:** Micro intro de 1–2 s con transición al mapa (fase 1); encadenar 3 repeticiones de fases 2–6 (fase 7) dentro del mismo vídeo; cierre (fase 8) con el mapa general, el nombre de la serie + número de episodio, y los dos rankings top 5 («Máis vitorias» y «Máis territorio», medido en nº de concellos); y, cuando quede un único dueño con todo el territorio, una escena especial declarando el ganador de toda la serie en vez del cierre normal.
- **Archivos:** `src/render/escenas.py`, `src/render/ranking.py`.
- **Hecho cuando:** el vídeo de prueba incluye intro, 3 batallas encadenadas y el cierre con ranking, dura entre 80 y 90 segundos, y todo el texto está en gallego.

---

## FASE 5 — Sonido

### [ ] 5.1 Conseguir los efectos de sonido y la música con licencia
- **Qué:** Reunir los sonidos (dados, golpes, «ding» de puntos, fanfarria de conquista, mugido) y la música de fondo con licencia que permita uso comercial en redes. Registrar la licencia de cada archivo.
- **Archivos:** `assets/audio/`, `docs/FUENTES.md`.
- **Hecho cuando:** cada archivo de `assets/audio/` tiene una línea en `docs/FUENTES.md` con su fuente y su licencia.

### [ ] 5.2 Sincronizar el audio con la animación
- **Qué:** Generar una línea de tiempo de eventos (dado se para, punto sumado, conquista) y colocar cada sonido en su instante. Mezclar con la música y normalizar el volumen.
- **Archivos:** `src/audio/mezcla.py`, `src/render/linea_tiempo.py`.
- **Hecho cuando:** en el vídeo de prueba cada sonido coincide con su evento visual (revisado a mano) y el volumen final está normalizado (p. ej. ≈ −14 LUFS).

---

## FASE 6 — Pipeline de un vídeo completo

### [ ] 6.1 Comando «generar vídeo»
- **Qué:** Un único comando que carga el estado, simula 3 batallas (fase 7), renderiza las 7 fases completas (textos en gallego), añade el audio, exporta el MP4 (H.264 + AAC) de 80–90 segundos, guarda el estado y escribe los metadatos (título, descripción, hashtags, en gallego). Si al cargar el estado ya hay un único dueño con todo el territorio, el vídeo generado es el especial de cierre de serie en vez de una batalla normal.
- **Archivos:** `src/pipeline.py`, `src/metadatos.py`, `src/cli.py`.
- **Hecho cuando:** `python -m src.cli generar` produce `output/AAAA-MM-DD_HHMM/video.mp4` y `metadatos.json`, dura entre 80 y 90 segundos, y el vídeo se reproduce bien en un móvil.

### [ ] 6.2 Validación técnica del vídeo
- **Qué:** Comprobar automáticamente la resolución, la duración (80–90 s), el códec, los fps y el tamaño frente a los requisitos vigentes de cada red (comprobar en ese momento el límite real de duración de YouTube Shorts, Reels y TikTok, por si hubiera cambiado).
- **Archivos:** `src/validar.py`, `tests/test_validar.py`.
- **Hecho cuando:** el pipeline se detiene con un error claro si el vídeo no cumple los requisitos.

### [ ] 6.3 Revisión del usuario
- **Qué:** Generar 3 vídeos de muestra con semillas distintas para que el usuario los revise.
- **Archivos:** `output/muestras/`.
- **Hecho cuando:** el usuario aprueba el resultado o deja apuntados los cambios (que se añaden al plan).

---

## FASE 7 — Publicación automática

### [ ] 7.1 YouTube Shorts
- **Qué:** Crear un proyecto en Google Cloud, activar la YouTube Data API v3 y configurar OAuth con un token de actualización. Implementar la subida con título, descripción y #Shorts.
- **Archivos:** `src/publicar/youtube.py`, `.env.example`, `docs/PUBLICACION.md`.
- **Hecho cuando:** se sube un vídeo de prueba (primero como privado) y el script devuelve su URL. La cuota diaria de la API está documentada.

### [ ] 7.2 Instagram Reels
- **Qué:** Usar la API de Instagram de Meta (hace falta una cuenta profesional y una app de Meta). El vídeo debe estar en una URL pública: definir dónde se aloja temporalmente. Implementar la creación del contenedor, la espera al procesado y la publicación.
- **Archivos:** `src/publicar/instagram.py`, `docs/PUBLICACION.md`.
- **Hecho cuando:** se publica un reel de prueba y el script devuelve su id. Los requisitos y la caducidad del token están documentados.

### [ ] 7.3 TikTok
- **Qué:** Registrar una app en TikTok for Developers y usar la Content Posting API. Verificar si hace falta una auditoría de la app para publicar en público (sin ella, las publicaciones podrían quedar privadas). Plan B: subir como borrador para publicarlo a mano.
- **Archivos:** `src/publicar/tiktok.py`, `docs/PUBLICACION.md`.
- **Hecho cuando:** se sube un vídeo de prueba y el estado de la auditoría y sus limitaciones están documentados.

### [ ] 7.4 Orquestador de publicación
- **Qué:** Publicar en las 3 redes con reintentos y registrar el resultado de cada una. Si falla una red, las demás siguen adelante.
- **Archivos:** `src/publicar/__init__.py`, `data/partida/publicaciones.jsonl`.
- **Hecho cuando:** `python -m src.cli publicar output/<carpeta>` sube a las redes configuradas, y si se simula un fallo en una de ellas, el log lo muestra sin detener las otras.

---

## FASE 8 — Despliegue y programación

### [ ] 8.1 Gestión de secretos
- **Qué:** Mover todos los tokens (YouTube, Instagram, TikTok) a **GitHub Secrets**. Nada sensible en el código ni en los archivos del repositorio.
- **Archivos:** `.env.example`, `docs/DESPLIEGUE.md`.
- **Hecho cuando:** una búsqueda en el repositorio no encuentra ningún token, los Secrets están creados en la configuración del repositorio, y el pipeline funciona leyendo solo variables de entorno.

### [ ] 8.2 Desplegar en GitHub Actions
- **Qué:** Crear el workflow de GitHub Actions: instalar Python, las dependencias y ffmpeg en cada ejecución, ejecutar el pipeline (fase 6) y la publicación (fase 7), y hacer commit de vuelta al repositorio con el estado actualizado de la partida (`data/partida/`) para que la siguiente ejecución continúe desde ahí.
- **Archivos:** `.github/workflows/generar.yml`, `docs/DESPLIEGUE.md`.
- **Hecho cuando:** una ejecución manual del workflow (`workflow_dispatch`) genera y publica un vídeo, y el commit con el estado actualizado queda en el historial del repositorio.

### [ ] 8.3 Programar la frecuencia
- **Qué:** Añadir el disparador `schedule` (cron) al workflow, con la frecuencia (diaria, a una hora fija) configurable desde un solo sitio.
- **Archivos:** `.github/workflows/generar.yml`, `config.yaml`.
- **Hecho cuando:** se producen al menos 2 ejecuciones automáticas seguidas sin intervención, visibles en la pestaña Actions del repositorio.

### [ ] 8.4 Avisos y registro
- **Qué:** Que cada ejecución deje su log en la pestaña Actions del repositorio (ya ocurre por defecto) y, además, un aviso al usuario si una ejecución falla (GitHub ya avisa por correo de los workflows fallidos si están activadas las notificaciones; valorar si hace falta algo adicional, como Telegram).
- **Archivos:** `src/avisos.py` (solo si se decide algo más allá del aviso nativo de GitHub), `docs/DESPLIEGUE.md`.
- **Hecho cuando:** un fallo provocado a propósito genera un aviso que llega al usuario.

---

## FASE 9 — Cierre

### [ ] 9.1 Prueba de extremo a extremo durante 3 días
- **Qué:** Dejar el sistema funcionando solo y revisar los vídeos, las publicaciones y los logs.
- **Archivos:** `PROGRESO.md` (resultado de la prueba).
- **Hecho cuando:** 3 días seguidos sin fallos (o con los fallos resueltos y documentados).

### [ ] 9.2 Documentación final
- **Qué:** Un README con la instalación, la configuración, cómo cambiar la frecuencia, cómo reiniciar la partida y cómo renovar los tokens.
- **Archivos:** `README.md`, `docs/`.
- **Hecho cuando:** siguiendo solo el README se puede montar el proyecto desde cero.

---

## Dudas abiertas

✅ Todas resueltas. Ver `docs/DECISIONES.md` para el detalle completo.
