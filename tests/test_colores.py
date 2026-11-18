"""Tests de la extracción de colores de banderas (paso 2.4)."""

import shutil

import pytest
from PIL import Image, ImageDraw

from src.datos.colores import abrir_imagen, paleta

AZUL = (0, 51, 153)
AMARILLO = (255, 204, 0)


def bandera_dos_franjas(ancho=200, alto=100, frac_azul=0.75):
    im = Image.new("RGBA", (ancho, alto), AMARILLO + (255,))
    ImageDraw.Draw(im).rectangle([0, 0, int(ancho * frac_azul) - 1, alto], fill=AZUL + (255,))
    return im


def test_dos_franjas_dan_dos_colores_con_su_peso():
    p = paleta(bandera_dos_franjas())
    assert [c for c, _ in p] == ["#003399", "#ffcc00"]
    assert p[0][1] == pytest.approx(0.75, abs=0.02)
    assert p[1][1] == pytest.approx(0.25, abs=0.02)


def test_los_pesos_suman_uno():
    assert sum(w for _, w in paleta(bandera_dos_franjas())) == pytest.approx(1.0, abs=0.01)


def test_los_pixeles_transparentes_se_ignoran():
    im = Image.new("RGBA", (100, 100), (0, 0, 0, 0))  # todo transparente
    ImageDraw.Draw(im).rectangle([0, 0, 49, 99], fill=AZUL + (255,))
    p = paleta(im)
    assert len(p) == 1 and p[0][0] == "#003399"


def test_imagen_totalmente_transparente_falla():
    with pytest.raises(ValueError):
        paleta(Image.new("RGBA", (10, 10), (0, 0, 0, 0)))


def test_tonos_parecidos_se_fusionan():
    im = bandera_dos_franjas()
    ruido = ImageDraw.Draw(im)
    for x in range(0, 150, 3):  # píxeles de un azul casi igual (antialiasing)
        ruido.point((x, 5), fill=(5, 55, 150, 255))
    assert len(paleta(im)) == 2


def test_color_minoritario_menor_del_4_por_ciento_se_descarta():
    im = bandera_dos_franjas(frac_azul=0.98)
    assert [c for c, _ in paleta(im)] == ["#003399"]


def test_abre_png_y_reduce_el_tamano(tmp_path):
    ruta = tmp_path / "x.png"
    bandera_dos_franjas(ancho=1000, alto=500).save(ruta)
    assert abrir_imagen(ruta).width == 240


@pytest.mark.skipif(shutil.which("rsvg-convert") is None, reason="falta rsvg-convert")
def test_abre_svg(tmp_path):
    ruta = tmp_path / "x.svg"
    ruta.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="300" height="200">'
        '<rect width="300" height="200" fill="#ffcc00"/>'
        '<rect width="150" height="200" fill="#003399"/></svg>',
        encoding="utf-8",
    )
    p = paleta(abrir_imagen(ruta))
    assert {c for c, _ in p} == {"#003399", "#ffcc00"}
