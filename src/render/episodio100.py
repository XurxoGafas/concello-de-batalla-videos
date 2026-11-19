"""Muestra de cómo sería el episodio 100 de una serie: 99 episodios ya jugados (297 batallas, quedan 16
dueños) y, encima, el episodio completo (portada, 3 batallas, cierre con ranking).

Uso: `python -m src.render.episodio100`  →  `output/muestras/episodio100_sin_audio.mp4`, `episodio100_portada.png`
y `episodio100_mapa_previo.png` (el mapa con el que empieza).
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from src.render import estilo as E
from src.render.escenas import construir_episodio, estado_de_muestra, renderizar
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"
SEMILLA = "muestra"
EPISODIO = 100
BATALLAS_POR_EPISODIO = 3


def generar(carpeta: Path = CARPETA) -> Path:
    t0 = time.time()
    mapa = MapaGalicia()
    previas = (EPISODIO - 1) * BATALLAS_POR_EPISODIO
    estado = estado_de_muestra(SEMILLA, previas=previas, episodio=EPISODIO - 1)
    print(f"Antes del episodio {EPISODIO}: {len(estado['donos'])} dueños", flush=True)
    carpeta.mkdir(parents=True, exist_ok=True)
    m = construir_episodio(estado, SEMILLA, mapa)
    print(f"Montaje listo: {len(m.escenas)} escenas, {m.duracion:.1f} s ({time.time() - t0:.0f} s)", flush=True)
    m.escenas[0].fotograma(0.0).save(carpeta / "episodio100_portada.png")
    m.escenas[1].fotograma(0.0).save(carpeta / "episodio100_mapa_previo.png")
    ruta = renderizar(m, carpeta / "episodio100_sin_audio.mp4", progreso=True)
    print(f"Render completo en {time.time() - t0:.0f} s", flush=True)
    return ruta


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA))
