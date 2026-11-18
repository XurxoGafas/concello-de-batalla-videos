"""Fotogramas de muestra estáticos para aprobar el estilo (paso 4.1).

Genera en `output/muestras/` tres fotogramas con datos reales (se simulan N batallas con una
semilla y se dibuja la siguiente, a mitad de tirada) para ver cómo se comporta el zoom:

Sobre un fondo de hierba (`fondo_hierba`).

- `estilo.png`: dos territorios medianos (4 concellos contra 4).
- `estilo_zoom_minimo.png`: dos concellos sueltos (el zoom no pasa de un mínimo).
- `estilo_zoom_grande.png`: territorios enormes (menos zoom, para que se vea todo).

Uso: `python -m src.render.muestra_estilo`
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import geopandas as gpd
from PIL import Image, ImageDraw

from src.motor.batalla import simular_batalla
from src.motor.estado import jugar_batalla
from src.motor.multiplicador import diferencia_porcentual
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import elegir_enfrentamiento
from src.render import estilo as E
from src.render.fondo import fondo_hierba

GEOJSON = E.RAIZ / "data" / "processed" / "concellos.geojson"
CARPETA = E.RAIZ / "output" / "muestras"
SUPERMUESTREO = 2  # el mapa se dibuja al doble y se reduce, para bordes suaves

# Zonas del fotograma (y en píxeles)
MAPA_Y0, MAPA_ALTO = 395, 510
LINEA_Y = MAPA_Y0 + MAPA_ALTO  # justo bajo el mapa
PANEL_FIN = E.ALTO - E.MARGEN_INF + 10


def _num(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _poligonos(geom):
    return list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]


def _pintar(d: ImageDraw.ImageDraw, geom, f, relleno, contorno, ancho=1):
    for poli in _poligonos(geom):
        d.polygon([f(*p) for p in poli.exterior.coords], fill=relleno, outline=contorno, width=ancho)


def _transformar(ventana, ancho_px: float, k: int):
    """Pasa coordenadas UTM a píxeles (×k) para que `ventana` ocupe `ancho_px` de ancho."""
    x0, y0, x1, y1 = ventana
    esc = ancho_px * k / (x1 - x0)
    return lambda x, y: ((x - x0) * esc, (y1 - y) * esc)


def _caja_silueta(gdf: gpd.GeoDataFrame, ancho: int, alto: int, k: int):
    """Transformación que encaja un concello en una caja (ancho×alto) dejando 10 px de aire."""
    minx, miny, maxx, maxy = gdf.total_bounds
    esc = min((ancho - 20) * k / (maxx - minx), (alto - 20) * k / (maxy - miny))
    ox = (ancho * k - (maxx - minx) * esc) / 2
    oy = (alto * k - (maxy - miny) * esc) / 2
    return lambda x, y: (ox + (x - minx) * esc, oy + (maxy - y) * esc)


def generar(ruta: Path, semilla: str = "muestra", previas: int = 106) -> Path:
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    rng = random.Random(semilla_de_batalla(semilla, previas + 1))
    f = elegir_enfrentamiento(estado, rng)
    va, vd = estado["donos"][f.atacante]["vacas"], estado["donos"][f.defensor]["vacas"]
    r = simular_batalla(va, vd, rng=rng)

    gdf = gpd.read_file(GEOJSON).to_crs(25829).set_index("id")
    k, W, H = SUPERMUESTREO, E.ANCHO, E.ALTO
    img = fondo_hierba(W, H)
    d = ImageDraw.Draw(img)

    # --- Título (dentro de la zona segura) ---
    E.texto_centrado(d, W / 2, 232, "CONCELLO DE BATALLA", E.T_TITULO, E.ORO, borde=9)
    E.texto_centrado(d, W / 2, 318, "Ep. 27", E.T_SUBTITULO, E.BLANCO, borde=7)

    # --- Mapa con zoom: encuadra los territorios completos de los dos bandos ---
    ids_bando = estado["donos"][f.atacante]["territorio"] + estado["donos"][f.defensor]["territorio"]
    ventana = E.caja_de_zoom(tuple(gdf.loc[ids_bando].total_bounds), W / MAPA_ALTO)
    mapa = Image.new("RGB", (W * k, MAPA_ALTO * k), E.FONDO)
    dm = ImageDraw.Draw(mapa)
    fm = _transformar(ventana, W, k)
    for i, fila in gdf.iterrows():
        dono = estado["concellos"][i]["dono"]
        _pintar(dm, fila.geometry, fm, estado["donos"][dono]["cor"]["colores"][0],
                E.CONTORNO_MAPA, k)
    for i in (f.concello_atacante, f.concello_defensor):  # siluetas en conflicto, en rojo
        _pintar(dm, gdf.loc[i].geometry, fm, None, E.CONFLICTO, 6 * k)
    img.paste(mapa.resize((W, MAPA_ALTO), Image.LANCZOS), (0, MAPA_Y0))

    # --- Línea dorada y panel inferior ---
    d.rectangle((0, MAPA_Y0 - 6, W, MAPA_Y0 - 1), fill=E.ORO)
    d.rectangle((0, LINEA_Y, W, LINEA_Y + 6), fill=E.ORO)
    panel = Image.new("RGB", (W, PANEL_FIN - LINEA_Y - 6), E.PANEL)  # tarjeta algo translúcida
    mezcla = Image.blend(img.crop((0, LINEA_Y + 6, W, PANEL_FIN)), panel, 0.93)
    img.paste(mezcla, (0, LINEA_Y + 6))
    d.rectangle((0, PANEL_FIN, W, PANEL_FIN + 4), fill=E.FONDO)

    cx_a, cx_d, cx_c = 270, 690, W / 2

    # --- Siluetas y nombres ---
    for concello, dono, cx in ((f.concello_atacante, f.atacante, cx_a),
                               (f.concello_defensor, f.defensor, cx_d)):
        g1 = gdf.loc[[concello]]
        sil = Image.new("RGBA", (300 * k, 150 * k), (255, 255, 255, 0))  # fondo transparente
        _pintar(ImageDraw.Draw(sil), g1.iloc[0].geometry, _caja_silueta(g1, 300, 150, k),
                estado["donos"][dono]["cor"]["colores"][0], E.BLANCO, 3 * k)
        sil = sil.resize((300, 150), Image.LANCZOS)
        img.paste(sil.convert("RGB"), (int(cx - 150), 930), sil.getchannel("A"))
        lineas, t = E.dividir_nombre(estado["concellos"][concello]["nome"], 52, 410)
        for n, linea in enumerate(lineas):
            E.texto_centrado(d, cx, 1088 + n * (t + 2), linea, t, E.BLANCO)
    E.texto_centrado(d, cx_c, 985, "VS", 64, E.ORO, borde=3)

    # --- Fila de vacas: cada bando, y entre ambos la diferencia en % (todo «pintado de vaca») ---
    cy_vacas = 1250
    dif = diferencia_porcentual(va, vd)
    lineas_dif = ["dif. vacas", f"+{_num(dif)}%" if dif else "0%"]
    wd, _ = E.tamano_pastilla(lineas_dif, E.T_MIN, 20)
    for vacas, cx_col, lado in ((va, cx_a, -1), (vd, cx_d, 1)):
        txt = f"{_num(vacas)} vacas"
        w, _ = E.tamano_pastilla(txt, E.T_MIN, 20)
        # que no invada el hueco central de la pastilla de la diferencia
        cx = min(cx_col, cx_c - wd / 2 - 12 - w / 2) if lado < 0 else max(cx_col, cx_c + wd / 2 + 12 + w / 2)
        E.pastilla_vaca(img, cx, cy_vacas, txt, E.T_MIN, 20)
    E.pastilla_vaca(img, cx_c, cy_vacas, lineas_dif, E.T_MIN, 20)

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
        E.texto_centrado_exacto(d, x0 + ancho_dados + 52, y_dados + lado / 2, f"{pts}", 76, E.BLANCO)
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
