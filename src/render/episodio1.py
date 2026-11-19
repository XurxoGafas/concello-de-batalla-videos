"""Episodio 1 completo, con sonido: portada, intro, 3 batallas con su conquista y cierre con rankings.

Parte de la partida nueva: los 313 concellos aparecen, cada uno con su dueño y su símbolo, sin ningún
concello gigante (el mapa con Ordes en 1/3 era solo una muestra gráfica, `mapa_episodio1.py`).
Uso: `python -m src.render.episodio1`  →  `output/muestras/episodio1_con_audio.mp4` (y la portada PNG)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from src.audio.mezcla import medir_lufs, poner_audio
from src.motor.persistencia import nueva_partida
from src.render import estilo as E
from src.render.escenas import construir_episodio, renderizar
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"


SEMILLA = "ep1-0"


def generar(carpeta: Path = CARPETA) -> Path:
    t0 = time.time()
    mapa = MapaGalicia()
    estado = nueva_partida()
    m = construir_episodio(estado, SEMILLA, mapa)
    print(f"Semilla {SEMILLA}; {len(estado['donos'])} dueños; montaje {m.duracion:.1f} s, {len(m.escenas)} escenas "
          f"({time.time() - t0:.0f} s)", flush=True)
    carpeta.mkdir(parents=True, exist_ok=True)
    m.escenas[0].fotograma(0.0).save(carpeta / "episodio1_portada.png")
    sin = renderizar(m, carpeta / "episodio1_sin_audio.mp4", progreso=True)
    print(f"Vídeo renderizado ({time.time() - t0:.0f} s); mezclando audio", flush=True)
    con = poner_audio(m, sin, carpeta / "episodio1_con_audio.mp4")
    print(con, medir_lufs(con), flush=True)
    return con


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA))
