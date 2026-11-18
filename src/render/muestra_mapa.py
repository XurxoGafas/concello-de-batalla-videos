"""Fotogramas de muestra del mapa (paso 4.2): mapa inicial y zoom al atacante.

- `output/muestras/mapa_inicial.png`: toda Galicia, un dueño por concello, sin nombres.
- `output/muestras/mapa_zoom_atacante.png`: fase 2, zoom sobre el atacante (solo su nombre en el mapa) con
  todos los vecinos enemigos visibles y, debajo, su nombre y sus vacas.

Uso: `python -m src.render.muestra_mapa`
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from src.motor.estado import jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import elegir_atacante
from src.render import estilo as E
from src.render.fondo import fondo_foto
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"
MAPA_Y0 = 395


def _base(episodio: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = fondo_foto(E.ANCHO, E.ALTO)
    d = ImageDraw.Draw(img)
    E.texto_centrado(d, E.ANCHO / 2, 232, "CONCELLO DE BATALLA", E.T_TITULO, E.ORO, borde=9)
    E.texto_centrado(d, E.ANCHO / 2, 318, f"Ep. {episodio}", E.T_SUBTITULO, E.BLANCO, borde=7)
    return img, d


def _num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def mapa_inicial(mapa: MapaGalicia, ruta: Path) -> Path:
    estado = nueva_partida()
    alto = E.ALTO - E.MARGEN_INF - MAPA_Y0 - 6  # hasta el borde de la zona segura
    img, d = _base(estado["episodio"] + 1)
    banda = mapa.dibujar(estado, mapa.ventana_general(E.ANCHO / alto), E.ANCHO, alto)
    img.paste(banda, (0, MAPA_Y0))
    d.rectangle((0, MAPA_Y0 - 6, E.ANCHO, MAPA_Y0 - 1), fill=E.ORO)
    d.rectangle((0, MAPA_Y0 + alto, E.ANCHO, MAPA_Y0 + alto + 5), fill=E.ORO)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta)
    return ruta


def mapa_zoom_atacante(mapa: MapaGalicia, ruta: Path, semilla: str = "muestra", previas: int = 106) -> Path:
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    atacante = elegir_atacante(estado, random.Random(semilla_de_batalla(semilla, previas + 1)))
    ids = estado["donos"][atacante]["territorio"]

    alto_mapa = 735
    img, d = _base(estado["episodio"] + 1)
    banda = mapa.dibujar(
        estado, mapa.ventana_atacante(estado, atacante, E.ANCHO / alto_mapa), E.ANCHO, alto_mapa,
        contornos=[(mapa.geometria(ids), E.ORO, 7)], nombres=[atacante],
    )
    img.paste(banda, (0, MAPA_Y0))
    y_linea = MAPA_Y0 + alto_mapa
    d.rectangle((0, MAPA_Y0 - 6, E.ANCHO, MAPA_Y0 - 1), fill=E.ORO)
    d.rectangle((0, y_linea, E.ANCHO, y_linea + 5), fill=E.ORO)
    fin = E.ALTO - E.MARGEN_INF + 10
    E.pegar_panel(img, y_linea + 5, fin)
    d.rectangle((0, fin, E.ANCHO, fin + 4), fill=E.FONDO)

    E.texto_centrado(d, E.ANCHO / 2, y_linea + 28, "ATACA", E.T_SUBTITULO, E.CONFLICTO, borde=7, color_borde=E.BLANCO)
    nombre = estado["donos"][atacante]["nome"]
    lineas, t = E.dividir_nombre(nombre, 84, E.ANCHO - E.MARGEN_IZQ - E.MARGEN_DER)
    for n, linea in enumerate(lineas):
        E.texto_centrado(d, E.ANCHO / 2, y_linea + 95 + n * (t + 4), linea, t, E.FONDO, borde=7, color_borde=E.BLANCO)
    y_vacas = y_linea + 95 + len(lineas) * (t + 4) + 55
    E.pastilla_vaca(img, E.ANCHO / 2, y_vacas, f"{_num(estado['donos'][atacante]['vacas'])} {E.ICONO_VACA}", 52, 28)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta)
    return ruta


if __name__ == "__main__":
    carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA
    m = MapaGalicia()
    print(mapa_inicial(m, carpeta / "mapa_inicial.png"))
    print(mapa_zoom_atacante(m, carpeta / "mapa_zoom_atacante.png"))
