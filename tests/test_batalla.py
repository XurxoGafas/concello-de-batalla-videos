"""Tests del paso 3.2: dados, multiplicador y muerte súbita."""

import random

import pytest

from src.motor.batalla import resolver, simular_batalla

IGUALES = (500, 500)  # mismas vacas: nadie multiplica


# --- Ejemplo del enunciado: 6 contra 1 → +5 ---


def test_ejemplo_del_enunciado_suma_las_diferencias():
    # Tiradas: 6-1 (+5 A), 3-4 (+1 B), 2-3 (+1 B)  →  A 5 · B 2
    r = resolver((6, 3, 2), (1, 4, 3), *IGUALES)
    assert [(t.puntos_a, t.puntos_b) for t in r.tiradas] == [(5, 0), (0, 1), (0, 1)]
    assert (r.puntos_a, r.puntos_b) == (5, 2)
    assert r.ganador == "a" and not r.hubo_empate


def test_no_se_restan_puntos_al_perder_una_tirada():
    r = resolver((1, 1, 1), (6, 6, 6), *IGUALES)
    assert (r.puntos_a, r.puntos_b) == (0, 15)
    assert r.ganador == "b"


def test_tirada_empatada_no_suma_a_nadie():
    r = resolver((3, 4, 6), (3, 2, 5), *IGUALES)
    assert [(t.puntos_a, t.puntos_b) for t in r.tiradas] == [(0, 0), (2, 0), (1, 0)]


# --- El multiplicador solo lo aplica el bando con más vacas ---


def test_solo_multiplica_el_bando_con_mas_vacas():
    # A: 2 puntos, tiene el doble de vacas → tope ×1,5 → 3,0
    r = resolver((3, 1, 1), (1, 1, 1), 2000, 1000)
    assert (r.mult_a, r.mult_b) == (1.5, 1.0)
    assert (r.decimas_a, r.decimas_b) == (30, 0)


def test_el_bando_con_menos_vacas_no_multiplica_aunque_puntue():
    # B: 3 puntos con menos vacas → se queda en 3,0 (no 4,5)
    r = resolver((1, 1, 1), (2, 2, 2), 2000, 1000)
    assert (r.puntos_a, r.puntos_b) == (0, 3)
    assert (r.mult_a, r.mult_b) == (1.5, 1.0)
    assert (r.decimas_a, r.decimas_b) == (0, 30)


def test_multiplicador_con_un_decimal_se_compara_exacto():
    # T1: 4-1 (+3) · T2: 4-2 (+2) · T3: 3-1 (+2)  → A 7 puntos × 1,3 = 9,1 (no 9)
    r = resolver((4, 4, 3), (1, 2, 1), 1300, 1000)
    assert r.puntos_a == 7 and r.mult_a == 1.3
    assert r.decimas_a == 91 and r.puntuacion_a == 9.1


def test_el_multiplicador_puede_dar_la_vuelta_al_resultado():
    # T1: 5-1 (+4 A) · T2: 1-4 (+3 B) · T3: 2-4 (+2 B)  → A 4 · B 5
    dados = ((5, 1, 2), (1, 4, 4))
    sin_bonus = resolver(*dados, 500, 500)
    assert (sin_bonus.puntos_a, sin_bonus.puntos_b) == (4, 5)
    assert sin_bonus.ganador == "b"
    con_bonus = resolver(*dados, 2000, 1000)  # A: 4 × 1,5 = 6,0 > 5
    assert con_bonus.decimas_a == 60 and con_bonus.ganador == "a"
    assert not con_bonus.hubo_empate


# --- Muerte súbita ---


def test_empate_sin_multiplicador_va_a_muerte_subita_y_desempata():
    # 0-0 con vacas iguales → empate. Rondas: (4,4) empata, (2,5) gana B
    r = resolver((3, 3, 3), (3, 3, 3), *IGUALES, dados_muerte_subita=[(4, 4), (2, 5), (6, 1)])
    assert r.hubo_empate
    assert [(x.dado_a, x.dado_b) for x in r.muerte_subita] == [(4, 4), (2, 5)]  # no consume más
    assert r.ganador == "b"


def test_empate_tras_aplicar_el_multiplicador():
    # T1: 5-1 (+4 A) · T2: 1-4 (+3 B) · T3: 1-4 (+3 B)  → A 4 × 1,5 = 6,0 · B 6 × 1 = 6,0
    r = resolver((5, 1, 1), (1, 4, 4), 2000, 1000, dados_muerte_subita=[(2, 6)])
    assert (r.puntos_a, r.puntos_b) == (4, 6)
    assert r.decimas_a == r.decimas_b == 60
    assert r.hubo_empate and r.ganador == "b"


def test_sin_dados_de_muerte_subita_falla():
    with pytest.raises(ValueError):
        resolver((3, 3, 3), (3, 3, 3), *IGUALES)


@pytest.mark.parametrize("a,b", [((0, 1, 1), (1, 1, 1)), ((7, 1, 1), (1, 1, 1)), ((1, 1), (1, 1))])
def test_dados_invalidos_fallan(a, b):
    with pytest.raises(ValueError):
        resolver(a, b, *IGUALES)


# --- Semilla y reproducibilidad ---


def test_misma_semilla_mismo_resultado():
    assert simular_batalla(1200, 800, semilla=42) == simular_batalla(1200, 800, semilla=42)


def test_distintas_semillas_dan_resultados_distintos():
    resultados = {simular_batalla(1000, 1000, semilla=s).tiradas for s in range(50)}
    assert len(resultados) > 10


def test_sin_semilla_ni_generador_falla():
    with pytest.raises(ValueError):
        simular_batalla(10, 10)


def test_encadenar_batallas_con_un_generador_es_reproducible():
    def tres(seed):
        rng = random.Random(seed)
        return [simular_batalla(500, 700, rng=rng) for _ in range(3)]

    assert tres(7) == tres(7)
    assert tres(7) != tres(8)


def test_la_batalla_guarda_la_semilla_y_los_dados():
    r = simular_batalla(300, 300, semilla=99)
    assert r.semilla == 99 and len(r.tiradas) == 3
    # se puede reproducir sin volver a sortear usando los dados guardados
    de_nuevo = resolver(
        [t.dado_a for t in r.tiradas],
        [t.dado_b for t in r.tiradas],
        r.vacas_a,
        r.vacas_b,
        [(x.dado_a, x.dado_b) for x in r.muerte_subita],
        semilla=99,
    )
    assert de_nuevo == r


# --- Propiedades sobre muchas batallas ---


def test_invariantes_en_muchas_batallas():
    for semilla in range(2000):
        r = simular_batalla(100 + semilla, 5000, semilla=semilla)
        assert all(1 <= t.dado_a <= 6 and 1 <= t.dado_b <= 6 for t in r.tiradas)
        assert all(t.puntos_a == 0 or t.puntos_b == 0 for t in r.tiradas)
        assert r.puntos_a == sum(t.puntos_a for t in r.tiradas)
        assert r.ganador in ("a", "b")
        assert r.mult_a == 1.0 or r.mult_b == 1.0
        if r.hubo_empate:
            assert r.decimas_a == r.decimas_b
            assert all(x.dado_a == x.dado_b for x in r.muerte_subita[:-1])
            assert r.muerte_subita[-1].dado_a != r.muerte_subita[-1].dado_b
        else:
            assert (r.ganador == "a") == (r.decimas_a > r.decimas_b)


def test_con_las_mismas_vacas_cada_bando_gana_la_mitad():
    gana_a = sum(simular_batalla(500, 500, semilla=s).ganador == "a" for s in range(20000))
    assert gana_a / 20000 == pytest.approx(0.5, abs=0.02)


def test_el_tope_de_vacas_da_ventaja_cercana_al_59_por_ciento():
    # Cálculo exacto previo: con ×1,5 el favorecido gana ≈ 59,1 % (muerte súbita al 50 %)
    gana_a = sum(simular_batalla(1500, 1000, semilla=s).ganador == "a" for s in range(20000))
    assert gana_a / 20000 == pytest.approx(0.591, abs=0.02)
