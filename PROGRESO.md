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
