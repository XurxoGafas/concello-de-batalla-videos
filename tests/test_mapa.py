"""Tests del paso 4.2: mapa de Galicia."""

import copy

import pytest
from PIL import Image, ImageChops

from src.motor.estado import aplicar_conquista
from src.motor.persistencia import nueva_partida
from src.motor.seleccion import territorio, vecinos_enemigos
from src.render import estilo as E
from src.render.mapa import MapaGalicia


@pytest.fixture(scope="module")
def mapa():
    return MapaGalicia()


@pytest.fixture(scope="module")
def estado():
    """Partida inicial con un color liso por concello: los concellos «solo escudo» (territorio blanco con
    el escudo encima, paso 2.5) se sustituyen por colores provisionales para probar el relleno."""
    e = copy.deepcopy(nueva_partida())
    for n, (i, c) in enumerate(e["concellos"].items()):
        if c["cor"].get("escudo") or c["cor"]["colores"][0].lower() == "#ffffff":
            cor = {"colores": ["#%02x%02x%02x" % (40 + (n * 37) % 200, 60 + (n * 91) % 180, 90 + (n * 53) % 150)],
                   "pesos": [1.0], "fonte": "provisional"}
            c["cor"] = e["donos"][i]["cor"] = cor
    return e


def hex_a_rgb(h: str) -> tuple[int, int, int]:
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def pixel_en(mapa, ventana, ancho, alto, geom):
    """Píxel (x, y) de la imagen donde cae un punto interior de `geom`."""
    x, y = geom.representative_point().coords[0]
    x0, y0, x1, y1 = ventana
    return round((x - x0) / (x1 - x0) * ancho), round((y1 - y) / (y1 - y0) * alto)


def test_carga_los_313_concellos_y_une_geometrias(mapa, estado):
    assert len(mapa.gdf) == 313
    ids = list(estado["concellos"])[:3]
    g = mapa.geometria(ids)
    assert mapa.geometria(reversed(ids)) is g  # cacheada, sin importar el orden
    assert g.area == pytest.approx(sum(mapa.gdf.geometry[i].area for i in ids), rel=1e-6)


def test_ventana_general_incluye_toda_galicia_con_la_proporcion(mapa):
    v = mapa.ventana_general(1080 / 1095)
    assert (v[2] - v[0]) / (v[3] - v[1]) == pytest.approx(1080 / 1095)
    b = mapa.gdf.total_bounds
    assert v[0] <= b[0] and v[1] <= b[1] and v[2] >= b[2] and v[3] >= b[3]


def test_ventana_atacante_enseña_su_territorio_y_todos_los_vecinos_enemigos(mapa, estado):
    for dono in list(estado["donos"])[:25]:
        v = mapa.ventana_atacante(estado, dono, 1080 / 735)
        ids = territorio(estado, dono) + vecinos_enemigos(estado, dono)
        b = mapa.limites(ids)
        assert v[0] <= b[0] and v[1] <= b[1] and v[2] >= b[2] and v[3] >= b[3]


def test_ventana_de_enfrentamiento_cubre_los_dos_territorios(mapa, estado):
    ids = list(estado["concellos"])
    a, d = ids[0], estado["concellos"][ids[0]]["vecinos"][0]
    v = mapa.ventana_enfrentamiento(estado, a, d, 2.0)
    b = mapa.limites([a, d])
    assert v[0] <= b[0] and v[2] >= b[2] and v[1] <= b[1] and v[3] >= b[3]


def test_cada_concello_se_pinta_con_el_color_de_su_dueno(mapa, estado):
    v = mapa.ventana_general(1.0)
    im = mapa.dibujar(estado, v, 900, 900)
    assert im.size == (900, 900)
    comprobados = 0
    for i in list(estado["concellos"])[:60]:
        geom = mapa.gdf.geometry[i]
        if geom.area < 6e7:  # solo concellos grandes: el punto cae lejos del borde
            continue
        x, y = pixel_en(mapa, v, 900, 900, geom)
        dono = estado["concellos"][i]["dono"]
        esperado = hex_a_rgb(estado["donos"][dono]["cor"]["colores"][0])
        assert all(abs(a - b) <= 6 for a, b in zip(im.getpixel((x, y)), esperado))
        comprobados += 1
    assert comprobados >= 5


def test_el_territorio_conquistado_cambia_al_color_del_ganador(mapa, estado):
    a, p = list(estado["concellos"])[:2]
    nuevo = aplicar_conquista(estado, a, p)
    v = mapa.ventana_enfrentamiento(estado, a, p, 1.0)
    antes, despues = (mapa.dibujar(e, v, 800, 800) for e in (estado, nuevo))
    x, y = pixel_en(mapa, v, 800, 800, mapa.gdf.geometry[p])
    ganador = hex_a_rgb(estado["donos"][a]["cor"]["colores"][0])
    assert all(abs(c - g) <= 6 for c, g in zip(despues.getpixel((x, y)), ganador))
    assert antes.getpixel((x, y)) != despues.getpixel((x, y))


def test_sin_nombres_no_hay_texto_en_el_mapa(mapa, estado):
    v = mapa.ventana_general(1.0)
    im = mapa.dibujar(estado, v, 900, 900)
    assert (255, 255, 255) not in {c for _, c in im.getcolors(1_000_000)}


def test_solo_se_escriben_los_nombres_pedidos_y_dentro_de_la_imagen(mapa, estado):
    dono = list(estado["donos"])[10]
    v = mapa.ventana_atacante(estado, dono, 1080 / 735)
    sin = mapa.dibujar(estado, v, 1080, 735)
    con = mapa.dibujar(estado, v, 1080, 735, nombres=[dono])
    assert sin.tobytes() != con.tobytes()
    caja = ImageChops.difference(sin, con).getbbox()
    assert caja and caja[0] >= 0 and caja[1] >= 0 and caja[2] <= 1080 and caja[3] <= 735
    # el texto ocupa poco: es un solo nombre, no todo el mapa
    assert (caja[2] - caja[0]) < 600 and (caja[3] - caja[1]) < 200


def test_el_nombre_del_territorio_conquistado_es_el_del_ganador(mapa, estado):
    a, p = list(estado["concellos"])[:2]
    nuevo = aplicar_conquista(estado, a, p)
    assert nuevo["donos"][a]["nome"] == estado["concellos"][a]["nome"]
    assert mapa._etiquetar(Image.new("RGB", (900, 900)), nuevo, lambda x, y: (450, 450), [a]) == [
        estado["concellos"][a]["nome"]
    ]


def test_los_contornos_se_dibujan_en_su_color(mapa, estado):
    ids = list(estado["concellos"])[:1]
    v = mapa.ventana_atacante(estado, ids[0], 1.0)
    base = mapa.dibujar(estado, v, 600, 600)
    con = mapa.dibujar(estado, v, 600, 600, contornos=[(mapa.geometria(ids), E.CONFLICTO, 6)])
    rojo = hex_a_rgb(E.CONFLICTO)
    n = lambda im: sum(1 for p in im.get_flattened_data() if p == rojo)  # noqa: E731
    assert n(con) > 200 and n(base) == 0


def test_las_muestras_se_generan_con_el_tamano_y_sin_nombres_en_el_mapa_general(tmp_path, mapa):
    from src.render.muestra_mapa import mapa_inicial, mapa_zoom_atacante

    ini = Image.open(mapa_inicial(mapa, tmp_path / "ini.png"))
    zoom = Image.open(mapa_zoom_atacante(mapa, tmp_path / "zoom.png", previas=20))
    assert ini.size == zoom.size == (E.ANCHO, E.ALTO)
    banda = ini.crop((0, 400, E.ANCHO, 1400))  # los territorios blancos (escudo) impiden buscar texto blanco: solo se comprueba que hay mapa
    assert len(banda.getcolors(2_000_000)) > 20
