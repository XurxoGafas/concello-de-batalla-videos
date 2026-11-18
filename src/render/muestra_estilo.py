"""Fotograma de muestra estático para aprobar el estilo (paso 4.1).

Genera `output/muestras/estilo.png` (1080×1920) con una batalla a mitad de tirada, con datos
reales: se simulan 120 batallas con la semilla indicada y se dibuja la siguiente.
Uso: `python -m src.render.muestra_estilo`
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import geopandas as gpd
from PIL import Image, ImageDraw

from src.motor.estado import jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import elegir_enfrentamiento
from src.motor.batalla import simular_batalla
from src.render import estilo as E

GEOJSON = E.RAIZ / "data" / "processed" / "concellos.geojson"
SALIDA = E.RAIZ / "output" / "muestras" / "estilo.png"
SUPERMUESTREO = 2  # se dibuja el mapa al doble y se reduce, para bordes suaves


def _num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _transformar(gdf: gpd.GeoDataFrame, caja: tuple[float, float, float, float], k: int):
    """Devuelve una función que pasa coordenadas UTM a píxeles dentro de `caja` (x0,y0,x1,y1)."""
    minx, miny, maxx, maxy = gdf.total_bounds
    x0, y0, x1, y1 = (v * k for v in caja)
    esc = min((x1 - x0) / (maxx - minx), (y1 - y0) / (maxy - miny))
    ox = x0 + ((x1 - x0) - (maxx - minx) * esc) / 2
    oy = y0 + ((y1 - y0) - (maxy - miny) * esc) / 2
    return lambda x, y: (ox + (x - minx) * esc, oy + (maxy - y) * esc)


def _poligonos(geom):
    return list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]


def _pintar(d: ImageDraw.ImageDraw, geom, f, relleno, contorno, ancho=1):
    for poli in _poligonos(geom):
        d.polygon([f(*p) for p in poli.exterior.coords], fill=relleno, outline=contorno,
                  width=ancho)


def generar(ruta: Path = SALIDA, semilla: str = "muestra", previas: int = 120) -> Path:
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    rng = random.Random(semilla_de_batalla(semilla, previas + 1))
    f = elegir_enfrentamiento(estado, rng)
    va, vd = estado["donos"][f.atacante]["vacas"], estado["donos"][f.defensor]["vacas"]
    r = simular_batalla(va, vd, rng=rng)

    gdf = gpd.read_file(GEOJSON).to_crs(25829).set_index("id")
    k = SUPERMUESTREO
    W, H = E.ANCHO, E.ALTO
    img = Image.new("RGB", (W, H), E.FONDO)
    d = ImageDraw.Draw(img)

    # --- Título (dentro de la zona segura) ---
    E.texto_centrado(d, W / 2, 232, "CONCELLO DE BATALLA", E.T_TITULO, E.ORO)
    E.texto_centrado(d, W / 2, 318, "Ep. 27", E.T_SUBTITULO, E.GRIS_AZUL)

    # --- Mapa (supermuestreado) ---
    caja_mapa = (E.MARGEN_IZQ, 395, W - E.MARGEN_DER + 40, 905)
    mapa = Image.new("RGB", (W * k, 560 * k), E.FONDO)
    dm = ImageDraw.Draw(mapa)
    f_mapa = _transformar(gdf, (caja_mapa[0], 0, caja_mapa[2], 510), k)
    en_juego = {f.concello_atacante, f.concello_defensor}
    for i, fila in gdf.iterrows():
        dono = estado["concellos"][i]["dono"]
        _pintar(dm, fila.geometry, f_mapa, estado["donos"][dono]["cor"]["colores"][0],
                E.CONTORNO_MAPA, k)
    for i in en_juego:
        _pintar(dm, gdf.loc[i].geometry, f_mapa, None, E.ORO, 4 * k)
    img.paste(mapa.resize((W, 560), Image.LANCZOS).crop((0, 0, W, 510)), (0, 395))

    # --- Línea dorada y panel inferior ---
    d.rectangle((0, 915, W, 921), fill=E.ORO)
    d.rectangle((0, 921, W, E.ALTO - E.MARGEN_INF + 10), fill=E.PANEL)

    # --- Siluetas, nombres y vacas ---
    def bando(concello, dono, cx, vacas):
        sil = Image.new("RGB", (300 * k, 200 * k), E.PANEL)
        ds = ImageDraw.Draw(sil)
        g1 = gdf.loc[[concello]]
        fs = _transformar(g1, (10, 8, 290, 192), k)
        col = estado["donos"][dono]["cor"]["colores"][0]
        _pintar(ds, g1.iloc[0].geometry, fs, col, E.BLANCO, 3 * k)
        img.paste(sil.resize((300, 200), Image.LANCZOS), (int(cx - 150), 932))
        lineas, t = E.dividir_nombre(estado["concellos"][concello]["nome"], 52, 410)
        for n, linea in enumerate(lineas):
            E.texto_centrado(d, cx, 1142 + n * (t + 2), linea, t, E.BLANCO)
        E.texto_centrado(d, cx, 1262, f"{_num(vacas)} vacas", E.T_DATO, E.GRIS_AZUL)

    cx_a, cx_d = 270, 690
    bando(f.concello_atacante, f.atacante, cx_a, va)
    bando(f.concello_defensor, f.defensor, cx_d, vd)
    E.texto_centrado(d, (cx_a + cx_d) / 2, 1000, "VS", 72, E.ORO, borde=3)

    # --- Dados: las tres tiradas; el borde dorado marca quién gana cada una ---
    lado = 92
    for i, t in enumerate(r.tiradas):
        xa = cx_a - 150 + i * (lado + 12)
        xd = cx_d - 150 + i * (lado + 12)
        E.dibujar_dado(d, xa, 1328, lado, t.dado_a, resaltado=t.puntos_a > 0)
        E.dibujar_dado(d, xd, 1328, lado, t.dado_b, resaltado=t.puntos_b > 0)

    # --- Marcador y multiplicador (insignia dorada junto a la puntuación del bando con más vacas) ---
    for cx, pts, mult in ((cx_a, r.puntos_a, r.mult_a), (cx_d, r.puntos_b, r.mult_b)):
        E.texto_centrado(d, cx - (40 if mult > 1 else 0), 1428, f"{pts}", 70, E.BLANCO)
        if mult > 1:
            txt = f"×{str(mult).replace('.', ',')}"
            w = E.ancho_texto(txt, 54) + 36
            x0 = cx + 10
            d.rounded_rectangle((x0, 1434, x0 + w, 1434 + 64), radius=24, fill=E.ORO)
            E.texto_centrado(d, x0 + w / 2, 1437, txt, 54, E.FONDO)

    ruta.parent.mkdir(parents=True, exist_ok=True)
    img.save(ruta)
    return ruta


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else SALIDA))
