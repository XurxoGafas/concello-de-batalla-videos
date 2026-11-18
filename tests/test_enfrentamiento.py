"""Tests del paso 4.3: pantalla de enfrentamiento."""

import random

import pytest
from PIL import Image

from src.motor.persistencia import nueva_partida
from src.motor.seleccion import elegir_enfrentamiento
from src.render import estilo as E
from src.render import enfrentamiento as EN
from src.render.mapa import MapaGalicia


@pytest.fixture(scope="module")
def mapa():
    return MapaGalicia()


def test_num_usa_punto_de_millar():
    assert EN.num(1234567) == "1.234.567" and EN.num(7) == "7"


def test_caja_silueta_encaja_dentro_de_la_caja():
    f = EN.caja_silueta((0, 0, 1000, 500), 300, 125, 2)
    x0, y0 = f(0, 500)
    x1, y1 = f(1000, 0)
    assert 20 <= x0 < x1 <= 580 and 20 <= y0 < y1 <= 230  # k=2: caja 600×250 con 10 px de aire


def test_la_pantalla_tiene_el_tamano_y_el_panel_con_siluetas_y_texto(mapa, tmp_path):
    estado = nueva_partida()
    f = elegir_enfrentamiento(estado, random.Random(3))
    img = EN.pantalla_enfrentamiento(estado, f, mapa, 5)
    assert img.size == (E.ANCHO, E.ALTO)
    # la silueta de cada bando se pinta con el color de su dueño dentro de su columna
    for dono, cx in ((f.atacante, EN.CX_A), (f.defensor, EN.CX_D)):
        c = estado["donos"][dono]["cor"]["colores"][0]
        rgb = tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))
        zona = img.crop((cx - 150, EN.Y_SILUETA, cx + 150, EN.Y_SILUETA + EN.ALTO_SILUETA))
        assert any(p == rgb for p in zona.get_flattened_data())
    # el texto (nombre) es blanco y está en su sitio; abajo del panel solo hay hierba
    assert (255, 255, 255) in {p for p in img.crop((0, EN.Y_NOMBRE, E.ANCHO, EN.Y_NOMBRE + 60)).get_flattened_data()}
    inferior = img.crop((0, E.ALTO - 300, E.ANCHO, E.ALTO))
    r, g, b = inferior.resize((1, 1), Image.BOX).getpixel((0, 0))
    assert g > r + 10 and g > b + 30


def test_los_textos_no_invaden_las_zonas_seguras(mapa):
    estado = nueva_partida()
    f = elegir_enfrentamiento(estado, random.Random(8))
    img = EN.pantalla_enfrentamiento(estado, f, mapa, 5)
    # el panel y sus textos terminan por encima de la zona inferior reservada a la interfaz
    assert EN.PANEL_FIN <= E.ALTO - E.MARGEN_INF + 10
    assert EN.Y_VACAS + 60 < EN.PANEL_FIN
    assert img.getpixel((5, E.ALTO - 5))[1] > 100  # hierba, sin textos, en el borde inferior


def test_generar_crea_la_muestra(tmp_path):
    ruta = EN.generar(tmp_path / "e.png", previas=20)
    assert Image.open(ruta).size == (E.ANCHO, E.ALTO)


def test_fondo_foto_cubre_el_fotograma_y_es_verde():
    from src.render.fondo import fondo_foto

    f = fondo_foto(E.ANCHO, E.ALTO)
    assert f.size == (E.ANCHO, E.ALTO)
    r, g, b = (sum(c) / (E.ANCHO * E.ALTO) for c in zip(*f.resize((54, 96)).get_flattened_data()))
    assert g > r and g > b
