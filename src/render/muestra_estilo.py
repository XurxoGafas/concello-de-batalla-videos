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
from src.render.enfrentamiento import CARPETA, fotograma_base
from src.render import marcador as M
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

    # --- Dados en vertical: una columna por bando, fila a fila, para ver de dónde sale cada punto ---
    lado, sep, y0 = 80, 10, 1222
    for i, t in enumerate(r.tiradas):
        y = y0 + i * (lado + sep)
        for cx, dado, ganado, fuera in ((235, t.dado_a, t.puntos_a, -1), (E.ANCHO - 235, t.dado_b, t.puntos_b, 1)):
            E.dibujar_dado(d, cx - lado / 2, y, lado, dado, resaltado=ganado > 0)
            # los puntos ganados salen pegados al dado que los gana (por fuera); «=» si empatan
            txt, color = (f"+{ganado}", E.VERDE_PUNTOS) if ganado > 0 else ("=" if t.puntos_a == t.puntos_b else "", E.GRIS_EMPATE)
            if txt:
                w = max(76, int(E.ancho_texto(txt, 50)) + 30)
                bx = cx + fuera * (lado / 2 + 14 + w / 2)
                d.rounded_rectangle((bx - w / 2, y + lado / 2 - 30, bx + w / 2, y + lado / 2 + 30), radius=30,
                                    fill=color, outline=E.FONDO, width=4)
                E.texto_centrado_exacto(d, bx, y + lado / 2, txt, 50, E.BLANCO)
    # --- Marcador total en el centro y multiplicador bajo el bando con más vacas ---
    ym = y0 + (3 * lado + 2 * sep) / 2
    for cx, pts, mult in ((M.X_A, r.puntos_a, r.mult_a), (M.X_D, r.puntos_b, r.mult_b)):
        E.texto_centrado_exacto(d, cx, ym - 25, f"{pts}", 100, E.FONDO, borde=8, color_borde=E.BLANCO)
        if mult > 1:
            E.pastilla_vaca(img, cx, ym + 60, f"×{str(mult).replace('.', ',')}", 46, 26)
    E.texto_centrado_exacto(d, E.ANCHO / 2, ym - 25, "-", 80, E.FONDO, borde=8, color_borde=E.BLANCO)

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
