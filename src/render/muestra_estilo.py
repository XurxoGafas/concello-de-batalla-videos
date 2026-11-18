"""Fotogramas de muestra estáticos para aprobar el estilo (paso 4.1).

Genera en `output/muestras/` tres fotogramas con datos reales (se simulan N batallas con una
semilla y se dibuja la siguiente, a mitad de tirada) para ver cómo se comporta el zoom:

Sobre la foto de hierba (`fondo_foto`).

- `estilo.png`: dos territorios medianos (4 concellos contra 4).
- `estilo_zoom_minimo.png`: dos concellos sueltos (el zoom no pasa de un mínimo).
- `estilo_zoom_grande.png`: territorios enormes (menos zoom, para que se vea todo).

Uso: `python -m src.render.muestra_estilo`
"""

from __future__ import annotations

import random
import sys
from pathlib import Path


from src.motor.batalla import simular_batalla
from src.motor.estado import jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import elegir_enfrentamiento
from src.render import estilo as E
from src.render.enfrentamiento import CARPETA, CX_A, CX_D, fotograma_base
from src.render.mapa import MapaGalicia

def generar(ruta: Path, semilla: str = "muestra", previas: int = 106) -> Path:
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    rng = random.Random(semilla_de_batalla(semilla, previas + 1))
    f = elegir_enfrentamiento(estado, rng)
    va, vd = estado["donos"][f.atacante]["vacas"], estado["donos"][f.defensor]["vacas"]
    r = simular_batalla(va, vd, rng=rng)

    # Todo lo común con la pantalla de enfrentamiento (4.3) viene de `fotograma_base`
    img, d = fotograma_base(estado, f, MapaGalicia(), 27)
    cx_a, cx_d = CX_A, CX_D

    # --- Dados (el borde dorado marca quién gana la tirada) y la puntuación, separada a un lado ---
    lado, sep = 88, 10
    y_dados = 1322
    for cx, dados_pts, pts, mult in (
        (cx_a, [(t.dado_a, t.puntos_a) for t in r.tiradas], r.puntos_a, r.mult_a),
        (cx_d, [(t.dado_b, t.puntos_b) for t in r.tiradas], r.puntos_b, r.mult_b),
    ):
        ancho_dados = 3 * lado + 2 * sep
        x0 = cx - ancho_dados / 2 - 20
        for i, (dado, ganado) in enumerate(dados_pts):
            E.dibujar_dado(d, x0 + i * (lado + sep), y_dados, lado, dado, resaltado=ganado > 0)
        E.texto_centrado_exacto(d, x0 + ancho_dados + 52, y_dados + lado / 2, f"{pts}", 76, E.FONDO, borde=7, color_borde=E.BLANCO)
        if mult > 1:  # multiplicador: pastilla de vaca bajo los dados del bando con más vacas
            E.pastilla_vaca(img, x0 + ancho_dados / 2, 1460, f"×{str(mult).replace('.', ',')}", 46, 26)

    CARPETA.mkdir(parents=True, exist_ok=True)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta)
    return ruta


MUESTRAS = (
    ("estilo.png", 106),  # 4 concellos contra 4
    ("estilo_zoom_minimo.png", 12),  # 1 contra 1
    ("estilo_zoom_grande.png", 278),  # 36 contra 22: menos zoom
)

if __name__ == "__main__":
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA
    for nombre, previas in MUESTRAS:
        print(generar(carpeta / nombre, previas=previas))
