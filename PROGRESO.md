# PROGRESO — Historial del proyecto «Concello de Batalla»

Las entradas no se borran. Las nuevas se añaden al final.

---

## 2026-11-18 — Creación del plan y de las reglas

- **Qué se hizo:** se crearon `PLAN.md` (plan paso a paso, fases 0 a 9), `CLAUDE.md` (reglas de trabajo) y este archivo `PROGRESO.md`.
- **Cómo se completó:** el plan se basa en la descripción del proyecto (`base.txt`). Cada paso indica qué se hace, qué archivos se tocan y su criterio de «Hecho cuando». Al final de `PLAN.md` hay 10 dudas abiertas sobre las reglas del juego.
- **Decisiones tomadas:** ninguna definitiva. Hay propuestas pendientes de aprobación: stack en Python + ffmpeg, y descartar Vercel como hosting para el renderizado de vídeo por sus límites de tiempo de ejecución.
- **Problemas:** ninguno.
- **Pendiente:** que el usuario apruebe el plan. Después, empezar por el paso 0.1 (resolver las dudas de las reglas).

---

## 2026-11-18 — Detalle de las 7 fases del vídeo y mecánica de batalla

- **Qué se hizo:** el usuario detalló la estructura completa de un vídeo (7 fases: intro, selección de atacante, selección de defensor, tirada de dados, multiplicador y empate, conquista, repetición x3) y la mecánica exacta de puntuación. Se creó `docs/DECISIONES.md` con todo recogido, y se actualizó `PLAN.md` (pasos 3.2, 3.4, y toda la fase 4 de gráficos, que pasó de 4 a 6 pasos) y la lista de dudas abiertas.
- **Cómo se completó:**
  - Decisiones nuevas: el multiplicador se aplica solo al bando con más vacas (no a ambos por diferencia relativa); los empates tras multiplicador se resuelven con dados de muerte súbita; el ganador de cada enfrentamiento siempre conquista al perdedor (sea este atacante o defensor); cada vídeo encadena 3 batallas (fases 2–6 repetidas 3 veces) dentro de una partida larga de 313 concellos.
  - `PLAN.md`: el paso 3.2 ahora describe la suma de diferencias por dado + multiplicador al bando con más vacas + muerte súbita. El paso 3.4 añade que el territorio conquistado se pinta con el color del ganador. La fase 4 de gráficos se dividió en 4.1 (estilo), 4.2 (mapa con zoom al atacante), 4.3 (pantalla de enfrentamiento con siluetas), 4.4 (dados y marcador con bonus/muerte súbita), 4.5 (animación de conquista) y 4.6 (intro + 3 batallas encadenadas + cierre). El paso 6.1 ahora dice «simula 3 batallas» en vez de una.
  - Dudas abiertas: se marcaron como resueltas las antiguas #1 (multiplicador del defensor), #3 (qué pasa si pierde el atacante), #4 (empates) y #5 (alcance de cada vídeo). Quedan abiertas: base del cálculo del porcentaje de vacas, si el multiplicador de un dueño con varios concellos usa la suma de todo su territorio, qué pasa al conquistar toda Galicia, valor por defecto sin datos de vacas, idioma de los vídeos y duración/frecuencia objetivo.
- **Problemas encontrados:** ninguno.
- **Pendiente:** el usuario revise `docs/DECISIONES.md` y responda las dudas que siguen abiertas antes de cerrar el paso 0.1.

---

## 2026-11-18 — Confirmación del cálculo del porcentaje de vacas

- **Qué se hizo:** el usuario confirmó con un ejemplo (Arteixo 1500 vacas vs A Coruña 1200 vacas) cómo se calcula el porcentaje que determina el multiplicador.
- **Cómo se completó:** `(1500 − 1200) / 1200 = 25 %` → redondeo a la decena (unidad 5 → hacia abajo) → 20 % → multiplicador ×1,2 para Arteixo. Esto confirma la fórmula `(mayor − menor) / menor` que ya se usaba por defecto; no hubo que cambiar la tabla de multiplicador del paso 3.1 de `PLAN.md`. Se añadió el ejemplo a `docs/DECISIONES.md` y se marcó esta duda como resuelta en `PLAN.md`.
- **Problemas encontrados:** ninguno.
- **Pendiente:** quedan 5 dudas abiertas en `PLAN.md` (multiplicador con territorio múltiple, fin de partida, concellos sin datos de vacas, idioma, duración/frecuencia).

---

## 2026-11-18 — Resueltas las últimas 5 dudas abiertas (paso 0.1 completado)

- **Qué se hizo:** el usuario respondió las 5 dudas que quedaban. Se actualizó `docs/DECISIONES.md` con cada respuesta, se marcó el paso 0.1 como `[x]` en `PLAN.md`, se vació la sección de dudas abiertas y se ajustaron los pasos 3.1, 2.3, 4.1, 4.6, 6.1 y 6.2 de `PLAN.md` para reflejar las decisiones.
- **Cómo se completó:**
  - **Multiplicador con varios concellos:** confirmado que usa la suma de vacas de **todo el territorio** del dueño, no solo del concello en combate. Las vacas se suman al conquistar (ejemplo: si A Coruña gana a Arteixo, pasa a tener 1200+1500=2700 vacas). Afecta al paso 3.1 (la función de multiplicador debe recibir el total del territorio, no las vacas de un único concello).
  - **Fin de partida:** es una serie diaria estilo TikTok que avanza de forma gradual; termina cuando un único dueño se queda con todo el territorio de Galicia y se declara ganador en ese vídeo. No hay reinicio automático (una temporada nueva sería una decisión manual posterior, fuera de alcance por ahora). Afecta al paso 6.1 (vídeo especial de cierre de serie).
  - **Concellos sin datos de vacas:** dos casos distintos — si oficialmente tienen 0 vacas, se usa 1 vaca (evita dividir por cero); si falta el dato en la fuente, se resuelve caso por caso cuando el usuario revise el conjunto de datos (paso 2.3), no se inventa un valor.
  - **Idioma:** gallego para todo el contenido de los vídeos (textos en pantalla, títulos, descripciones, narración). La documentación interna del proyecto sigue en castellano. Afecta a los pasos 4.1, 4.6 y 6.1.
  - **Duración y frecuencia:** vídeo diario, duración objetivo 80–90 segundos (1:20–1:30) con las 3 batallas dentro. Afecta a los pasos 4.6, 6.1 y 6.2 (validación de duración, y aviso de que conviene comprobar en su momento el límite real de duración de cada red).
- **Problemas encontrados:** ninguno.
- **Pendiente:** el paso 0.1 queda completado. Siguiente paso: 0.2 (elegir el stack técnico) y 0.3 (elegir el hosting gratuito), pendientes de que el usuario los apruebe.

---

## 2026-11-18 — Pasos 0.2 y 0.3 completados: stack técnico y hosting

- **Qué se hizo:** se investigaron las condiciones actuales (noviembre 2026) de GitHub Actions, Oracle Cloud Always Free y Vercel antes de recomendar nada, se preguntó al usuario sobre visibilidad del repositorio y dónde ejecutar, y se cerraron los pasos 0.2 y 0.3 de `PLAN.md`.
- **Cómo se completó:**
  - **Investigación:** confirmado que GitHub Actions da minutos ilimitados en repos públicos y 2.000 min/mes gratis en privados (de sobra para 1 vídeo diario); confirmado que Oracle Cloud Always Free sigue siendo gratis pero redujo su tope de cómputo a la mitad a mediados de 2026 (de 4 a 2 OCPU, de 24 a 12 GB), sin aviso público; confirmado que Vercel no encaja porque sus funciones serverless están pensadas para peticiones web cortas, no para procesos de varios minutos con ffmpeg.
  - **Stack técnico (0.2):** Python 3.11+ con geopandas/shapely, Pillow/pycairo y ffmpeg. Se descartó Remotion por ser más pesado de ejecutar gratis.
  - **Hosting (0.3):** se preguntó al usuario con `AskUserQuestion`. Sobre la visibilidad del repo, el usuario indicó que no tiene mucho conocimiento técnico para decidir, así que se eligió **repositorio privado** (2.000 min/mes de sobra, nadie ve el código ni los datos de la partida). Sobre dónde ejecutar, el usuario no respondió; se asumió **GitHub Actions** (en vez de una VM de Oracle Cloud) porque no exige mantenimiento de servidor, lo cual encaja con el perfil del usuario. El estado de la partida se persistirá haciendo commit al propio repositorio en cada ejecución. Todo documentado con el razonamiento en `docs/DECISIONES.md`.
  - Se actualizaron los pasos 8.1–8.4 de `PLAN.md` para ser específicos de GitHub Actions + repo privado (antes estaban redactados como disyuntiva genérica).
- **Problemas encontrados:** ninguno.
- **Pendiente:** queda toda la Fase 0 cerrada. Siguiente paso: Fase 1 (crear la estructura del repositorio). Si en el futuro 2.000 min/mes no bastaran, o el usuario prefiere más control, se puede migrar a Oracle Cloud (anotado como alternativa en `docs/DECISIONES.md`).

---

## 2026-11-18 — Análisis del vídeo de referencia y nueva fase 8 (ranking de cierre)

- **Qué se hizo:** el usuario adjuntó al Proyecto un vídeo de ejemplo del formato en el que se basa el proyecto. Se extrajeron fotogramas con ffmpeg/ffprobe (76 s, 720×1280, 30 fps) en varios instantes y se revisaron visualmente para confirmar el estilo y detectar elementos no recogidos aún en el plan.
- **Cómo se completó:**
  - Confirmado el estilo visual general: fondo azul marino oscuro, dorado para títulos/multiplicador, tipografía redondeada en negrita, línea dorada separando el mapa del panel inferior — coincide con lo ya previsto para el paso 4.1.
  - Detectados dos elementos visuales nuevos para añadir al plan: icono de espadas cruzadas antes de la tirada de dados, y pantalla de conquista con etiquetas «LOSER»/«WINNER» (adaptadas a «PERDEDOR»/«GAÑADOR» en gallego) con icono de espada apuntando al ganador. Añadidos a los pasos 4.4 y 4.5 de `PLAN.md`.
  - Detectada una **fase 8 nueva**: pantalla de cierre con el nombre de la serie, número de episodio («Ep. Nº») y dos rankings top 5 (más victorias, más territorio). Se preguntó al usuario con `AskUserQuestion` si añadirla: **sí**. Se documentó en `docs/DECISIONES.md` y en el paso 4.6 de `PLAN.md`. Decisión de diseño propia (no confirmada explícitamente por el usuario, señalada para revisión): «territorio» se mide en número de concellos controlados, no en km².
  - Esto obliga a llevar un contador de **victorias acumuladas por dueño** a lo largo de toda la serie (no solo del episodio). Se añadió a los pasos 2.4 (estado inicial) y 3.5 (persistencia) de `PLAN.md`.
  - Se preguntó también si el multiplicador debía copiar el del vídeo de referencia (que se aplica a ambos bandos a la vez, según población absoluta). El usuario respondió explícitamente que **no**, que su concepto de multiplicador es distinto y no hay que tomar el vídeo como referencia para esa parte — se mantiene la regla ya documentada sin cambios (solo multiplica el bando con más vacas, sobre la diferencia relativa).
- **Problemas encontrados:** ninguno.
- **Pendiente:** revisar con el usuario si «territorio = nº de concellos» en el ranking le convence, o prefiere otra unidad (p. ej. nº de vacas totales). Seguir con la Fase 1 cuando el usuario lo indique.

---

## 2026-11-18 — Paso 1.1 completado (repositorio y estructura) · Paso 1.2 en curso

- **Qué se hizo:** se clonó el repositorio privado `ZZurxo/concello-de-batalla` (estaba vacío), se copiaron a su raíz `PLAN.md`, `CLAUDE.md` y `PROGRESO.md` y `docs/DECISIONES.md`, y se creó la estructura de carpetas y los archivos base.
- **Cómo se completó:**
  - Carpetas: `src/{datos,motor,render,audio,publicar}`, `tests/`, `scripts/`, `data/{raw,processed,partida}`, `assets/{audio,fonts}`, `output/`, `docs/`, `.github/workflows/` (con `__init__.py` o `.gitkeep` donde hacía falta).
  - Archivos: `README.md`, `.gitignore` (excluye `.env`, `output/`, `data/raw/`, claves y tokens), `.env.example` (solo nombres de variables, sin valores), `requirements.txt` y `scripts/check_env.py`.
  - Aviso: el repositorio pasa a ser la copia de trabajo de `PLAN.md`, `CLAUDE.md`, `PROGRESO.md` y `docs/DECISIONES.md`; las copias del Proyecto de claude.ai se actualizan desde ahí.
- **Problemas encontrados:** en el entorno de esta sesión no están instalados `geopandas`, `shapely` ni `pyproj`, y la red está bloqueada para instalar paquetes. Por eso el paso 1.2 no se puede dar por terminado aquí: `python scripts/check_env.py` detecta correctamente que faltan (Python 3.13, ffmpeg 6.1, numpy, pandas, Pillow, PyYAML y pytest sí están).
- **Pendiente:** para cerrar 1.2 hay que ejecutar `pip install -r requirements.txt` en un entorno con red (en el ordenador del usuario o en GitHub Actions) y comprobar que `check_env.py` termina con «Entorno correcto». Se puede avanzar mientras tanto con los pasos que no dependen de geopandas (por ejemplo, el motor del juego, Fase 3), pero hay que pedir confirmación al usuario antes de saltarse el orden del plan.

---

## 2026-11-18 — Paso 1.1 rehecho en el repositorio real (el anterior se perdió) · Paso 1.2 sigue en curso

- **Qué se hizo:** al reanudar «sigue paso 1.2», esta sesión arrancó en un contenedor nuevo y vacío, y se comprobó que el repositorio al que apuntaba la entrada anterior (`ZZurxo/concello-de-batalla`, privado) no existe o no es accesible. El repositorio real del usuario es **`XurxoGafas/concello-de-batalla-videos`** (público) y estaba completamente vacío: el trabajo del paso 1.1 anterior nunca llegó a hacer `git push`, así que se perdió al terminar aquella sesión.
- **Cómo se completó:**
  - Se adjuntó y clonó `XurxoGafas/concello-de-batalla-videos`, y se recreó toda la estructura: carpetas `src/{datos,motor,render,audio,publicar}` (con `__init__.py`), `tests/`, `scripts/`, `data/{raw,processed,partida}`, `assets/{audio,fonts}`, `output/`, `docs/`, `.github/workflows/`.
  - Archivos creados: `README.md`, `.gitignore`, `.env.example`, `requirements.txt`, `scripts/check_env.py`, y las copias de `PLAN.md`, `CLAUDE.md` y `docs/DECISIONES.md` (con una corrección: el plan original asumía repositorio privado, pero el real creado por el usuario es público; se documentó el cambio en `docs/DECISIONES.md` — sigue encajando con GitHub Actions, que da minutos ilimitados en repos públicos).
  - Se añadió una nota nueva en `CLAUDE.md` («Nota sobre continuidad entre sesiones») recordando que cada sesión corre en un contenedor nuevo y que **solo lo que quede commiteado y empujado a GitHub persiste** — para evitar que se repita la pérdida de trabajo del paso 1.1 anterior.
  - Se intentó `pip install -r requirements.txt`: la red para PyPI está bloqueada en esta cuenta (mismo bloqueo que en la sesión anterior). Se ejecutó `python scripts/check_env.py` para documentar el estado real de este entorno.
- **Resultado de `check_env.py` en esta sesión:** Python 3.13.18, ffmpeg 6.1.1 ✅, numpy 2.5.3 ✅, pandas 3.0.5 ✅, Pillow 12.3.0 ✅, PyYAML 6.0.3 ✅, pytest 9.1.1 ✅. Faltan: `geopandas`, `shapely`, `pyproj`, `pycairo` (no se pueden instalar aquí porque el acceso a la red para `pip` está desactivado para esta cuenta).
- **Problemas encontrados:** (1) pérdida del trabajo del intento anterior de 1.1 por no haber hecho push — ya corregido con el commit de esta sesión y la nota añadida a `CLAUDE.md`; (2) red de `pip` bloqueada en esta cuenta, igual que en la sesión anterior — el usuario puede activar el acceso a la red para instalar paquetes desde los ajustes de su cuenta, o bien el paso 1.2 se puede cerrar ejecutando `check_env.py` en GitHub Actions (que instalará las dependencias desde el workflow de la fase 8) o en el propio ordenador del usuario.
- **Pendiente:** paso 1.2 sigue `[~]` en curso. Para cerrarlo hace falta un entorno con red donde `pip install -r requirements.txt` funcione y `check_env.py` termine con «Entorno correcto» — candidatos: activar red en los ajustes de la cuenta de Claude para esta sesión, instalarlo en el ordenador del usuario, o adelantar el workflow de GitHub Actions (paso 8.2) para que sea ahí donde se verifique por primera vez. Se avisa al usuario de esta disyuntiva antes de decidir por cuenta propia.


---

## 2026-11-18 — Paso 1.2 completado (entorno y dependencias)

- **Qué se hizo:** con el acceso a la red ya activado por el usuario, se creó un entorno virtual (`.venv`, ignorado por git), se instaló `requirements.txt` y se ejecutó `scripts/check_env.py`.
- **Cómo se completó:** `python -m venv .venv` + `pip install -r requirements.txt` (pycairo se compiló sin problemas). Resultado de `check_env.py`: Python 3.13.18, ffmpeg 6.1.1, geopandas 1.2.0, shapely 2.2.0, pyproj 3.8.0, Pillow 13.0.0, pycairo 1.29.2, numpy 2.5.5, pandas 3.1.1, PyYAML 6.0.3, pytest 9.2.0 → «Entorno correcto». Paso 1.2 marcado `[x]` en `PLAN.md`.
- **Problemas encontrados:** ninguno (el bloqueo de red de las sesiones anteriores ya no existe).
- **Pendiente:** siguiente paso, 2.1 (conseguir los límites geográficos de los concellos). Hay que registrar fuente, fecha y licencia en `docs/FUENTES.md` (regla j). Recordar que el entorno de cada sesión es nuevo: habrá que repetir la instalación de dependencias.

---

## 2026-11-18 — Paso 2.1 completado (límites geográficos de los concellos)

- **Qué se hizo:** se descargaron los polígonos de los 313 concellos de Galicia y se registró la fuente y la licencia en `docs/FUENTES.md`.
- **Cómo se completó:**
  - Se compararon dos fuentes oficiales. El servicio de la Xunta (IET) está actualizado a 02/2026, pero su licencia es ambigua (una ficha indica CC BY-SA 4.0 y las condiciones del IET hablan de «compatible con CC-BY 4.0»); la cláusula «compartir igual» podría afectar a los datos derivados en un repositorio público. Se eligió el **IGN (API-Features, CC BY 4.0)**, con licencia inequívoca, tal como se había planteado al usuario (que respondió «sigue»).
  - `scripts/descargar_concellos.py` descarga por páginas (con reintentos, porque el túnel de red corta a veces la conexión) y guarda `data/raw/concellos.geojson` (9 MB, ignorado por git; se regenera con el script).
  - Comprobado con geopandas: 313 concellos (A Coruña 93, Lugo 67, Ourense 92, Pontevedra 61), ids y nombres únicos, todas las geometrías válidas, EPSG:4326. Las cifras cuadran con el total oficial actual (313 tras la fusión de Cerdedo y Cotobade, que consta como «Cerdedo Cotobade»).
- **Problemas encontrados:** cortes puntuales de conexión con el servidor del IGN (resueltos con reintentos). Un fallo mío de proceso: empecé a comparar fuentes sin haber marcado el paso como en curso ni confirmado con el usuario (regla f y c); se corrigió antes de descargar nada.
- **Pendiente:** (1) confirmar antes de publicar el primer vídeo la fórmula exacta de cita que exige el IGN para productos derivados y ponerla en las descripciones (anotado en `docs/FUENTES.md`); (2) decidir cómo mostrar el nombre «Cerdedo Cotobade»; (3) siguiente paso: 2.2 (simplificar la geometría y calcular adyacencias), que exige tests con 3 parejas de vecinos y 3 que no lo son (p. ej. Ordes–Cerceda).

---

## 2026-11-18 — Paso 2.2 completado (geometría simplificada y adyacencias)

- **Qué se hizo:** se simplificaron los polígonos para dibujar rápido y se calcularon los vecinos de cada concello. Archivos: `src/datos/geometria.py`, `data/vecindades_manuales.json`, `data/processed/concellos.geojson` (2,5 MB), `data/processed/adyacencias.json` y `tests/test_geometria.py`. Se ejecuta con `python -m src.datos.geometria`.
- **Cómo se completó:**
  - **Cambio de regla (regla d):** el plan decía que los vecinos compartían frontera «no solo un punto». El usuario indicó que **basta con tocarse en una esquina**. Se actualizó el paso 2.2 de `PLAN.md` y se añadió la sección «Vecindad entre concellos» a `docs/DECISIONES.md`.
  - **Adyacencias:** se calculan con las geometrías originales (no las simplificadas) usando `intersects`. Salen 826 parejas (806 comparten línea y 20 solo un punto, p. ej. Moraña–Pontevedra). No hay casi-contactos a menos de 5 m, así que no hace falta ninguna tolerancia.
  - **Simplificación:** con `shapely.coverage_simplify` (30 m de tolerancia), que simplifica cada frontera común una sola vez. Pasa de 266.554 a 96.695 vértices, el área total se mantiene (29.577 km²) y no hay solapes entre vecinos.
  - **A Illa de Arousa:** era el único concello sin vecinos. Se preguntó al usuario (regla f) y eligió conectarla con Vilanova de Arousa y O Grove. Al comprobarlo después, las fuentes de la Xunta solo dicen que el puente la une con Vilanova de Arousa; **la premisa sobre O Grove que le di era un dato no verificado**. Por eso quedó conectada solo con Vilanova (común a todas las opciones) y se dejó anotada la duda.
  - **Tests (18, en verde):** lógica con cuadrados sintéticos (línea, esquina, separados, manual, id desconocido) y datos reales: 3 parejas vecinas (Ordes–Cerceda, Arteixo–A Coruña, Vigo–Redondela), 3 que no lo son (Ordes–Vigo, A Coruña–Ourense, Lugo–Pontevedra), una pareja de solo esquina, la isla, simetría, ≥1 vecino por concello e ids coherentes.
- **Problemas encontrados:** la isla (resuelto como se explica arriba). Un error mío: afirmé en la pregunta que el puente conectaba con dos concellos sin verificarlo.
- **Pendiente:** (1) el usuario debe confirmar si A Illa de Arousa también debe ser vecina de O Grove (una línea en `data/vecindades_manuales.json`; al cambiarlo, volver a ejecutar `python -m src.datos.geometria`); (2) siguiente paso: 2.3 (censo de vacas por concello), que exige localizar la fuente oficial, registrarla en `docs/FUENTES.md` y consultar con el usuario los concellos sin dato.

---

## 2026-11-18 — Paso 2.3 completado (censo de vacas por concello)

- **Qué se hizo:** se descargó el censo de vacas de los 313 concellos desde el IGE (como indicó el usuario) y se generó `data/processed/vacas.json`.
- **Cómo se completó:**
  - Tabla 62 del IGE («Efectivos e explotacións de gando bovino», datos del registro de bovino de la Consellería do Medio Rural), descargada de la API de datos del IGE con `scripts/descargar_vacas.py` (un solo uso, para no abusar de la API). `src/datos/vacas.py` lo cruza con los ids de los concellos (los 5 últimos dígitos del id del IGN son el código INE que usa el IGE) y valida el resultado.
  - **Decisiones mías (revisables):** variable «Número de vacas» (muxidura + non muxidura; no se cuentan terneros ni novillas) y año 2025 (el último). Constan en `docs/DECISIONES.md`.
  - **Resultado:** 313 de 313 concellos con dato, total 511.138 vacas, igual al total publicado por el IGE para Galicia. Siete concellos con 0 vacas oficiales (A Arnoia, Barbadás, Larouco, Ribadavia, Rubiá, Toén, A Illa de Arousa) pasan a 1 según la regla ya decidida (total del juego: 511.145). Las 4 filas de la tabla sin dato son concellos desaparecidos (Cesuras, Oza dos Ríos, Cerdedo, Cotobade), así que no hubo que consultar ningún caso suelto.
  - **Tests (25 en total, en verde):** lógica sintética (0→1, el dato que falta no se inventa, total que no cuadra, otros años ignorados) y datos reales (313 concellos, todos ≥ 1, el total cuadra con el oficial más los 7 ajustes, el ajuste incluye la isla).
- **Problemas encontrados:** ninguno técnico. Aviso: el servidor del IGE sirve el JSON en ISO-8859-1 (el script lo decodifica). No se ha localizado el aviso legal propio del IGE; solo se han confirmado las condiciones de la API (mostrar un aviso, no modificar los datos) y el aviso general de la Xunta (citar la fuente, no desnaturalizar).
- **Pendiente / a tener en cuenta:** (1) antes del primer vídeo, decidir dónde se muestra el aviso obligatorio del IGE y confirmar que el uso encaja con sus condiciones (anotado en `docs/FUENTES.md`); (2) **consecuencia de juego a revisar:** los datos reales son muy desiguales (A Coruña tiene solo 7 vacas, Pastoriza 15.204). Con la fórmula `(mayor − menor) / menor` y el tope del 50 %, casi cualquier enfrentamiento entre un concello rural y uno urbano dará el multiplicador máximo ×1,5; conviene ver la distribución real en el paso 3.1; (3) siguiente paso: 2.4 (unir los datos en el estado inicial: id, nombre, geometría, vecinos, vacas, color y dueño, con contador de victorias a 0).

---

## 2026-11-18 — Paso 2.4 EN CURSO (estado inicial; colores de las banderas bloqueados)

- **Qué se hizo:** el usuario confirmó que el color de cada concello debe ser **el de su bandera**. Se prepararon el código y los tests para obtener esos colores y para construir el estado inicial, pero el paso **no está completado**: faltan los colores de las banderas.
- **Cómo se avanzó:**
  - `scripts/descargar_banderas.py`: lista las banderas desde Wikidata (P41) y baja las imágenes de Commons de una en una, con pausas y respetando los 429. `src/datos/colores.py`: extrae de cada imagen una paleta de hasta 4 colores con su peso (ignora lo transparente, fusiona tonos parecidos y descarta lo que ocupa menos del 4 %); lee SVG con `rsvg-convert`. 8 tests con imágenes sintéticas.
  - `src/datos/construir_estado.py` genera `data/processed/estado_inicial.json` (313 concellos, cada uno dueño de sí mismo, vacas, vecinos, victorias a 0, episodio 0). Los concellos sin bandera reciben un color provisional marcado con `"fonte": "provisional"`. 12 tests (`tests/test_estado_inicial.py`). Total: **40 tests en verde**.
  - Cambio de plan (regla d): la geometría ya no se copia al estado (se referencia por id), porque el estado se guardará con un commit diario y la geometría es estática y pesa 2,5 MB. Paso 2.4 de `PLAN.md` actualizado.
- **Problemas encontrados:**
  1. **Cobertura:** Wikidata solo tiene imagen de bandera para **142 de los 313** concellos. Los otros ~171 no tienen imagen allí (no se sabe cuántos tienen bandera oficial sin imagen; la Xunta lleva aprobados 285 escudos y banderas de entidades locales en total, cifra que mezcla ambos símbolos).
  2. **Límite de Wikimedia:** tras 1 descarga de prueba, Commons y su servidor de archivos responden 429 con espera de 600 s, y sigue respondiendo 429 pasada esa espera (límite compartido de la red de la sesión). No se ha forzado ni rodeado. El script es reanudable: no repite lo ya descargado.
  3. El servicio de consultas de Wikidata dejó también de responder; se reutilizó el resultado de la primera consulta (guardado en `data/raw/banderas_wikidata.json`).
- **Pendiente:** decidir con el usuario (a) cómo conseguir las imágenes (reintentar más tarde, ejecutar el script desde otro entorno sin límite, o aportarlas él) y (b) cómo completar los ~171 concellos sin imagen en Wikidata y qué color provisional/definitivo usar para los que no tengan bandera. El paso 2.4 queda en `[~]`.

---

## 2026-11-18 — Paso 2.4 completado (estado inicial con colores provisionales) y nuevo paso 2.5

- **Qué se hizo:** se resolvió el bloqueo del 2.4 preguntando al usuario (regla f). Respondió: seguir con colores provisionales, genéricos y no repetidos, y que él enviará las banderas más adelante.
- **Cómo se completó:**
  - El estado inicial (`data/processed/estado_inicial.json`, 186 KB) ya tiene los 313 concellos, cada uno dueño de sí mismo, con vecinos, vacas, victorias a 0, episodio 0 y un color provisional distinto (tono, saturación y brillo variables, de modo que no se repiten). 40 tests en verde. Criterio «Hecho cuando» del 2.4 cumplido.
  - **Cambio de plan (regla d):** se añadió el paso **2.5** a `PLAN.md` (colores reales de las banderas, a partir de las imágenes que envíe el usuario) y el paso 2.4 queda `[x]`. `docs/DECISIONES.md` recoge la decisión.
  - Lo ya hecho para las banderas se aprovecha en el 2.5: `src/datos/colores.py` (paleta por imagen, 8 tests) y `scripts/descargar_banderas.py` (bloqueado por el límite de Wikimedia desde la red de la sesión; la lista de 142 banderas de Wikidata está guardada en `data/raw/banderas_wikidata.json`, ignorada por git).
- **Problemas encontrados:** los que ya constan en la entrada anterior (cobertura de Wikidata del 45 % y límite de peticiones de Wikimedia).
- **Pendiente:** (1) el usuario enviará las banderas (paso 2.5); acordar el formato/nombre de los archivos cuando las envíe; (2) siguiente paso: **3.1** (función del multiplicador), con los datos reales de vacas, que son muy desiguales (ver aviso en la entrada del 2.3).

---

## 2026-11-18 — Paso 3.1 completado (función del multiplicador)

- **Qué se hizo:** se implementó el multiplicador por vacas en `src/motor/multiplicador.py` con sus tests en `tests/test_multiplicador.py`.
- **Cómo se completó:**
  - Funciones: `bonus_porcentaje` (0–50 %), `multiplicador` (×1,0–×1,5), `multiplicadores` (solo el bando con más vacas multiplica; el otro ×1) y `vacas_de_dono` (suma de vacas de todo el territorio de un dueño). El cálculo usa fracciones exactas, para que los límites (5 %, 15 %, 35 %...) no fallen por coma flotante.
  - **27 tests en verde (67 en total):** ejemplo confirmado Arteixo 1500 / A Coruña 1200 → ×1,2; ejemplos del enunciado (30→1,3, 40→1,4, 35→1,3, 36→1,4, 70→1,5); bordes 0, 5, 6, 15, 16, 45, 46, 50, 56 y 200 %; decimales; empate a vacas; simetría; 1 vaca contra 15.204; vacas < 1 rechazadas; y un dueño con 2 concellos que usa la suma (2.700 vacas frente a 2.000 → ×1,3, frente a ×1,5 que saldría usando solo el concello).
  - **Decisión mía (revisable):** para porcentajes con decimales (que los ejemplos no cubren) se sube si sobra más de 5 de la decena y se baja si sobra 5 o menos. Con enteros coincide con la regla del usuario. Constatada en `docs/DECISIONES.md`.
- **Hallazgos con datos reales:** con el estado inicial, el **80 % de las 827 parejas de vecinos** (664) parte del tope ×1,5, y solo el 3 % sin bonus. Pero el efecto en el resultado es moderado: calculado enumerando todas las tiradas, el favorecido gana el 50 % sin bonus, ~54–58 % con ×1,1 a ×1,4 y **59 % con ×1,5** (los puntos son enteros pequeños y por eso ×1,1 y ×1,2 se parecen). Es decir, el multiplicador ayuda pero no decide, y habrá bastantes «sorpresas» a favor del concello con menos vacas.
- **Problemas encontrados:** ninguno.
- **Pendiente:** siguiente paso 3.2 (tirada de dados y puntuación): el multiplicador se aplica al total acumulado del bando con más vacas y, si hay empate, muerte súbita con semilla reproducible. En 3.2 hay que decidir cómo se comparan las puntuaciones cuando el multiplicador da decimales (p. ej. 7 × 1,3 = 9,1): se propone comparar con fracciones exactas, sin redondear, salvo que el usuario prefiera redondear la puntuación (hay que preguntarlo antes).

---

## 2026-11-18 — Paso 3.2 completado (tirada de dados y puntuación de una batalla)

- **Qué se hizo:** se implementó la batalla completa en `src/motor/batalla.py` y sus tests en `tests/test_batalla.py`.
- **Cómo se completó:**
  - **Decisión del usuario:** las puntuaciones se comparan con decimales (el usuario escribió «con decimales, solo hasta 1 decimal pero…»; el mensaje quedó cortado tras «pero»). Con puntos enteros y un multiplicador de un decimal la puntuación ya tiene como mucho un decimal, así que se guarda en décimas (enteros) y se compara exacta, sin redondeo. Si había algún matiz tras el «pero», queda pendiente de que el usuario lo aclare. Recogido en `docs/DECISIONES.md`.
  - **Diseño:** `resolver(...)` es una función pura (recibe los dados) y `simular_batalla(...)` sortea los dados con semilla y llama a `resolver`. El resultado (`ResultadoBatalla`) guarda las 3 tiradas con los puntos de cada bando, los puntos antes del multiplicador, los multiplicadores, las puntuaciones en décimas, las rondas de muerte súbita, el ganador y la semilla; eso es lo que usarán los gráficos y el audio de las fases 4 y 5.
  - **Reproducibilidad:** el orden de los sorteos queda fijado (dado de A y de B en cada tirada; después, rondas de muerte súbita) y el resultado guarda todos los dados, de modo que se puede repetir sin volver a sortear.
  - **Tests (21 nuevos, 88 en total, en verde):** ejemplo del enunciado (6-1 → +5, total 5-2); no se restan puntos al perder una tirada; tirada empatada no suma; solo multiplica el bando con más vacas; 7 × 1,3 = 9,1 exacto; un caso en que el multiplicador da la vuelta al resultado (4 vs 5 → 6,0 vs 5); empate tras multiplicador (4 × 1,5 = 6,0 contra 6) con muerte súbita; la muerte súbita no consume más dados de los necesarios y repite hasta desempatar; sin dados de desempate o con dados inválidos falla; misma semilla → mismo resultado; encadenar batallas con un generador es reproducible; y propiedades sobre 2.000 batallas aleatorias y sobre 20.000 (con vacas iguales cada bando gana el 50 %; con ×1,5 el favorecido gana ≈ 59 %, igual que el cálculo exacto).
- **Problemas encontrados:** ninguno en el código. Un test mío estaba mal montado al escribirlo (el cálculo a mano, no el código); se reescribió con casos verificados.
- **Pendiente:** siguiente paso 3.3 (selección de atacante y defensor). Hay que decidir cómo se elige el atacante «al azar entre los dueños vivos»: con la misma probabilidad para cada dueño (lo que favorece a quien tiene muchos concellos poco a poco, porque sigue siendo un solo dueño) o con probabilidad proporcional al territorio. El plan dice «al azar entre los dueños vivos»; se implementará con la misma probabilidad para cada dueño, salvo que el usuario diga otra cosa.

---

## 2026-11-18 — Paso 3.3 completado (selección de atacante y defensor)

- **Qué se hizo:** se implementó la selección del enfrentamiento en `src/motor/seleccion.py` con sus tests en `tests/test_seleccion.py`.
- **Cómo se completó:**
  - **Decisión confirmada por el usuario:** cada dueño vivo tiene la misma probabilidad de ser atacante, sin importar su tamaño.
  - Funciones: `duenos_vivos`, `territorio`, `vecinos_enemigos` (concellos de otros dueños que tocan cualquier concello del territorio), `elegir_atacante` (uniforme entre los dueños que tienen al menos un vecino enemigo), `elegir_defensor` (uniforme entre los vecinos enemigos de todo el territorio del atacante) y `elegir_enfrentamiento`, que además sortea cuál de los concellos del atacante toca al defensor (el que saldrá en pantalla). Si no queda ningún dueño con enemigos se lanza `NoHayEnfrentamiento` (fin de la partida).
  - **Reproducibilidad (regla i):** usa el `random.Random` recibido; orden de sorteos fijo (atacante, concello defensor, concello atacante) y listas ordenadas por id, de modo que no depende del orden de los diccionarios.
  - **16 tests en verde (104 en total):** el defensor siempre es colindante y de otro dueño; un dueño con varios concellos usa los vecinos de todo su territorio; un dueño sin vecinos enemigos nunca ataca; partida terminada con un único dueño; equiprobabilidad entre dueños grandes y pequeños (≈1/3 cada uno en 30.000 sorteos); equiprobabilidad entre defensores; misma semilla → mismos enfrentamientos; con los datos reales, el mapa de Galicia es conexo (necesario para que la partida pueda acabar), todos los dueños iniciales tienen enemigos y 5.000 enfrentamientos reales son válidos.
- **Problemas encontrados:** ninguno.
- **Pendiente:** siguiente paso 3.4 (conquista y actualización del estado): el ganador absorbe territorio y vacas, se eliminan dueños sin territorio y se detecta el final. Hay que tener en cuenta que `Enfrentamiento.defensor` es el dueño del concello atacado, y que las vacas de cada bando para la batalla son las de todo el territorio del dueño (`vacas_de_dono`).

---

## 2026-11-18 — Paso 3.4 completado (conquista y actualización del estado)

- **Qué se hizo:** se implementó la conquista en `src/motor/estado.py` con sus tests en `tests/test_estado.py`.
- **Cómo se completó:**
  - Funciones: `aplicar_conquista(estado, ganador, perdedor)` (devuelve un estado nuevo, sin modificar el original: el ganador absorbe todo el territorio y todas las vacas del perdedor y este se elimina), `color_de_concello` (color del dueño actual), `partida_terminada` / `ganador_de_la_serie`, y `jugar_batalla(estado, rng)`, que sortea el enfrentamiento (3.3), simula la batalla con las vacas de todo el territorio de cada bando (3.2) y aplica la conquista, devolviendo un `Episodio` con todo lo que usarán el render y el audio. Orden de sorteos fijo: selección primero, dados después, con el mismo generador.
  - **Decisión mía (revisable, en `docs/DECISIONES.md`):** el contador de victorias suma 1 al ganador y además hereda las del perdedor (así lo dice el paso 3.5 del plan: «se transfiere al ganador cuando se funden territorios»).
  - **14 tests en verde (118 en total):** absorbe territorio y vacas; gana el atacante o el defensor, igual; absorbe todo el territorio del perdedor y no solo el concello atacado; color del ganador en el territorio conquistado; victorias; estado original intacto; conquistas inválidas; fin de partida; no se puede jugar tras el final; las vacas de combate son las de todo el territorio; 50 series sintéticas siempre terminan con un único dueño tras n−1 batallas; misma semilla → misma serie; y **simulación real completa de Galicia con semilla 42: 312 batallas, un único dueño con 313 concellos y todas las vacas (el total se conserva en cada batalla), reproducible**.
- **Problemas encontrados:** ninguno.
- **Pendiente:** siguiente paso 3.5 (persistencia entre ejecuciones): guardar/cargar `estado_actual.json` e `historial.jsonl`, con número de episodio. El guardado debe incluir la semilla/estado del generador aleatorio para que 5 procesos seguidos den lo mismo que 1 proceso (o derivar una semilla por batalla, a decidir en 3.5; hay que elegir con cuidado y probablemente preguntar al usuario si afecta a la reproducibilidad pública). Además, una serie completa tiene 312 batallas, es decir, ~104 vídeos de 3 batallas (≈ 3,5 meses con un vídeo diario).

---

## 2026-11-18 — Cambio de regla en el paso 3.4: las victorias no se heredan

- **Qué se hizo:** el usuario decidió que el contador de victorias cuente solo las batallas ganadas por el propio dueño: el ganador suma 1 y **no hereda** las victorias del perdedor (ejemplo: si O Porriño gana a Ordes, que tenía 10 victorias, O Porriño solo tiene 1).
- **Cómo se completó:** `aplicar_conquista` en `src/motor/estado.py` pasó de `victorias += 1 + victorias_del_perdedor` a `victorias += 1`. Tests actualizados en `tests/test_estado.py` (el de herencia se sustituyó por uno de no herencia y otro con el ejemplo del usuario; en la simulación real, las victorias del dueño final son las batallas que ganó él mismo). 119 tests en verde. `docs/DECISIONES.md` y el paso 3.5 de `PLAN.md` actualizados (regla d); la entrada anterior de este archivo se conserva como historial.
- **Problemas encontrados:** ninguno.
- **Pendiente:** el paso 3.5 hereda este criterio: al persistir, el contador de cada dueño es el de batallas ganadas por él. Consecuencia para el ranking «Máis vitorias»: las victorias de un dueño eliminado desaparecen del ranking. Siguiente paso: 3.5.

---

## 2026-11-18 — Paso 3.5 completado (persistencia de la partida)

- **Qué se hizo:** se implementó la persistencia en `src/motor/persistencia.py` con sus tests en `tests/test_persistencia.py`.
- **Cómo se completó:**
  - Funciones: `nueva_partida`, `cargar_estado`, `guardar_estado` (atómico, formato estable), `anadir_al_historial`/`leer_historial` (JSON Lines), `jugar_episodio` (juega 3 batallas encadenadas, avanza el número de episodio y se detiene si la partida termina) y `jugar_y_guardar`.
  - **Decisión mía (revisable, en `docs/DECISIONES.md`):** semilla de serie **secreta** (`SEMILLA_SERIE`, añadida a `.env.example`, no se guarda en el repositorio) y semilla por batalla derivada con SHA-256 de `semilla_serie:nº_de_batalla`, que sí se guarda en el historial. Así no hace falta arrastrar el estado del generador entre procesos, y como el repositorio es público nadie puede adelantar los resultados futuros. Contrapartida: la semilla de serie no se puede recuperar si se pierde.
  - **11 tests en verde (130 en total):** semilla estable y distinta por batalla y serie; falla sin `SEMILLA_SERIE`; un episodio = 3 batallas y episodio +1; se detiene al terminar la partida; el registro guarda semilla y todos los dados; repetir con la misma serie da lo mismo; una batalla del historial se reproduce desde su semilla; guardar/cargar idéntico y formato estable; el historial solo se añade; continuar donde se dejó; y el criterio «Hecho cuando»: **5 batallas en 5 procesos distintos (subprocesos reales sobre el estado de Galicia) = 5 batallas en un solo proceso**, con el contador de victorias de cada dueño igual a las batallas que ganó él mismo.
  - No se ha creado todavía `data/partida/estado_actual.json`: la serie real empezará con el comando de la fase 6/8 y la semilla elegida por el usuario.
- **Problemas encontrados:** ninguno de fondo (un test comparaba tuplas con listas tras pasar por JSON; se ajustó el test).
- **Pendiente:** (1) el usuario debe elegir y guardar la semilla de serie antes de empezar la serie real (en GitHub Secrets, paso 8.1, y una copia propia); (2) siguiente paso 3.6 (simulación por consola, `src/cli.py`), que usará una semilla pasada por argumento para las pruebas.

---

## 2026-11-18 — Paso 3.6 completado (simulación por consola) · Fase 3 cerrada

- **Qué se hizo:** `src/cli.py` con el comando `python -m src.cli simular --batallas N --semilla S`, y sus tests en `tests/test_cli.py`.
- **Cómo se completó:** simula N batallas desde el estado inicial de Galicia y escribe cada una en texto: bandos (con el tamaño del territorio si tiene más de un concello), vacas, las 3 tiradas con quién suma, puntos, multiplicador, puntuación final con decimales, muerte súbita si la hay, ganador y estado resultante. Usa las mismas semillas derivadas que la persistencia (`semilla_de_batalla`), así que la batalla n-ésima de una semilla es la misma que jugaría la serie real con esa semilla de serie. **No guarda nada** en `data/partida/`. Se detiene si la partida termina.
- **7 tests en verde (137 en total):** el comando exacto del plan imprime 10 batallas completas; misma semilla → misma salida y otra semilla → otra; las primeras batallas no dependen de cuántas se pidan; no escribe en `data/partida/`; una simulación completa de Galicia termina en 312 batallas con ganador; argumentos inválidos fallan; formato de números (1.234, 10,5).
- **Problemas encontrados:** ninguno (limpié una línea mía mal escrita antes de probar).
- **Pendiente:** la fase 3 está completa. Siguiente: fase 4 (gráficos), empezando por el paso 4.1 (guía visual), que exige aprobación del usuario de un fotograma de muestra. Antes conviene decidir con el usuario el paso 2.5 (banderas) o seguir con colores provisionales; también necesita elegir tipografía con licencia libre (registrar en `docs/FUENTES.md`, regla j) y revisar el vídeo de referencia.

---

## 2026-11-18 — Paso 4.1 EN CURSO (guía visual; falta la aprobación del usuario del fotograma de muestra)

- **Qué se hizo:** se fijó la guía visual y se generó un fotograma de muestra con datos reales.
- **Cómo se avanzó:**
  - `src/render/estilo.py`: constantes (1080×1920, 30 fps, zonas seguras 60/140/220/420 px, paleta, tamaños de texto) y utilidades (texto centrado, partir nombres largos en 2 líneas, dado con puntos, contraste WCAG). `docs/ESTILO.md` explica cada decisión.
  - **Tipografía:** Lilita One (SIL OFL 1.1), descargada de Google Fonts a `assets/fonts/` con su licencia; registrada en `docs/FUENTES.md` antes de usarla (regla j). Cobertura de ñ, tildes, ü, ¡, ¿ y × comprobada con un test (se añadió `fonttools` a `requirements.txt`).
  - `src/render/muestra_estilo.py` genera `output/muestras/estilo.png`: título «CONCELLO DE BATALLA · Ep. 27», mapa con 120 batallas ya jugadas (colores provisionales), línea dorada, siluetas reales de los dos concellos con nombre y vacas, tres dados por bando y la insignia «×1,5». Se envió al usuario.
  - 6 tests en `tests/test_estilo.py` (143 en total).
- **Problemas encontrados:** en la primera versión los nombres largos se solapaban y la insignia del multiplicador tapaba la puntuación; se corrigió partiendo los nombres en dos líneas y recolocando el marcador.
- **Pendiente:** que el usuario apruebe el fotograma (o pida cambios) para marcar 4.1 como `[x]`. Puntos a mirar por el usuario: el mapa ocupa poco ancho (Galicia es casi cuadrada y la zona segura recorta la altura); las zonas seguras son prudentes y se comprobarán con un vídeo real (6.3).

---

## 2026-11-18 — Paso 4.1 (en curso): ajustes tras la primera revisión del usuario

- **Qué se pidió:** (1) el mapa gusta, pero en el enfrentamiento debe hacer zoom a los concellos que pelean, con menos zoom si el territorio ya es muy grande; (2) el «×1,5» estaba descentrado en su recuadro; (3) separar más del dado el número de resultado; (4) marcar en rojo la silueta de los concellos en conflicto en el mapa; (5) poner entre el número de vacas la diferencia en % entero aproximado («diff vacas +50%»); (6) todo lo relacionado con vacas (cifras, porcentaje y multiplicador) coloreado como una vaca pinta (blanca con manchas negras).
- **Cómo se resolvió:**
  - Zoom: `caja_de_zoom` en `src/render/estilo.py` encuadra los territorios completos de los dos bandos con 20 % de aire, mínimo 40 km y la proporción de la zona del mapa; nunca recorta, así que un territorio enorme se ve entero con menos zoom. (El paso 4.2 reutilizará esta función en `src/render/mapa.py`.)
  - Contorno rojo (`CONFLICTO`) en los dos concellos que se enfrentan; la puntuación pasa a un lado de los dados; el multiplicador va debajo de los dados.
  - `pastilla_vaca`: pastilla blanca con manchas negras en los bordes y texto con halo, centrado por su tinta real (corrige el desajuste del «×1,5»). Se aplica a las vacas de cada bando, a la diferencia y al multiplicador.
  - **Decisión mía (revisable):** el % mostrado es la diferencia real `(mayor − menor)/menor` redondeada, **sin el tope del 50 %** (`diferencia_porcentual` en `src/motor/multiplicador.py`, con tests): p. ej. 143 contra 3 vacas muestra «+4.667%», mientras el multiplicador sigue topado en ×1,5. Es más informativo, pero con los datos reales aparecen cifras muy grandes (A Coruña 7 vacas contra Pastoriza 15.204 → «+217.057%»); si no gusta, se puede mostrar un tope tipo «+999%» o el % del bonus.
  - Se generan 3 muestras (`estilo.png`, `estilo_zoom_minimo.png`, `estilo_zoom_grande.png`) para ver el comportamiento del zoom; `docs/ESTILO.md` actualizado; tests ampliados (zoom, pastillas, centrado): 155 en total.
- **Problemas encontrados:** las manchas de la primera versión eran demasiado grandes y tapaban letras; la insignia ×1,5 quedaba pegada a los dados. Se redujeron las manchas y se recolocó.
- **Pendiente:** que el usuario apruebe las muestras para marcar 4.1 `[x]`.

---

## 2026-11-18 — Paso 4.1 (en curso): tope del 50 % en la diferencia de vacas mostrada

- **Qué se pidió:** cuando el porcentaje de diferencia de vacas sea mayor que 50, mostrar simplemente «+50»; en el resto, el valor real.
- **Cómo se resolvió:** `diferencia_porcentual` (`src/motor/multiplicador.py`) ahora devuelve como máximo 50 (el valor real por debajo del tope), con tests (143 contra 3 → 50; 149 contra 100 → 49; 150 → 50). Esto sustituye la decisión mía anterior de mostrar la cifra real sin tope; `docs/ESTILO.md` actualizado y muestras regeneradas.
- **Pendiente:** que el usuario apruebe las muestras para marcar 4.1 `[x]`.

---

## 2026-11-18 — Paso 4.1 (en curso): fondo de hierba viva

- **Qué se pidió:** sustituir el fondo azul marino por un fondo de hierba verde «viva y guay» (opción 1 de dos que valoró el usuario; la opción 2, un rayo que parte la pantalla con una foto de cada concello, queda como mejora futura pendiente de que el usuario envíe las fotos con su autor y licencia).
- **Cómo se resolvió:** `src/render/fondo.py` dibuja el césped por código (sin imágenes ni licencias externas, determinista con semilla): gradiente de verde, briznas en capas con raíz oscura y punta clara, manchas de sol y viñeta; admite una fase de viento (0–1, cíclica) para animarlo más adelante. Tarda ~0,8 s por fotograma, así que se dibujará una vez y se reutilizará. Para mantener la legibilidad: título con trazo oscuro grueso, mapa con líneas doradas arriba y abajo (el mar sigue azul marino), panel de datos como tarjeta azul marino casi opaca; los 420 px inferiores quedan solo con hierba. Silueta de concello con fondo transparente (antes se veía un recuadro más oscuro sobre el panel) y sin hueco entre el mapa y la línea dorada.
- **Tests:** 3 nuevos (fondo verde y determinista, viento cíclico, contraste del texto) y el test del fotograma comprueba que la zona inferior es hierba: 154 en total. `docs/ESTILO.md` actualizado.
- **Problemas encontrados:** la primera hierba se veía plana (briznas del mismo tono que la base); se añadieron raíz oscura y puntas claras en capas.
- **Pendiente:** que el usuario apruebe las muestras para marcar 4.1 `[x]`. Posible paso nuevo (a decidir con el usuario): foto de cada concello con rayo en el panel de enfrentamiento, que necesitaría registrar fuente y licencia de cada foto (regla j).

---

## 2026-11-18 — Paso 4.1 completado (guía visual aprobada)

- **Qué se hizo:** el usuario aprobó las muestras (`estilo.png`, `estilo_zoom_minimo.png`, `estilo_zoom_grande.png`). El paso queda `[x]`.
- **Cómo se completó:** ver las entradas anteriores del 4.1 y `docs/ESTILO.md`. Resumen de lo fijado: 1080×1920 a 30 fps; zonas seguras 60/140/220/420 px; tipografía Lilita One (OFL); fondo de hierba dibujado por código; mapa con zoom que encuadra los territorios completos de los dos bandos; contorno rojo en los concellos en conflicto; pastillas «de vaca» para vacas, diferencia (tope +50 %) y multiplicador; todo en gallego.
- **Problemas encontrados:** los ya descritos en las entradas del 4.1.
- **Pendiente / a tener en cuenta:** (1) el usuario valoró cambiar a Node para animar más fácil; la opinión fue mantener Python (el motor y los 154 tests ya están ahí) y decidir de nuevo tras el prototipo de animación del paso 4.4 (medir tiempo de render y aspecto; si no convence, se puede sustituir solo el renderizador porque el motor guarda las batallas como datos); (2) posible paso futuro: foto de cada concello con rayo en el panel de enfrentamiento (necesita fotos con autor y licencia); (3) siguiente paso: 4.2 (renderizar el mapa).

---

## 2026-11-18 — Paso 4.2 (renderizar el mapa): en curso, a falta de aprobación

- **Qué se hizo:** módulo `src/render/mapa.py` (`MapaGalicia`: geometrías por dueño, ventanas general/atacante/enfrentamiento, dibujo con supersampling, contornos y nombres opcionales) y muestras `src/render/muestra_mapa.py` → `output/muestras/mapa_inicial.png` y `mapa_zoom_atacante.png`. `muestra_estilo.py` usa ahora `MapaGalicia`.
- **Cómo se hizo:** cada concello se pinta con el color de su dueño; la ventana del atacante enseña su territorio completo más los vecinos enemigos. Por decisión del usuario, **el mapa general no lleva nombres**; solo se escriben en zoom y solo los de los concellos en conflicto (nombre del dueño, tamaño 30–52 px, siempre dentro de la imagen).
- **Cambio en el panel del estilo:** para ser coherente con el mapa, ahora muestra el nombre del **dueño** y la silueta de todo su territorio (antes, el nombre del concello). A confirmar en el paso 4.3.
- **Problemas encontrados:** el primer etiquetado automático de todos los dueños se descartó tras la indicación del usuario; un test de color fallaba por 1 unidad de antialiasing (tolerancia 6).
- **Tests:** `tests/test_mapa.py` (11) → 165 en total, todos pasan. `docs/ESTILO.md` actualizado.
- **Pendiente:** que el usuario confirme que las muestras se leen bien en el móvil (criterio «Hecho cuando») para marcar 4.2 `[x]`; después, 4.3.

---

## 2026-11-18 — Paso 4.2 completado (mapa de Galicia)

- **Qué se hizo:** el usuario confirmó las muestras (`mapa_inicial.png`, `mapa_zoom_atacante.png`) y el panel con nombre y silueta del dueño. El paso queda `[x]`.
- **Cómo se completó:** ver la entrada anterior del 4.2 (módulo `src/render/mapa.py`, muestras, 11 tests, 165 en total).
- **Problemas encontrados:** los ya descritos.
- **Pendiente:** siguiente paso, 4.3 (pantalla de enfrentamiento con siluetas).

---

## 2026-11-18 — Paso 4.3 EN CURSO (pantalla de enfrentamiento; falta la aprobación de la muestra)

- **Qué se hizo:** `src/render/enfrentamiento.py` con `fotograma_base` (título, mapa con zoom y contornos rojos, panel, siluetas de los territorios completos, nombre del dueño, rótulos ATACA/DEFENDE, «VS», pastillas de vaca con vacas y diferencia) y `pantalla_enfrentamiento`. `muestra_estilo.py` se simplificó: ahora reutiliza `fotograma_base` y solo añade los dados. Muestra: `output/muestras/enfrentamiento.png`.
- **Tests:** `tests/test_enfrentamiento.py` (5) → 170 en total, todos en verde.
- **Problemas encontrados:** ninguno. La pantalla deja libre la zona de dados a propósito (continuidad con 4.4); las siluetas de territorios estrechos salen pequeñas.
- **Pendiente:** que el usuario apruebe la muestra para marcar 4.3 `[x]`; después, 4.4 (dados y marcador).

---

## 2026-11-18 — Paso 4.3 (en curso): fondo con la foto de hierba del usuario

- **Qué se pidió:** poner como fondo una foto de hierba que el usuario aportó (de una página «sin copyright»).
- **Cómo se resolvió:** la imagen (`assets/img/hierba.avif`, 500×750) se escala para cubrir 1080×1920 y se recorta centrada, con un ligero afinado (`fondo_foto` en `src/render/fondo.py`). La usan `enfrentamiento.py` y las muestras (`estilo*.png`, `mapa_*.png`). La hierba dibujada por código se conserva como alternativa. Los tests de «zona inferior verde» se relajaron porque la foto es más apagada. 171 tests en verde.
- **Licencia (regla j):** registrada en `docs/FUENTES.md` con lo que se sabe, pero **falta el nombre/URL de la página, el autor y el texto de la licencia**. Hasta tenerlos, no se publica ningún vídeo con este fondo.
- **Problemas encontrados:** la foto es pequeña y se amplía ×2,5: queda algo suave, aceptable para un fondo. Para animar el viento (4.4+) la foto no ofrece fase de viento; se podría hacer un desplazamiento suave.
- **Pendiente:** que el usuario facilite la fuente/licencia de la foto y apruebe la pantalla para marcar 4.3 `[x]`.

---

## 2026-11-18 — Paso 4.3 (en curso): mar azul cielo y panel blanco con manchas de vaca

- **Qué se pidió:** cambiar el azul marino del mapa por azul cielo y el panel de dados/peleas por un fondo blanco con manchas de vaca, con textos y delineados que se vean claros.
- **Cómo se resolvió:** `MAR` pasa a `#7CC6F0` y el mapa lo usa de fondo; `panel_vaca`/`pegar_panel` (en `estilo.py`) dibujan el panel blanco con manchas suaves en los bordes (determinista). Textos del panel en azul marino con halo blanco; ATACA rojo, DEFENDE azul; bordes marino en siluetas y dados (más gruesos). Se aplicó a `enfrentamiento.py`, `muestra_estilo.py` y `muestra_mapa.py`. 173 tests en verde.
- **Problemas encontrados:** las primeras manchas eran enormes y angulosas y una tapaba el multiplicador; se hicieron más pequeñas, redondeadas y pegadas a los bordes.
- **Pendiente:** que el usuario apruebe la pantalla (y aporte la fuente/licencia de la foto de hierba) para marcar 4.3 `[x]`.

---

## 2026-11-18 — Paso 4.3 (en curso): dados en vertical con «+N» junto al dado ganador

- **Qué se pidió:** disposición vertical de los dados para ver de dónde salen los puntos; que los puntos ganados (p. ej. «+2» de Frades) aparezcan al lado del dado que los gana; mantener el resalte del dado ganador.
- **Cómo se resolvió:** dos columnas de 3 dados (una por bando), fila a fila; borde dorado en el dado que gana la tirada y, por fuera de él, insignia verde «+N» (gris «=» en empate); marcador total en el centro y multiplicador bajo el total del bando con más vacas. El mapa se redujo de 510 a 440 px de alto para que cupieran los dados sin invadir la zona inferior reservada. Constantes de layout de `enfrentamiento.py` ajustadas (afecta también a la pantalla 4.3). Colores `VERDE_PUNTOS` y `GRIS_EMPATE` en `estilo.py`.
- **Problemas encontrados:** al principio el total quedaba pegado a la columna del defensor; se separaron las columnas de dados hacia fuera (x = 235 y 845).
- **Pendiente:** aprobación del usuario para marcar 4.3 `[x]` (y fuente/licencia de la foto de hierba). El dibujo de dados vive aún en `muestra_estilo.py`; en 4.4 pasa a `dados.py`/`marcador.py`.

---

## 2026-11-18 — Paso 4.3 completado (pantalla de enfrentamiento)

- **Qué se hizo:** el usuario aprobó la pantalla de enfrentamiento y la disposición vertical de los dados, y pidió aplicar los cambios (foto de hierba, mar azul cielo, panel blanco con manchas, textos claros) a todas las pantallas. Se comprobó que `mapa_inicial.png`, `mapa_zoom_atacante.png`, `estilo*.png` y `enfrentamiento.png` ya los usan, porque comparten `fondo_foto`, `MAR`, `pegar_panel` y `fotograma_base`. Paso `[x]`.
- **Cómo se completó:** ver las entradas anteriores del 4.3 y `docs/ESTILO.md`.
- **Problemas encontrados:** los ya descritos.
- **Pendiente:** (1) la fuente y licencia de la foto de hierba (`docs/FUENTES.md`) antes de publicar nada; (2) siguiente paso, 4.4 (animación de dados y marcador), que es donde se decide si el rendimiento de Python basta para animar.

---

## 2026-11-18 — Registrada la fuente y licencia de la foto de hierba

- **Qué se hizo:** el usuario indicó la página de origen de la foto de fondo (Unsplash). Se comprobó en la página: autor bady abbas, licencia Unsplash (uso comercial permitido, atribución no obligatoria, sin compilar imágenes para un servicio competidor). Registrada en `docs/FUENTES.md` (regla j); queda resuelto el pendiente del paso 4.3.
- **Pendiente:** decidir si se acredita al autor en las descripciones (opcional). Siguiente: paso 4.4 en curso (animación de dados y marcador); `crear_pastilla` (RGBA) ya extraída de `pastilla_vaca` para poder animar la pastilla.

---

## 2026-11-18 — Cambio de regla (paso 2.2): vecinos solo por frontera con línea

- **Qué se pidió:** el usuario cambió de criterio: un concello solo se considera colindante si hace frontera **con línea**; tocarse en una esquina ya no cuenta, porque la conquista se vería rara.
- **Cómo se resolvió:** `calcular_adyacencias` (`src/datos/geometria.py`) exige que la intersección de las fronteras tenga longitud > 0 (`LONGITUD_MINIMA`, 1e-6°). Se regeneraron `data/processed/adyacencias.json` y `estado_inicial.json` (solo cambian los vecinos; colores y vacas idénticos). Pasan de 827 a **807 parejas**; las 20 descartadas (p. ej. Moraña–Pontevedra, Cervo–Viveiro, Rianxo–Rois) están listadas en `docs/DECISIONES.md`. `PLAN.md` (paso 2.2) y `docs/DECISIONES.md` actualizados (regla d); la entrada anterior del 2.2 se conserva como historial.
- **Comprobaciones:** el mapa sigue conexo (313 de 313 alcanzables) y ningún concello queda sin vecinos (A Illa de Arousa sigue unida a mano a Vilanova de Arousa). Tests: se cambió el de esquinas (ahora «no son vecinos»), se añadió uno de frontera parcial corta y otro de conexión; 175 tests en verde.
- **Efecto en el juego:** la selección de defensor (3.3) usa estas adyacencias, así que ahora solo se atacan concellos que comparten línea; las simulaciones con una semilla dada dan resultados distintos a los anteriores a este cambio (la serie real aún no ha empezado).
- **Pendiente:** retomar el paso 4.4 (animación de dados; ya hay un primer render en `output/muestras/`).

---

## 2026-11-18 — Paso 4.4 EN CURSO (animación de dados y marcador; falta la aprobación de los vídeos de muestra)

- **Qué se hizo:** `src/render/dados.py` (sprites del dado, hueco, insignia «+N» y espadas cruzadas dibujadas por código; suavizados; geometría de las columnas), `src/render/marcador.py` (totales con decimales, multiplicador con halo, tarjeta de muerte súbita, recuadro del ganador) y `src/render/animacion_batalla.py` (línea de tiempo, `fotograma(base, r, t)` sin estado, codificación a MP4 con ffmpeg/libx264). Se extrajo `crear_pastilla` (RGBA) de `pastilla_vaca` para poder escalarla en la animación. Muestras: `output/muestras/batalla_sin_audio.mp4` (10,4 s, con multiplicador) y `batalla_muerte_subita.mp4` (12,9 s, con una ronda de desempate).
- **Cómo se hizo:** el fotograma base (4.3) se dibuja una vez por batalla y cada fotograma solo copia la base y pinta los dados, insignias y marcador (muy barato). Los dados cambian de cara de forma determinista (semilla = clave + instante), así que el vídeo es reproducible.
- **Rendimiento (para la decisión Python vs Node):** 312–387 fotogramas de 1080×1920 se generan y codifican en ≈12 s por vídeo, y el fotograma base cuesta ≈1 s. Un episodio de 3 batallas con conquista y cierre (≈90 s) saldrá en torno a 1–2 minutos de cómputo: Python **es suficiente** por ahora.
- **Problemas encontrados:** los totales con decimales («3,0 - 3,0») chocaban con el guion central: se separaron las columnas del marcador (±105 px) y se redujo la letra de los decimales; un test mío de muerte súbita tenía mal los dados (no empataba) y otro miraba un borde dorado del dado vecino. Se corrigieron los tests.
- **Tests:** `tests/test_animacion_batalla.py` (9) → 184 en total, todos en verde. `docs/ESTILO.md` actualizado.
- **Pendiente:** que el usuario revise los dos vídeos y apruebe (criterio «Hecho cuando»: «se ve fluida, sin saltos»; yo solo he comprobado fotogramas sueltos y que no hay saltos bruscos entre ellos, no he podido verlos reproducirse). Sin audio todavía (fase 5). Después, 4.5 (conquista).

---

## 2026-11-18 — Paso 4.4 (en curso): navaja gallega y botella de licor café en vez de las espadas

- **Qué se pidió:** cambiar las espadas cruzadas por una navaja de bolsillo típica gallega con mango de madera y una botella de licor café.
- **Cómo se resolvió:** `navaja_botella_sprite` (en `dados.py`, sustituye a `espadas_sprite`) dibuja por código una navaja abierta (hoja plateada, virola de latón, mango de madera con vetas y remaches) y una botella marrón con tapón dorado y etiqueta «CAFÉ», inclinadas una hacia la otra. Se actualizaron la animación, los tests, `PLAN.md` (4.4) y `docs/ESTILO.md`. Vídeos de muestra regenerados; imagen de comprobación en `output/muestras/inicio_duelo.png`.
- **A tener en cuenta:** el paso 4.5 del plan habla de un «icono de espada apuntando hacia el ganador»; probablemente convenga cambiarlo también (p. ej. una navaja), a decidir con el usuario al empezar el 4.5.
- **Pendiente:** aprobación de los vídeos y del icono para marcar 4.4 `[x]`.

---

## 2026-11-18 — Paso 4.4 (en curso): rediseño de la navaja y la botella (solo diseño, sin animación todavía)

- **Qué se pidió:** que la navaja se parezca a la foto de referencia que envió el usuario (navaja gallega de mango de madera clara y virola de acero con anillos), que se vea que es plegable (**entreabierta**), que la botella ponga «LIC. CAFÉ» y, más adelante, que las dos «se crucen como espadas» antes de pasar a los dados. Pidió ver el diseño **antes** de hacer la animación.
- **Cómo se hizo:** `navaja_sprite(largo, apertura)` y `botella_sprite(alto)` en `src/render/dados.py`; la navaja tiene la hoja girada 55° respecto al mango y un pasador dorado en el eje. También quedaron preparados `destello_sprite` (estrella de impacto) y los ángulos/desplazamientos de cruce (`ANGULO_NAVAJA`, `ANGULO_BOTELLA`, `DESPL_*`), aún sin usar en la animación. Muestra del diseño: `output/muestras/diseno_navaja_botella.png`.
- **Pendiente:** que el usuario apruebe (o corrija) el diseño; entonces se anima el cruce (entran por los lados, chocan con un destello y se cruzan como espadas) y se rehacen los vídeos de muestra. Hasta entonces los vídeos de muestra del repositorio llevan todavía el icono anterior.

---

## 2026-11-18 — Paso 4.4 (en curso): ajustes del diseño de la navaja

- **Qué se pidió:** la botella gusta; el mango de madera debe ser uniforme junto con los anillos, y los anillos deben ir acabando en punta, no rectos.
- **Cómo se resolvió:** mango de grosor uniforme (el mismo que el extremo ancho de la virola, sin escalón) y virola cónica que se estrecha hacia la hoja, con anillos cuya altura sigue el cono. Muestra actualizada: `output/muestras/diseno_navaja_botella.png`.
- **Pendiente:** aprobación del diseño; después, la animación del cruce.

---

## 2026-11-18 — Paso 4.4 (en curso): hoja de cuchillo con un solo filo

- **Qué se pidió:** que la hoja tenga filo solo por el lado que se cierra y el otro lado recto (lomo), para que parezca un cuchillo y no una daga.
- **Cómo se resolvió:** hoja de un solo filo: lomo recto con la muesca de la uña, y filo curvo por el lado que mira al mango al girar (el que se cerraría hacia él), con un brillo en el filo. Muestra actualizada: `output/muestras/diseno_navaja_botella.png`.
- **Pendiente:** aprobación del diseño; después, la animación del cruce.

---

## 2026-11-18 — Paso 4.4 (en curso): hoja sin círculo gris y con el brillo más corto

- **Qué se pidió:** quitar el círculo gris de la parte exterior de la hoja y acortar la línea blanca del reflejo para que acabe antes del perfil.
- **Cómo se resolvió:** eliminada la muesca de la uña (el círculo gris) y el brillo empieza y termina dentro de la hoja, sin tocar el contorno. Muestra: `output/muestras/diseno_navaja_botella.png`.
- **Pendiente:** aprobación del diseño; después, la animación del cruce.

---

## 2026-11-18 — Paso 4.4 (en curso): animación del cruce de la navaja y la botella

- **Qué se pidió:** hacer el vídeo de prueba con la navaja y la botella cruzándose como espadas antes de pasar a los dados (diseño aprobado por el usuario).
- **Cómo se resolvió:** `_duelo` en `animacion_batalla.py`: la navaja entra desde la izquierda y la botella desde la derecha, girando (0,55 s); al chocar sale un destello dorado (`destello_sprite`) y un breve temblor; quedan cruzadas (navaja a 32°, botella a 28°, con la navaja cruzando por el cuello de la botella para que se lea la etiqueta) y se desvanecen antes de los dados. La fase del duelo dura ahora 1,7 s (antes 1,1 s). Vídeos regenerados: `batalla_sin_audio.mp4` (11,0 s) y `batalla_muerte_subita.mp4` (13,5 s); imagen fija del cruce: `output/muestras/duelo_cruzado.png`. Test nuevo del duelo: 185 tests en verde.
- **Pendiente:** aprobación de los vídeos para marcar 4.4 `[x]`; después, 4.5 (conquista; ahí hay que decidir si el «icono de espada apuntando al ganador» pasa a ser la navaja).

---

## 2026-11-18 — Paso 4.4 (en curso): choque con la navaja abierta, «LIORTA!» y tarjeta en llamas

- **Qué se pidió:** (a) la caja de «morte súbita» con llamas, no solo blanca; (b) choque con la navaja abierta y recta, el filo hacia la botella y inclinada a la derecha; (c) «LIORTA!» escrito debajo del choque; (d) se mantienen el ritmo de los dados y la velocidad del cruce.
- **Cómo se resolvió:** `dados.py`: nuevas constantes de pose (navaja a -122°, botella a 14°) y `texto_sprite` (texto con borde grueso). `_duelo` usa `navaja_sprite(250, apertura=0)`, el destello y «LIORTA!» (dorado, rebote) centrado bajo el choque; los tiempos no cambian. `marcador.tarjeta_muerte_subita(img, u, t)` dibuja un degradado rojo→naranja con tres capas de lenguas (roja, naranja, amarilla) que oscilan con `t`, título blanco con borde oscuro. Tests: el de la tarjeta comprueba fuego y título blanco; test nuevo de «LIORTA!»; sprite de la navaja actualizado. 186 tests en verde. Vídeos regenerados en `output/muestras/`.
- **Problemas:** la punta de la navaja se solapaba con la pastilla «dif. vacas»; se redujeron los sprites y se bajó el conjunto.
- **Pendiente:** aprobación de los vídeos para marcar 4.4 `[x]`; después 4.5 (decidir si el icono del ganador pasa a ser la navaja).

---

## 2026-11-18 — Paso 4.4 (en curso): huecos de B, R, A, O… con el color del borde

- **Qué se pidió:** las B y R mayúsculas tenían un huequito blanco raro; que quede del color del delineado.
- **Cómo se resolvió:** con trazos gruesos la fuente dejaba una rendija del fondo en los huecos interiores. `estilo.texto_con_borde` dibuja el trazo, detecta los huecos cerrados (relleno por inundación desde fuera) y los pinta del color del borde antes de dibujar el relleno; lo usan `texto_centrado`, `texto_centrado_exacto` y `dados.texto_sprite`. Test nuevo (B con borde sin píxeles blancos dentro). Muestras y vídeos regenerados.
- **Pendiente:** igual que antes: aprobación de los vídeos para cerrar 4.4.

---

## 2026-11-18 — Paso 4.4 (en curso): proporción de la navaja abierta

- **Qué se pidió:** el mango debe medir 1,1–1,2 veces la hoja (estaba demasiado largo, ≈1,5).
- **Cómo se resolvió:** en `navaja_sprite` el mango con la virola mide ahora 175 unidades desde el pasador frente a 152 de la hoja (≈1,15; medido en el sprite abierto: ≈1,18). Virola más corta (150→214) con 5 anillos y mango de madera más corto. Muestra: `output/muestras/diseno_navaja_botella.png`; vídeos regenerados. 187 tests en verde.
- **Pendiente:** aprobación de los vídeos para cerrar 4.4.

---

## 2026-11-18 — Paso 4.4 (en curso): tamaños de la navaja y la botella en el choque

- **Qué se pidió:** hoja algo más grande, pero la navaja algo más pequeña que la botella.
- **Cómo se resolvió:** proporción del mango a 1,1 × la hoja (límite bajo del rango pedido; la hoja pesa más en el conjunto). En el duelo la botella pasa a 234 px de alto y la navaja a 244 px de largo, que al ir inclinada ocupa menos alto que la botella (≈325 vs 340 px de bajada). Límite: no se puede agrandar más sin que la botella invada las pastillas de vacas de arriba o «LIORTA!» salga de la zona. Vídeos regenerados; 187 tests en verde.
- **Pendiente:** aprobación de los vídeos para cerrar 4.4.
