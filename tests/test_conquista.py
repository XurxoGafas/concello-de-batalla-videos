"""Tests de la animación de conquista (paso 4.5)."""

import pytest
from PIL import ImageChops

from src.render import conquista as C
from src.render import dados as D
from src.render import enfrentamiento as M
from src.render import estilo as E

pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(scope="module")
def ctx():
    return C.conquista_de_muestra()


def _hex(c):
    return tuple(int(c[i:i + 2], 16) for i in (1, 3, 5))


def test_gaita_sprite_con_transparencia():
    g = D.gaita_sprite(200)
    assert g.height == 200 and g.getpixel((0, 0))[3] == 0
    assert _hex("#C62F3A") in {p[:3] for p in g.get_flattened_data() if p[3] == 255}  # fol rojo


def test_los_rotulos_cambian_a_campion_y_malogrado(ctx):
    antes, despues = C.fotograma(ctx, 0.2), C.fotograma(ctx, 0.9)
    zona = (0, M.Y_ROTULO - 5, E.ANCHO, M.Y_ROTULO + 70)
    assert ImageChops.difference(antes.crop(zona), despues.crop(zona)).getbbox() is not None
    oro = _hex(E.ORO)
    lado = (int(ctx.cx_ganador) - 160, M.Y_ROTULO, int(ctx.cx_ganador) + 160, M.Y_ROTULO + 70)
    assert oro in set(despues.crop(lado).get_flattened_data())  # «CAMPIÓN» en dorado sobre el ganador
    assert oro not in set(antes.crop(lado).get_flattened_data())


def test_el_color_del_ganador_se_extiende_por_el_territorio_del_perdedor(ctx):
    f = C.M.MAPA_Y0
    inicio, fin = C.fotograma(ctx, C.T_EXTENSION - 0.05), C.fotograma(ctx, C.T_EXTENSION + C.D_EXTENSION + 0.1)
    banda = (0, f, E.ANCHO, f + M.MAPA_ALTO)
    assert ImageChops.difference(inicio.crop(banda), fin.crop(banda)).getbbox() is not None
    # a mitad de camino hay menos concellos cambiados que al final
    medio = C.fotograma(ctx, C.T_EXTENSION + 0.45 * C.D_EXTENSION)
    d_medio = ImageChops.difference(inicio.crop(banda), medio.crop(banda)).convert("L").point(lambda v: 255 if v > 30 else 0).histogram()[255]
    d_fin = ImageChops.difference(inicio.crop(banda), fin.crop(banda)).convert("L").point(lambda v: 255 if v > 30 else 0).histogram()[255]
    assert 0 < d_medio < d_fin


def test_orden_de_extension_empieza_por_la_frontera(ctx):
    g = ctx.mapa.gdf.geometry
    contacto = g[ctx.f.concello_atacante if ctx.ganador == ctx.f.atacante else ctx.f.concello_defensor].centroid
    dist = [g[i].centroid.distance(contacto) for i in ctx.orden]
    assert dist == sorted(dist)
    assert set(ctx.orden) == set(ctx.estado_antes["donos"][ctx.perdedor]["territorio"])


def test_gaita_confeti_y_pastillas_aparecen_a_su_hora(ctx):
    zona = (380, D.Y_MEDIO - 120, 700, D.Y_MEDIO + 140)
    sin = C.fotograma(ctx, C.T_GAITA - 0.1).crop(zona)
    con = C.fotograma(ctx, C.T_GAITA + 0.8).crop(zona)
    assert ImageChops.difference(sin, con).getbbox() is not None
    rojo_fol = _hex("#C62F3A")
    assert rojo_fol not in set(sin.get_flattened_data()) and rojo_fol in set(con.get_flattened_data())
    pastillas = (int(ctx.cx_ganador) - 120, D.Y_MEDIO - 60, int(ctx.cx_ganador) + 220, D.Y_MEDIO + 110)
    assert ImageChops.difference(C.fotograma(ctx, C.T_PASTILLAS - 0.1).crop(pastillas),
                                 C.fotograma(ctx, C.T_PASTILLAS + 0.7).crop(pastillas)).getbbox() is not None


def test_es_determinista_y_dura_lo_previsto(ctx):
    assert C.fotograma(ctx, 2.3).tobytes() == C.fotograma(ctx, 2.3).tobytes()
    assert C.numero_de_fotogramas() == 126
    assert C.fotograma(ctx, 0).size == (E.ANCHO, E.ALTO)


def test_pluralizacion_gallega():
    assert C._plural(1) == "+1 concello" and C._plural(4) == "+4 concellos"
