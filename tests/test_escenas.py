"""Tests de las escenas y el montaje del episodio completo (paso 4.6)."""

import random

import pytest

from src.motor.estado import jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.render import escenas as S
from src.render import estilo as E
from src.render import enfrentamiento as M
from src.render import ranking as R
from src.render.mapa import MapaGalicia


@pytest.fixture(scope="module")
def mapa():
    return MapaGalicia()


@pytest.fixture(scope="module")
def montaje(mapa):
    return S.construir_episodio(S.estado_de_muestra(), "muestra", mapa)


def _tipos(m):
    return [type(e).__name__ for e in m.escenas]


def test_estructura_intro_tres_batallas_y_cierre(montaje):
    assert _tipos(montaje) == ["EscenaPortada", "EscenaIntro"] + ["EscenaSeleccion", "EscenaBatalla", "EscenaConquista"] * 3 + ["EscenaCierre"]


def test_el_video_dura_entre_80_y_90_segundos(montaje):
    assert 80 <= montaje.duracion <= 90


def test_la_duracion_se_adapta_con_muerte_subita(mapa):
    """Cualquier episodio (con o sin muertes súbitas) cae en el rango; el cierre absorbe la diferencia."""
    estado = S.estado_de_muestra()
    for semilla in ("b", "d", "f"):
        m = S.construir_episodio(estado, semilla, mapa)
        assert 80 <= m.duracion <= 90, (semilla, m.duracion)


def test_los_fotogramas_son_validos_y_deterministas(montaje):
    for t in (0.5, 3.0, 8.0, 20.0, 40.0, montaje.duracion - 0.1):
        a, b = S.fotograma_de_video(montaje, t), S.fotograma_de_video(montaje, t)
        assert a.size == (E.ANCHO, E.ALTO) and a.tobytes() == b.tobytes()


def test_fundido_cruzado_entre_escenas(montaje):
    # batalla → conquista conserva un fundido corto; la intro y la selección son un corte exacto
    j = next(i for i, e in enumerate(montaje.escenas) if isinstance(e, S.EscenaConquista))
    t = montaje.inicios[j] + 0.1
    mezcla = S.fotograma_de_video(montaje, t)
    a = montaje.escenas[j - 1].fotograma(t - montaje.inicios[j - 1])
    b = montaje.escenas[j].fotograma(t - montaje.inicios[j])
    assert mezcla.tobytes() not in (a.tobytes(), b.tobytes())


def test_plano_continuo_sin_cortes(montaje):
    intro, sel, bat = montaje.escenas[1], montaje.escenas[2], montaje.escenas[3]
    assert intro.fundido == 0.0 and sel.fundido == 0.0 and bat.fundido == 0.0
    assert intro.fotograma(intro.duracion).tobytes() == sel.fotograma(0.0).tobytes()
    assert sel.fotograma(sel.duracion).tobytes() == bat.fotograma(0.0).tobytes()


def test_sorteos_terminan_en_atacante_y_defensor(montaje):
    sel = montaje.escenas[2]
    assert sel.sec_a[-1] == sel.f.atacante
    assert sel.sec_d[-1] == sel.f.concello_defensor
    assert len(sel.sec_a) == len(sel.pasos_a) and len(sel.sec_d) == len(sel.pasos_d)
    assert 1.8 <= sum(sel.pasos_a) <= 2.6  # ≈2 s de incertidumbre
    assert sel.t_a < sel.t_a_bloqueo < sel.t_z < sel.t_d < sel.t_d_bloqueo < sel.t_m < sel.duracion


def test_zoom_suave_y_monotono():
    assert S._facil(0.0) == 0.0 and S._facil(1.0) == 1.0
    xs = [S._facil(i / 100) for i in range(101)]
    assert all(b >= a for a, b in zip(xs, xs[1:]))
    # arranque y frenado suaves: la velocidad en los extremos es casi nula
    assert xs[1] < 0.001 and 1 - xs[-2] < 0.001


def test_clasificaciones_ordenan_y_desempatan():
    estado = S.estado_de_muestra()
    vit, vac = R.clasificaciones(estado)
    assert len(vit) <= 5 and len(vac) == 5
    assert [v for _, v in vit] == sorted((v for _, v in vit), reverse=True)
    assert [n for _, n in vac] == sorted((n for _, n in vac), reverse=True)
    assert all(estado["donos"][i]["victorias"] == v > 0 for i, v in vit)
    assert all(estado["donos"][i]["vacas"] == n for i, n in vac)
    # el que más vacas tiene es el primero de la lista (y ninguno fuera de ella tiene más)
    assert vac[0][1] == max(d["vacas"] for d in estado["donos"].values())
    assert R.clasificaciones(estado) == (vit, vac)  # determinista


def test_clasificaciones_al_empezar_la_serie():
    estado = nueva_partida()
    vit, vac = R.clasificaciones(estado)
    assert vit == [] and len(vac) == 5
    assert [n for _, n in vac] == sorted((d["vacas"] for d in estado["donos"].values()), reverse=True)[:5]


def test_las_filas_del_ranking_aparecen_de_la_quinta_a_la_primera(montaje):
    cierre = montaje.escenas[-1]
    zona = (0, R.Y_FILAS - 50, E.ANCHO, R.Y_FILAS + 4 * R.PASO_FILA + 50)

    def n_filas(t):
        return cierre.fotograma(t).crop((0, R.Y_FILAS + 4 * R.PASO_FILA - 40, E.ANCHO, R.Y_FILAS + 4 * R.PASO_FILA + 40)).tobytes()
    vacio = cierre.base.crop((0, R.Y_FILAS + 4 * R.PASO_FILA - 40, E.ANCHO, R.Y_FILAS + 4 * R.PASO_FILA + 40)).tobytes()
    assert n_filas(0.3) == vacio          # aún no sale la 5ª
    assert n_filas(1.2) != vacio          # ya salió
    assert zona[1] < zona[3]


def test_escena_del_campeon_cuando_queda_un_unico_dueno(mapa):
    estado = nueva_partida()
    n = 0
    while len(estado["donos"]) > 1:
        n += 1
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla("fin", n)))
    final = S.EscenaFinalSerie(estado, 105, mapa)
    img = final.fotograma(3.0)
    assert img.size == (E.ANCHO, E.ALTO) and final.fotograma(3.0).tobytes() == img.tobytes()
    assert final.fotograma(0.1).tobytes() != img.tobytes()


def test_un_episodio_que_acaba_la_serie_termina_con_la_escena_del_campeon(mapa):
    """Si en el episodio se juega la última batalla, el cierre normal se sustituye por el del campeón."""
    estado = nueva_partida()
    n = 0
    while len(estado["donos"]) > 2:
        n += 1
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla("fin", n)))
    estado["batallas_jugadas"] = n
    m = S.construir_episodio(estado, "fin", mapa)
    assert _tipos(m)[-1] == "EscenaFinalSerie" and _tipos(m).count("EscenaBatalla") == 1


def test_mapa_grande_en_el_sorteo_y_encoge_sin_saltos(montaje):
    sel = montaje.escenas[2]
    # durante el sorteo del atacante, la línea dorada bajo el mapa está más abajo (mapa grande)
    def y_linea(img):
        for y in range(M.LINEA_Y - 5, S.MAPA_GRANDE + M.MAPA_Y0 + 10):
            r, g, b = img.getpixel((5, y))
            if r > 200 and 150 < g < 210 and b < 90:
                return y
        return None
    alturas = [y_linea(sel._fotograma(sel.t_z + k * S.D_ZOOM_ENTRADA / 10)) for k in range(11)]
    assert alturas[0] == M.MAPA_Y0 + S.MAPA_GRANDE and alturas[-1] == M.LINEA_Y
    assert all(b <= a for a, b in zip(alturas, alturas[1:]))          # siempre sube, nunca rebota
    assert max(a - b for a, b in zip(alturas, alturas[1:])) < 80      # sin saltos bruscos


def test_intro_muestra_el_mapa_desde_el_primer_fotograma(montaje):
    intro = montaje.escenas[1]
    assert intro.fotograma(0.0).tobytes() == intro.fotograma(intro.duracion).tobytes()


def test_el_desenfoque_de_movimiento_solo_actua_en_los_zooms(montaje):
    sel = montaje.escenas[2]
    quieto = sel.t_a + 0.5       # sorteo del atacante: mapa quieto → sin promediar
    assert sel.fotograma(quieto).tobytes() == sel._fotograma(quieto).tobytes()
    t = sel.t_z + S.D_ZOOM_ENTRADA / 2   # mitad del zoom: se promedian instantes vecinos
    assert sel.fotograma(t).tobytes() != sel._fotograma(t).tobytes()
