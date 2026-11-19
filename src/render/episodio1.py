"""Episodio 1 completo, con sonido: portada, intro, 3 batallas con su conquista y cierre con rankings,
sobre el mapa del episodio 1 (Ordes con ≈1/3 de Galicia).

La semilla `ep1-N` se elige para que Ordes participe en alguna de las 3 batallas (es una muestra).
Uso: `python -m src.render.episodio1`  →  `output/muestras/episodio1_con_audio.mp4` (y la portada PNG)
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from src.audio.mezcla import medir_lufs, poner_audio
from src.motor.persistencia import jugar_episodio_detallado
from src.render import estilo as E
from src.render.escenas import construir_episodio, renderizar
from src.render.mapa import MapaGalicia
from src.render.mapa_episodio1 import estado_episodio1

CARPETA = E.RAIZ / "output" / "muestras"


def elegir_semilla(estado: dict, dueno_id: str, maximo: int = 200) -> str:
    """Primera semilla `ep1-N` en la que `dueno_id` participa en alguna de las 3 batallas."""
    for n in range(maximo):
        semilla = f"ep1-{n}"
        _, _, pasos = jugar_episodio_detallado(estado, semilla)
        if any(dueno_id in (ep.enfrentamiento.atacante, ep.enfrentamiento.defensor) for _, ep in pasos):
            return semilla
    raise RuntimeError("Ninguna semilla hace participar a ese dueño")


def generar(carpeta: Path = CARPETA) -> Path:
    t0 = time.time()
    mapa = MapaGalicia()
    estado = estado_episodio1(mapa)
    ordes = next(i for i, c in estado["concellos"].items() if c["nome"] == "Ordes")
    semilla = elegir_semilla(estado, ordes)
    m = construir_episodio(estado, semilla, mapa)
    print(f"Semilla {semilla}; episodio {estado.get('episodio')}; montaje {m.duracion:.1f} s, {len(m.escenas)} escenas "
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
