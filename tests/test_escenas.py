"""Tests de las escenas y el montaje del episodio completo (paso 4.6)."""

import random

import pytest

from src.motor.estado import jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.render import escenas as S
from src.render import estilo as E
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
    assert _tipos(montaje) == ["EscenaIntro"] + ["EscenaSeleccion", "EscenaBatalla", "EscenaConquista"] * 3 + ["EscenaCierre"]


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
    t = montaje.inicios[1] + 0.1  # la intro y la selección se solapan
    mezcla = S.fotograma_de_video(montaje, t)
    a = montaje.escenas[0].fotograma(t - montaje.inicios[0])
    b = montaje.escenas[1].fotograma(t - montaje.inicios[1])
    assert mezcla.tobytes() not in (a.tobytes(), b.tobytes())


def test_el_sorteo_acaba_en_el_defensor(montaje):
    sel = montaje.escenas[1]
    assert sel.secuencia[-1] == sel.f.concello_defensor
    assert len(sel.secuencia) == len(sel.pasos)
    assert sel.duracion == pytest.approx(sel.t_bloqueo + S.D_BLOQUEO)
    # el atacante aparece en el panel solo a partir de T_PANEL
    antes, despues = sel.fotograma(S.T_PANEL - 0.05), sel.fotograma(S.T_PANEL + 0.4)
    assert antes.tobytes() != despues.tobytes()


def test_clasificaciones_ordenan_y_desempatan():
    estado = S.estado_de_muestra()
    vit, ter = R.clasificaciones(estado)
    assert len(vit) <= 5 and len(ter) == 5
    assert [v for _, v in vit] == sorted((v for _, v in vit), reverse=True)
    assert [n for _, n in ter] == sorted((n for _, n in ter), reverse=True)
    assert all(estado["donos"][i]["victorias"] == v > 0 for i, v in vit)
    assert all(len(estado["donos"][i]["territorio"]) == n for i, n in ter)
    assert R.clasificaciones(estado) == (vit, ter)  # determinista


def test_clasificaciones_al_empezar_la_serie():
    vit, ter = R.clasificaciones(nueva_partida())
    assert vit == [] and len(ter) == 5 and all(n == 1 for _, n in ter)


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
