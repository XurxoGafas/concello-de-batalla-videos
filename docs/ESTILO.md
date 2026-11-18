# ESTILO — Guía visual de «Concello de Batalla»

Todas las constantes están en `src/render/estilo.py`. Fotograma de muestra: `python -m src.render.muestra_estilo` → `output/muestras/estilo.png` (con datos reales: 120 batallas simuladas y la siguiente a mitad de tirada).

## Formato
- **1080×1920 (9:16) a 30 fps.** 30 fps es lo que usa el vídeo de referencia, rinde bien para redes y renderizar a 60 fps duplicaría el tiempo en GitHub Actions sin ganar nada visible en este tipo de animación.

## Zonas seguras
La interfaz de TikTok, Reels y Shorts tapa los bordes. Todo el texto importante queda dentro de: **60 px a la izquierda, 140 a la derecha (botones), 220 arriba y 420 abajo (descripción, cuenta, música).** Son valores prudentes que sirven para las tres redes; se comprobarán con un vídeo real subido como borrador en el paso 6.3.

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
- **Mapa:** concellos rellenos con el color del dueño, borde fino azul oscuro; los dos concellos en combate se resaltan con contorno dorado. Debajo, línea dorada de 6 px que separa mapa y panel.
- **Siluetas:** el concello dibujado con su forma real, relleno con el color de su dueño y borde blanco; nombre debajo (hasta 2 líneas) y número de vacas.
- **Dados:** cara blanca con puntos oscuros y esquinas redondeadas; el borde dorado marca al bando que gana esa tirada.
- **Multiplicador:** insignia dorada «×1,5» junto a la puntuación del bando con más vacas.
- **Textos:** todos en gallego (título, «Ep. N», «vacas», «PERDEDOR», «GAÑADOR», «Máis vitorias»…).

## Pendiente de las siguientes fases
Icono de espadas cruzadas (4.4), pantallas PERDEDOR/GAÑADOR (4.5), ranking y escenas (4.6).
