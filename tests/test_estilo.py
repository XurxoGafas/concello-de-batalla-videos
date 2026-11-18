"""Tests del paso 4.1: guía visual."""

import pytest
from fontTools.ttLib import TTFont
from PIL import Image

from src.render import estilo as E


def test_la_tipografia_cubre_los_caracteres_del_gallego():
    cmap = TTFont(str(E.FUENTE_TTF)).getBestCmap()
    necesarios = "ñÑáéíóúÁÉÍÓÚüÜ¡¿×+=·–«»%0123456789.,:;!?()/"
    assert [c for c in necesarios if ord(c) not in cmap] == []


def test_formato_y_zona_segura_coherentes():
    assert (E.ANCHO, E.ALTO) == (1080, 1920) and E.FPS == 30
    x0, y0, x1, y1 = E.ZONA_SEGURA
    assert 0 <= x0 < x1 <= E.ANCHO and 0 <= y0 < y1 <= E.ALTO
    assert (x1 - x0) > E.ANCHO // 2 and (y1 - y0) > E.ALTO // 2


def test_contraste_suficiente_de_los_textos():
    assert E.contraste(E.BLANCO, E.FONDO) >= 7
    assert E.contraste(E.ORO, E.FONDO) >= 7
    assert E.contraste(E.GRIS_AZUL, E.PANEL) >= 4.5
    assert E.contraste(E.FONDO, E.ORO) >= 7  # texto oscuro sobre la insignia dorada
    assert E.contraste("#FFFFFF", "#FFFFFF") == pytest.approx(1)


def test_nombres_largos_caben_en_dos_lineas():
    for nombre in ("Carballeda de Valdeorras", "San Cristovo de Cea", "Cerdedo Cotobade",
                   "Santa Comba", "Ordes", "Pazos de Borbén"):
        lineas, tam = E.dividir_nombre(nombre, 52, 410)
        assert 1 <= len(lineas) <= 2 and tam >= E.T_MIN
        assert " ".join(lineas) == nombre
        assert all(E.ancho_texto(x, tam) <= 410 for x in lineas)


def test_ajustar_tamano_no_baja_del_minimo():
    assert E.ajustar_tamano("a" * 80, 80, 100) == E.T_MIN
    assert E.ajustar_tamano("Ordes", 56, 1000) == 56


def test_fotograma_de_muestra_se_genera_con_el_tamano_correcto(tmp_path):
    from src.render.muestra_estilo import generar

    ruta = generar(tmp_path / "estilo.png", previas=10)
    im = Image.open(ruta)
    assert im.size == (E.ANCHO, E.ALTO)
    # la zona inferior (bajo la zona segura) queda sin elementos: solo color de fondo
    bajo = im.crop((0, E.ALTO - E.MARGEN_INF + 20, E.ANCHO, E.ALTO))
    assert bajo.getcolors() is not None and len(bajo.getcolors()) == 1
