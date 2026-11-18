"""Tests del paso 4.1: guía visual."""

import pytest
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw

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
    # la zona inferior (bajo la zona segura) queda solo con hierba: predomina el verde
    bajo = im.crop((0, E.ALTO - E.MARGEN_INF + 20, E.ANCHO, E.ALTO)).resize((1, 1), Image.BOX)
    r, g, b = bajo.getpixel((0, 0))
    assert g > r + 15 and g > b + 40  # la foto de hierba es más apagada que la dibujada


# --- Zoom del mapa ---


def test_el_zoom_encuadra_los_territorios_con_la_proporcion_pedida():
    lim = (500_000.0, 4_700_000.0, 540_000.0, 4_730_000.0)  # 40 × 30 km
    x0, y0, x1, y1 = E.caja_de_zoom(lim, 1080 / 510)
    assert (x1 - x0) / (y1 - y0) == pytest.approx(1080 / 510)
    assert x0 <= lim[0] and y0 <= lim[1] and x1 >= lim[2] and y1 >= lim[3]  # nunca recorta
    assert (x0 + x1) / 2 == pytest.approx((lim[0] + lim[2]) / 2)  # centrado


def test_dos_concellos_pequenos_no_se_amplian_mas_del_minimo():
    lim = (500_000.0, 4_700_000.0, 505_000.0, 4_704_000.0)  # 5 × 4 km
    x0, y0, x1, y1 = E.caja_de_zoom(lim, 1080 / 510)
    assert min(x1 - x0, y1 - y0) >= 40_000


def test_un_territorio_enorme_hace_menos_zoom_y_se_ve_entero():
    chico = E.caja_de_zoom((0, 0, 10_000, 8_000), 2.0)
    grande = E.caja_de_zoom((0, 0, 200_000, 180_000), 2.0)
    assert (grande[2] - grande[0]) > 4 * (chico[2] - chico[0])  # mucha más superficie visible
    assert grande[0] < 0 and grande[2] > 200_000 and grande[1] < 0 and grande[3] > 180_000


# --- Pastillas «de vaca» ---


def test_pastilla_vaca_es_blanca_con_manchas_negras_y_esta_centrada():
    img = Image.new("RGB", (600, 300), E.PANEL)
    x0, y0, x1, y1 = E.pastilla_vaca(img, 300, 150, "143 vacas", 46)
    w, h = E.tamano_pastilla("143 vacas", 46)
    assert (x1 - x0, y1 - y0) == (w, h)
    assert abs((x0 + x1) / 2 - 300) <= 1 and abs((y0 + y1) / 2 - 150) <= 1
    colores = {c for _, c in img.crop((x0, y0, x1, y1)).getcolors(100000)}
    assert (255, 255, 255) in colores  # blanco
    assert any(sum(c) < 100 for c in colores)  # y manchas oscuras


def test_pastilla_vaca_es_determinista_y_admite_varias_lineas():
    def pinta(texto):
        im = Image.new("RGB", (600, 300), E.PANEL)
        E.pastilla_vaca(im, 300, 150, texto, 44, 20)
        return im.tobytes()
    assert pinta("×1,5") == pinta("×1,5")
    assert pinta(["dif. vacas", "+50%"]) == pinta(["dif. vacas", "+50%"])
    w1, h1 = E.tamano_pastilla("+50%", 44)
    w2, h2 = E.tamano_pastilla(["dif. vacas", "+50%"], 44)
    assert h2 > h1 and w2 >= w1


def test_texto_centrado_exacto_centra_la_tinta():
    img = Image.new("L", (400, 200), 0)
    d = ImageDraw.Draw(img)
    E.texto_centrado_exacto(d, 200, 100, "×1,5", 60, color=255)
    x0, y0, x1, y1 = img.getbbox()
    assert abs((x0 + x1) / 2 - 200) <= 1.5 and abs((y0 + y1) / 2 - 100) <= 1.5


# --- Fondo de hierba ---


def test_fondo_de_hierba_es_verde_determinista_y_del_tamano_pedido():
    from src.render.fondo import fondo_hierba

    a = fondo_hierba(270, 480)
    assert a.size == (270, 480)
    assert a.tobytes() == fondo_hierba(270, 480).tobytes()  # misma semilla, mismo fondo
    assert a.tobytes() != fondo_hierba(270, 480, semilla=8).tobytes()
    r, g, b = a.resize((1, 1), Image.BOX).getpixel((0, 0))
    assert g > r + 15 and g > b + 40  # la foto de hierba es más apagada que la dibujada


def test_fondo_de_hierba_se_mueve_con_el_viento_y_es_ciclico():
    from src.render.fondo import fondo_hierba

    f0, f1 = fondo_hierba(200, 300, fase=0.0), fondo_hierba(200, 300, fase=0.25)
    assert f0.tobytes() != f1.tobytes()
    # cíclico: la fase 1 es la fase 0 (salvo redondeos de coma flotante, imperceptibles)
    from PIL import ImageChops, ImageStat

    dif = ImageChops.difference(fondo_hierba(200, 300, fase=1.0), f0)
    assert max(ImageStat.Stat(dif).mean) < 0.5


def test_el_texto_sobre_la_hierba_tiene_borde_oscuro_para_leerse():
    # el título dorado va con trazo del color de fondo oscuro: contraste alto contra el trazo
    assert E.contraste(E.ORO, E.FONDO) >= 7 and E.contraste(E.BLANCO, E.FONDO) >= 7
