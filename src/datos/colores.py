"""Colores de las banderas de los concellos (paso 2.4).

Para cada bandera (imagen) calcula una **paleta**: hasta 4 colores con su peso (proporción de
superficie). El primero es el color principal (el de mayor superficie). La paleta permite
rellenar el territorio con un color liso o, más adelante, con rayas o un patrón.

Las imágenes se bajan con `scripts/descargar_banderas.py` a `data/raw/banderas/<ine>.<ext>`.
Los SVG se rasterizan con `rsvg-convert` (solo hace falta al preparar los datos; el resultado,
`data/processed/colores_bandera.json`, ya va en el repositorio).

Uso:
    python -m src.datos.colores
"""

from __future__ import annotations

import io
import json
import shutil
import subprocess
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parents[2]
CARPETA = RAIZ / "data" / "raw" / "banderas"
LISTA = RAIZ / "data" / "raw" / "banderas_wikidata.json"
CONCELLOS = RAIZ / "data" / "processed" / "concellos.geojson"
SALIDA = RAIZ / "data" / "processed" / "colores_bandera.json"

ANCHO = 240  # ancho al que se reduce/rasteriza la imagen para contar píxeles
N_CUANTIZAR = 12  # colores iniciales antes de fusionar los parecidos
DIST_FUSION = 48  # distancia RGB por debajo de la cual dos colores se consideran el mismo
PESO_MINIMO = 0.04  # colores con menos del 4 % de superficie se descartan
MAX_COLORES = 4


def abrir_imagen(ruta: Path) -> Image.Image:
    """Abre una imagen (rasterizando los SVG) y la devuelve en modo RGBA."""
    if ruta.suffix.lower() == ".svg":
        exe = shutil.which("rsvg-convert")
        if not exe:
            raise RuntimeError("Hace falta rsvg-convert (librsvg2-bin) para leer SVG")
        png = subprocess.run(
            [exe, "-w", str(ANCHO), "-f", "png", str(ruta)],
            check=True,
            capture_output=True,
        ).stdout
        return Image.open(io.BytesIO(png)).convert("RGBA")
    im = Image.open(ruta).convert("RGBA")
    if im.width > ANCHO:
        im = im.resize((ANCHO, max(1, round(im.height * ANCHO / im.width))), Image.LANCZOS)
    return im


def _distancia(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return sum((x - y) ** 2 for x, y in zip(a, b)) ** 0.5


def paleta(im: Image.Image) -> list[tuple[str, float]]:
    """Devuelve [(color hex, peso)] ordenado por peso, con los pesos sumando 1.

    Se ignoran los píxeles transparentes. Los colores parecidos se fusionan (el antialiasing
    y los degradados generan muchos tonos intermedios) y se descartan los casi inexistentes.
    """
    im = im.convert("RGBA")
    # Pillow ≥ 13 renombra getdata() a get_flattened_data()
    datos = getattr(im, "get_flattened_data", im.getdata)()
    opacos = [p[:3] for p in datos if p[3] >= 128]
    if not opacos:
        raise ValueError("La imagen no tiene píxeles opacos")
    rgb = Image.new("RGB", (len(opacos), 1))
    rgb.putdata(opacos)
    q = rgb.quantize(colors=N_CUANTIZAR, method=Image.Quantize.MEDIANCUT)
    pal = q.getpalette()
    cuentas = sorted(q.getcolors(), reverse=True)  # [(n, índice)]
    colores: list[list] = []  # [rgb, n]
    for n, idx in cuentas:
        c = tuple(pal[3 * idx : 3 * idx + 3])
        for g in colores:
            if _distancia(c, g[0]) < DIST_FUSION:
                g[1] += n  # se suma al grupo; el color del grupo es el de mayor peso
                break
        else:
            colores.append([c, n])
    total = sum(g[1] for g in colores)
    util = [(c, n / total) for c, n in colores if n / total >= PESO_MINIMO]
    util.sort(key=lambda t: -t[1])
    util = util[:MAX_COLORES]
    suma = sum(p for _, p in util)
    return [("#%02x%02x%02x" % c, round(p / suma, 4)) for c, p in util]


def construir(ids: list[str], nombres: dict[str, str]) -> dict:
    """Paleta por id de concello (los 5 últimos dígitos del id son el código INE)."""
    lista = json.loads(LISTA.read_text(encoding="utf-8")) if LISTA.exists() else {}
    colores: dict[str, dict] = {}
    for i in ids:
        ine = i[-5:]
        archivos = sorted(CARPETA.glob(f"{ine}.*"))
        if not archivos:
            continue
        pal = paleta(abrir_imagen(archivos[0]))
        colores[i] = {
            "nome": nombres[i],
            "colores": [c for c, _ in pal],
            "pesos": [p for _, p in pal],
            "origen": f"Wikidata P41 · {lista.get(ine, {}).get('imagen', '')}",
        }
    return colores


def main() -> None:
    g = json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"]
    nombres = {f["properties"]["id"]: f["properties"]["nome"] for f in g}
    colores = construir(sorted(nombres), nombres)
    SALIDA.write_text(
        json.dumps(
            {"con_bandera": colores, "sin_bandera": sorted(set(nombres) - set(colores))},
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"{len(colores)} concellos con paleta de bandera, {len(nombres) - len(colores)} sin ella")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
