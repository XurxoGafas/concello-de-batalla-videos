"""Tests del mapa del episodio 1 (Ordes con ≈1/3 del territorio) y del dibujo de territorios unidos."""

from __future__ import annotations

import copy

import pytest

from src.render import estilo as E
from src.render.mapa import MapaGalicia
from src.render.mapa_episodio1 import FRACCION, estado_episodio1, tabla


@pytest.fixture(scope="module")
def mapa():
    return MapaGalicia()


@pytest.fixture(scope="module")
def estado(mapa):
    return estado_episodio1(mapa)


def _ordes(estado):
    return next(i for i, c in estado["concellos"].items() if c["nome"] == "Ordes")


def test_ordes_ocupa_un_tercio(mapa, estado):
    o = _ordes(estado)
    sup = mapa.geometria(estado["donos"][o]["territorio"]).area / mapa.gdf.geometry.area.sum()
    assert abs(sup - FRACCION) < 0.01
    assert o in estado["donos"] and estado["donos"][o]["victorias"] == 0


def test_resto_sin_cambios_y_vacas_conservadas(estado):
    o = _ordes(estado)
    otros = [d for d in estado["donos"] if d != o]
    assert all(estado["donos"][d]["territorio"] == [d] for d in otros)
    assert sum(d["vacas"] for d in estado["donos"].values()) == sum(c["vacas"] for c in estado["concellos"].values())


def test_territorio_es_contiguo(mapa, estado):
    t = estado["donos"][_ordes(estado)]["territorio"]
    assert len(t) > 1
    vistos, pend = {t[0]}, [t[0]]
    while pend:
        for v in estado["concellos"][pend.pop()]["vecinos"]:
            if v in t and v not in vistos:
                vistos.add(v)
                pend.append(v)
    assert vistos == set(t)


def test_escudo_unico_por_territorio(mapa, estado):
    """Un dueño de solo escudo con varios concellos lleva UN escudo, no uno por concello, y sin
    fronteras interiores."""
    est = copy.deepcopy(estado)
    o = _ordes(est)
    est["donos"][o]["cor"] = {"colores": ["#ffffff"], "pesos": [1.0], "fonte": "escudo", "escudo": "assets/escudos/15001.png"}
    ventana = mapa.ventana_general(1.0)
    unida = mapa.dibujar(est, ventana, 600, 600, unir_territorios=True)
    suelta = mapa.dibujar(est, ventana, 600, 600, unir_territorios=False)
    assert unida.tobytes() != suelta.tobytes()
    # el interior de Ordes (blanco) ya no tiene líneas de frontera: es más claro en conjunto
    bbox = mapa.geometria(est["donos"][o]["territorio"]).bounds
    f = lambda x, y: ((x - ventana[0]) * 600 / (ventana[2] - ventana[0]), (ventana[3] - y) * 600 / (ventana[3] - ventana[1]))
    x0, y1 = f(bbox[0], bbox[1])
    x1, y0 = f(bbox[2], bbox[3])
    caja = (int(x0), int(y0), int(x1), int(y1))
    oscuros = lambda im: sum(1 for p in im.crop(caja).getdata() if sum(p) < 200)
    assert oscuros(unida) < oscuros(suelta)


def test_tabla_una_fila_por_concello(estado, tmp_path):
    ruta = tmp_path / "t.tsv"
    tabla(estado, ruta)
    filas = ruta.read_text(encoding="utf-8").strip().split("\n")
    assert len(filas) == 314
    assert sum(1 for f in filas if "Ordes\t" in f.split("\t")[2:3][0] + "\t") >= 98


def test_banderas_recortadas_por_el_territorio(mapa, estado):
    """Con `banderas=True` el territorio de Ordes no es un color liso: se ve su bandera (verde, amarillo
    y negro) y nada se sale del contorno del territorio."""
    ventana = mapa.ventana_general(1.0)
    liso = mapa.dibujar(estado, ventana, 600, 600)
    con = mapa.dibujar(estado, ventana, 600, 600, unir_territorios=True, banderas=True)
    o = _ordes(estado)
    bb = mapa.geometria(estado["donos"][o]["territorio"]).bounds
    ancho = ventana[2] - ventana[0]
    cx = (bb[0] + bb[2]) / 2
    cy = (bb[1] + bb[3]) / 2
    px = int((cx - ventana[0]) * 600 / ancho)
    py = int((ventana[3] - cy) * 600 / (ventana[3] - ventana[1]))
    zona = (px - 40, py - 40, px + 40, py + 40)
    colores = {c for _, c in con.crop(zona).getcolors(10000) and [(0, p) for p in [q for _, q in con.crop(zona).getcolors(10000)]]}
    assert len(colores) > len({p for _, p in liso.crop(zona).getcolors(10000)})
    # el mar (esquina) sigue siendo mar: la bandera no se sale del territorio
    assert con.getpixel((2, 2)) == liso.getpixel((2, 2))
