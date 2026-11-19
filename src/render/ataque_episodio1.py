"""Animación corta del episodio 1: un solo ataque sobre el mapa con Ordes ocupando 1/3 de Galicia.

Intro con el mapa → sorteo de atacante y defensor → batalla → conquista → alejamiento. Sin portada ni
ranking. La semilla (`SEMILLA`) se elige para que Ordes participe en el ataque (es una muestra); la
batalla sale de la mecánica normal (semilla de batalla derivada, reproducible).

Uso: `python -m src.render.ataque_episodio1`  →  `output/muestras/ataque_episodio1.mp4`
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from src.motor.persistencia import jugar_episodio_detallado
from src.render import estilo as E
from src.render.escenas import construir_ataque, renderizar
from src.render.mapa import MapaGalicia
from src.render.mapa_episodio1 import estado_episodio1

CARPETA = E.RAIZ / "output" / "muestras"


def elegir_semilla(estado: dict, dueno_id: str, maximo: int = 400) -> str:
    """Primera semilla `ataque1-N` en la que `dueno_id` es atacante o defensor del único ataque."""
    for n in range(maximo):
        semilla = f"ataque1-{n}"
        _, _, pasos = jugar_episodio_detallado(estado, semilla, n_batallas=1)
        f = pasos[0][1].enfrentamiento
        if dueno_id in (f.atacante, f.defensor):
            return semilla
    raise RuntimeError("Ninguna semilla hace participar a ese dueño")


def generar(carpeta: Path = CARPETA) -> Path:
    t0 = time.time()
    mapa = MapaGalicia()
    estado = estado_episodio1(mapa)
    ordes = next(i for i, c in estado["concellos"].items() if c["nome"] == "Ordes")
    semilla = elegir_semilla(estado, ordes)
    m = construir_ataque(estado, semilla, mapa)
    ep = jugar_episodio_detallado(estado, semilla, n_batallas=1)[2][0][1]
    f = ep.enfrentamiento
    print(f"Semilla {semilla}: ataca {estado['donos'][f.atacante]['nome']} a {estado['donos'][f.defensor]['nome']}; "
          f"gana {estado['donos'][ep.ganador]['nome']}. Montaje {m.duracion:.1f} s ({time.time() - t0:.0f} s de preparación)", flush=True)
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = renderizar(m, carpeta / "ataque_episodio1.mp4", progreso=True)
    print(f"Render completo en {time.time() - t0:.0f} s", flush=True)
    return ruta


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA))
