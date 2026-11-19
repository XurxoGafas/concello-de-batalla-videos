"""Tests de la línea de tiempo del sonido y la mezcla (paso 5.2)."""

import numpy as np
import pytest

from src.audio import mezcla as Z
from src.audio import sintesis as S
from src.render import escenas as ES
from src.render import linea_tiempo as LT
from src.render.mapa import MapaGalicia


@pytest.fixture(scope="module")
def montaje():
    return ES.construir_episodio(ES.estado_de_muestra(), "muestra", MapaGalicia())


@pytest.fixture(scope="module")
def eventos(montaje):
    return LT.eventos(montaje)


def _num(eventos, n):
    return [e for e in eventos if e.num == n]


def test_eventos_ordenados_y_dentro_del_video(montaje, eventos):
    assert [e.t for e in eventos] == sorted(e.t for e in eventos)
    assert eventos[0].t == 0.0 and eventos[0].num == "01"
    assert all(0 <= e.t < montaje.duracion for e in eventos)


def test_cada_batalla_tiene_sus_sonidos_basicos(eventos):
    """Tres batallas: 3 sorteos de atacante y de defensor, 3 duelos, 9 tiradas, 3 ganadores, 3 conquistas."""
    for n, veces in (("05", 3), ("08", 3), ("07", 3), ("10", 3), ("11", 3), ("12", 3), ("13", 3), ("14", 3),
                     ("15", 9), ("16", 9), ("21", 3), ("24", 3), ("25", 3), ("27", 6), ("01", 1), ("02", 1), ("03", 1),
                     ("31", 1)):
        assert len(_num(eventos, n)) == veces, n
    assert len(_num(eventos, "06")) == 6  # bloqueo del atacante y del defensor
    assert len(_num(eventos, "26")) == 6  # dos tandas de confeti por conquista


def test_los_tics_son_uno_por_paso_del_sorteo(eventos, montaje):
    selecciones = [e for e in montaje.escenas if isinstance(e, ES.EscenaSeleccion)]
    assert [len(e.params) for e in _num(eventos, "05")] == [len(s.pasos_a) for s in selecciones]
    assert [len(e.params) for e in _num(eventos, "08")] == [len(s.pasos_d) for s in selecciones]


def test_cada_dado_tiene_un_ding_o_un_empate(eventos):
    assert len(_num(eventos, "17")) + len(_num(eventos, "18")) == 9
    assert len(_num(eventos, "19")) == len(_num(eventos, "17"))
    assert all(1 <= e.params[0] <= 5 for e in _num(eventos, "17"))


def test_el_pop_del_defensor_cae_al_entrar_en_el_panel(eventos, montaje):
    """El efecto 10 empieza con el zoom (t_m) y su «pop» va a 0,45 s de montaje, cuando entra el defensor."""
    for ev, e, ini in zip(_num(eventos, "10"), [e for e in montaje.escenas if isinstance(e, ES.EscenaSeleccion)],
                          [i for e, i in zip(montaje.escenas, montaje.inicios) if isinstance(e, ES.EscenaSeleccion)]):
        assert ev.t == pytest.approx(ini + e.t_m)
        assert S.T_POP_MORPH == pytest.approx(0.45 / S.VELOCIDAD)


def test_pops_de_extension_acaban_cuando_acaba_el_color():
    assert LT.tiempos_pops_extension(1) == [pytest.approx(2.3)]
    t = LT.tiempos_pops_extension(40)
    assert len(t) == 24 and t == sorted(t) and t[-1] == pytest.approx(2.3)
    assert t[0] > 0.5


def test_mezcla_coloca_cada_efecto_en_su_instante(montaje):
    pista = Z.mezclar(montaje)
    assert pista.shape[1] == 2 and len(pista) == int(np.ceil(montaje.duracion / ES.VELOCIDAD * S.SR))
    primer = np.argmax(np.abs(pista).max(axis=1) > 1e-4)
    assert primer < 0.01 * S.SR  # el golpe de la portada suena en el primer fotograma
    assert np.max(np.abs(pista)) > 0.1


def test_los_sonidos_para_una_sola_vez_son_los_mismos_que_los_aprobados():
    """Con los pasos reales, los tics del 05 y 08 coinciden con los archivos aprobados."""
    a = Z.efecto(LT.Evento(0.0, "05", params=S.PASOS_SORTEO_ATACANTE))
    assert np.allclose(a, S.tics_sorteo_atacante())
