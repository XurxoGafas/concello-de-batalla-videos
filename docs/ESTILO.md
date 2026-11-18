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

## Pendiente de las siguientes fases
Icono de espadas cruzadas (4.4), pantallas PERDEDOR/GAÑADOR (4.5), ranking y escenas (4.6).
