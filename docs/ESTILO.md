# ESTILO — Guía visual de «Concello de Batalla»

Todas las constantes están en `src/render/estilo.py`. Fotogramas de muestra: `python -m src.render.muestra_estilo` → `output/muestras/estilo.png`, `estilo_zoom_minimo.png` y `estilo_zoom_grande.png` (con datos reales: se simulan N batallas y se dibuja la siguiente a mitad de tirada).

## Formato
- **1080×1920 (9:16) a 30 fps.** 30 fps es lo que usa el vídeo de referencia, rinde bien para redes y renderizar a 60 fps duplicaría el tiempo en GitHub Actions sin ganar nada visible en este tipo de animación.

## Zonas seguras
La interfaz de TikTok, Reels y Shorts tapa los bordes. Todo el texto importante queda dentro de: **60 px a la izquierda, 140 a la derecha (botones), 220 arriba y 420 abajo (descripción, cuenta, música).** Son valores prudentes que sirven para las tres redes; se comprobarán con un vídeo real subido como borrador en el paso 6.3.

## Fondo: hierba viva (decisión del usuario, 2026-11-18)
Césped dibujado **por código** (`src/render/fondo.py`, sin imágenes ni texturas externas: no hay licencias que registrar y sale idéntico en cualquier máquina). Gradiente de verde oscuro arriba a verde luminoso abajo, briznas en capas con raíz oscura y punta clara, manchas de sol y viñeta suave. Admite una fase de viento (0–1, cíclica) para animar el balanceo en los vídeos (4.4 en adelante); tarda unos 0,8 s en dibujar un fotograma, así que se dibuja una vez y se reutiliza. Para la legibilidad: el título lleva trazo oscuro grueso, el mapa va con líneas doradas arriba y abajo (el «mar» fuera de Galicia sigue siendo azul marino) y el panel de datos es una tarjeta azul marino casi opaca. Los 420 px inferiores (zona de la interfaz de las redes) quedan solo con hierba.

## Paleta
| Uso | Color |
|---|---|
| Fondo | `#0B1730` azul marino oscuro |
| Panel inferior | `#13244D` |
| Dorado (título, línea divisoria, multiplicador, concellos en combate) | `#F5B82E` |
| Texto | `#FFFFFF`; secundario `#A9BAE0` |
| Ganador / perdedor | `#3DDC84` / `#FF5470` |
Los colores de cada concello son los de su bandera (paso 2.5; por ahora provisionales).

## Tipografía
**Lilita One** (SIL OFL 1.1, ver `docs/FUENTES.md`): negrita redondeada de estilo juego, como la del vídeo de referencia. Cubre ñ, tildes, ü, ¡, ¿ y ×. Tamaños: título 78 px, subtítulo 52, nombres 52–56, datos 46, marcador 70–96; **mínimo 44 px** para leerse bien en el móvil. Los nombres largos se parten en dos líneas.

## Elementos
- **Mapa con zoom en el enfrentamiento:** la cámara encuadra los **territorios completos** de los dos bandos (todos los concellos que posee cada uno) con un 20 % de aire alrededor. Así, si un bando es enorme, hace menos zoom y se ve entero; si son dos concellos pequeños, el zoom se detiene en un mínimo de 40 km de lado para ver el entorno. La ventana nunca recorta (`caja_de_zoom`). El mapa ocupa todo el ancho (y = 395–905).
- **Concellos en conflicto:** su silueta se marca con **contorno rojo** (`#FF2D55`) en el mapa; la línea dorada de 6 px separa mapa y panel.
- **Siluetas:** el concello con su forma real, relleno con el color de su dueño y borde blanco; debajo el nombre (hasta 2 líneas).
- **Todo lo relacionado con las vacas va «pintado de vaca»:** pastillas blancas con manchas negras (`pastilla_vaca`): el número de vacas de cada bando, la **diferencia real en % entero** entre ambos («dif. vacas +50%», en el centro) y el multiplicador «×1,5». Las manchas salen por los bordes y el texto lleva halo blanco para leerse bien; el texto se centra por su tinta real, no por su caja tipográfica.
- **Diferencia de vacas mostrada:** `(mayor − menor) / menor` redondeada al entero (`diferencia_porcentual`) y **con tope en 50** (decisión del usuario): si la diferencia real es mayor, se muestra simplemente «+50%».
- **Dados:** cara blanca con puntos oscuros; el borde dorado marca al bando que gana esa tirada. La puntuación va **a un lado** de los dados, separada, y el multiplicador debajo de los dados del bando con más vacas.
- **Textos:** todos en gallego (título, «Ep. N», «vacas», «dif. vacas», «PERDEDOR», «GAÑADOR», «Máis vitorias»…).

- **Nombres en el mapa (decisión del usuario, 2026-11-18):** el mapa general de Galicia **no lleva nombres** (hay 313 concellos y no se leerían). Solo se escriben nombres en las vistas con zoom y **solo los de los bandos en conflicto**. Los nombres son los del **dueño** (el territorio conquistado lleva el nombre del ganador). El panel usa el mismo criterio: nombre del dueño y silueta de todo su territorio.

- **Pantalla de enfrentamiento (4.3, `src/render/enfrentamiento.py`):** mapa con zoom y contornos rojos + panel con rótulo ATACA (rojo) / DEFENDE (blanco), silueta del territorio completo, nombre del dueño, «VS», y fila de pastillas de vaca (vacas de cada bando y dif. %). Los dados (4.4) aparecen debajo, en el hueco libre, reutilizando `fotograma_base`.

- **Fondo (2026-11-18):** foto real de hierba aportada por el usuario (`assets/img/hierba.avif`, ver `docs/FUENTES.md`), escalada para cubrir el fotograma y recortada centrada (`fondo_foto`). Sustituye a la hierba dibujada por código (`fondo_hierba`, que se conserva como alternativa y por su soporte de viento animado).

- **Colores claros (2026-11-18):** el mar del mapa es **azul cielo** (`#7CC6F0`) y el panel de datos es **blanco con grandes manchas negras de vaca** (`panel_vaca`, manchas en los bordes y centro libre). Los textos del panel van en **azul marino con halo blanco** (nombres, puntuaciones), «ATACA» en rojo, «DEFENDE» en azul (`#1B5FD6`) y «VS» en dorado con borde marino; las siluetas y los dados llevan borde marino. Las pastillas de vaca conservan su contorno marino para destacar sobre el panel.

- **Dados en vertical (2026-11-18):** cada bando tiene una **columna de 3 dados** (fila a fila, atacante a la izquierda y defensor a la derecha) para ver de qué dado sale cada punto. El dado que gana la tirada lleva **borde dorado** y, pegada a él por fuera, una insignia verde **«+N»** con los puntos ganados («=» gris en las dos si empatan). En el centro, el marcador «2 - 4» y, debajo del total del bando con más vacas, la pastilla del multiplicador. Para hacer sitio, el mapa baja a 440 px de alto (y = 395–835) y el panel empieza en y = 841.

## Animación de la batalla (4.4: `dados.py`, `marcador.py`, `animacion_batalla.py`)
Secuencia (tiempos en `animacion_batalla.py`): pantalla de enfrentamiento 0,8 s → **duelo: navaja de bolsillo gallega ABIERTA y recta, inclinada a la derecha (mango de madera, virola cónica, hoja de un solo filo), y botella «LIC. CAFÉ»** 1,7 s: entran girando desde los lados (0,55 s), la navaja golpea la botella con el filo con un destello dorado y un pequeño temblor, y debajo del choque aparece «LIORTA!» (dorado con borde oscuro, efecto pop); todo se desvanece (sustituyen a las espadas, decisión del usuario) → **3 tiradas** de 1,8 s (los dados de cada fila ruedan 0,9 s cambiando de cara y botando; al parar, el ganador de la tirada se agranda un poco, se resalta con borde dorado y le sale su «+N»; el marcador sube con un pequeño «pop») → **multiplicador** 1,6 s (pastilla de vaca «×1,5» con halo dorado bajo el bando con más vacas; los totales pasan a decimales, p. ej. «6,0 - 3,0») → **muerte súbita** si hay empate (tarjeta en llamas —degradado rojo→naranja y lenguas de fuego animadas— «MORTE SÚBITA» que cubre la zona de dados, con un par de dados grandes por ronda) → **recuadro dorado** en el total del ganador 1,5 s. Total: ≈10 s sin muerte súbita, ≈13 s con una ronda. `fotograma(base, r, t)` es una función pura del instante, así que cualquier fotograma se puede repetir; la pantalla base se dibuja una vez por batalla (el render completo de la muestra tarda ≈12 s por vídeo).

## Pendiente de las siguientes fases
Icono de espadas cruzadas (4.4), pantallas PERDEDOR/GAÑADOR (4.5), ranking y escenas (4.6).

## Conquista (paso 4.5)

`src/render/conquista.py`, 4,2 s. Pantalla de enfrentamiento con los rótulos cambiados a **«CAMPIÓN»** (dorado con borde oscuro, sobre el ganador) y **«MALOGRADO»** (gris, sobre el perdedor) a los 0,5 s, con un destello. El color del ganador se extiende por el mapa sobre el territorio del perdedor, concello a concello desde la frontera (1,8 s, hasta 24 pasos); al acabar, el territorio fusionado queda con contorno dorado y el nombre del ganador. A 1 s sale la **gaita gallega** (`dados.gaita_sprite`: la ilustración `assets/img/gaita.svg` aportada por el usuario: fol negro con flecos y borlas verdes, ronco, ronquillo, soprete y punteiro de boj) con rebote y balanceo, más un chorro de confeti (otro, menor, a 2 s). A 2 s salen las pastillas de vaca «+N vacas» y «+K concellos» junto al ganador. La gaita sustituye al icono de espada del vídeo de referencia; su música se añadirá en la fase 5.

## Vídeo completo del episodio (paso 4.6)

`src/render/escenas.py` monta el episodio con fundido cruzado de 0,2 s entre escenas:

1. **Intro** (2,0 s): título, «Ep. N» y el mapa general de Galicia, que entra con un fundido.
2. **Por cada batalla (×3):**
   - **Selección** (≈4,5 s): el mapa hace zoom hasta el atacante (contorno rojo y nombre); sale su silueta, «ATACA» y sus vacas; un sorteo recorre los concellos vecinos enemigos (cada vez más despacio, contorno dorado) hasta pararse en el defensor, que queda con contorno rojo y su nombre.
   - **Enfrentamiento, duelo (navaja y botella), dados, multiplicador y, si hace falta, morte súbita** (≈11 s sin desempate).
   - **Conquista** (4,2 s): CAMPIÓN / MALOGRADO, color que se extiende, gaita y confeti.
3. **Cierre** (`src/render/ranking.py`): mapa general con el estado actual y dos top 5: **«MÁIS VITORIAS»** (batallas gañadas, solo dueños con alguna) y **«MÁIS TERRITORIO»** (nº de concellos). Las filas salen de la 5ª a la 1ª con un «pop»; la 1ª va resaltada en dorado, y 2ª y 3ª en plata y bronce. Empates: por la otra magnitud y luego por nombre.
4. **Final de serie:** si en el episodio queda un único dueño, en vez del cierre sale «CAMPIÓN DE GALICIA» con su nombre, concellos, vacas y vitorias, la gaita y confeti.

**Duración:** la del cierre se ajusta (10–26 s) para que el vídeo dure ≈85 s (el requisito es 80–90 s); con muertes súbitas el cierre se acorta. Render de un episodio: ≈2 min 15 s (2.550 fotogramas), 9,7 MB sin audio.
