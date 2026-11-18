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


def test_panel_de_vaca_es_blanco_con_manchas_y_determinista():
    a = E.panel_vaca(540, 600)
    assert a.tobytes() == E.panel_vaca(540, 600).tobytes()
    px = list(a.get_flattened_data())
    blancos = sum(p == (255, 255, 255) for p in px) / len(px)
    negros = sum(max(p) < 60 for p in px) / len(px)
    assert 0.6 < blancos < 0.95 and 0.05 < negros < 0.35
    # manchas repartidas: hay negro también en la franja central, pero menos que en los bordes
    def negro(x0, x1):
        zona = list(a.crop((x0, 0, x1, 600)).get_flattened_data())
        return sum(max(p) < 60 for p in zona) / len(zona)
    assert 0 < negro(180, 360) < max(negro(0, 180), negro(360, 540))
    # manchas pequeñas: ningún cuadrado de 110 px es todo negro
    for x in range(0, 430, 20):
        for y in range(0, 490, 20):
            assert a.crop((x, y, x + 110, y + 110)).convert("L").getextrema()[1] > 60


def test_el_mar_del_mapa_es_azul_cielo(mapa):
    estado = nueva_partida()
    im = mapa.dibujar(estado, mapa.ventana_general(1.0), 400, 400)
    assert im.getpixel((2, 2)) == tuple(int(E.MAR[i:i + 2], 16) for i in (1, 3, 5))


def test_vs_centrado_entre_los_dos_bandos():
    assert (EN.CX_A + EN.CX_D) / 2 == EN.CX_C == E.ANCHO / 2


def test_pastilla_central_diferencia_y_bonus():
    from src.motor.persistencia import nueva_partida
    from src.motor.seleccion import Enfrentamiento
    est = nueva_partida()
    a, b = list(est["donos"])[:2]
    est["donos"][a]["vacas"], est["donos"][b]["vacas"] = 1500, 1200
    f = Enfrentamiento(a, b, a, b)
    assert EN.texto_diferencia(est, f) == ["diferencia = +25%", "bonus = ×1,2"]


def test_icono_de_vaca_en_lugar_de_la_palabra():
    sin = E.ancho_linea("1.500", 44)
    con = E.ancho_linea(f"1.500 {E.ICONO_VACA}", 44)
    assert con > sin + 40
    pastilla = E.crear_pastilla(f"1.500 {E.ICONO_VACA}", 44, 20)
    assert pastilla.width == E.tamano_pastilla(f"1.500 {E.ICONO_VACA}", 44, 20)[0]
    # el icono tiene piel rosada (hocico): aparece color rosado/rojizo en la pastilla
    px = pastilla.convert("RGB").get_flattened_data()
    assert any(r > 170 and 80 < g < 130 and b < 120 for r, g, b in px)
