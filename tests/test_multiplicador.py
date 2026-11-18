"""Tests del paso 3.1: multiplicador por vacas."""

import pytest

from src.motor.multiplicador import (
    bonus_porcentaje,
    multiplicador,
    multiplicadores,
    vacas_de_dono,
)


def bonus(porcentaje_extra: int, menor: int = 100) -> int:
    """Bonus cuando el mayor tiene `porcentaje_extra` % más vacas que el menor."""
    return bonus_porcentaje(menor + menor * porcentaje_extra // 100, menor)


# --- Ejemplo confirmado por el usuario ---


def test_ejemplo_arteixo_a_coruna():
    # 1500 vs 1200 → 25 % → se baja a 20 % → ×1,2 para Arteixo; A Coruña no multiplica
    assert multiplicadores(1500, 1200) == (1.2, 1.0)


# --- Ejemplos del enunciado ---


@pytest.mark.parametrize(
    "extra,esperado",
    [(30, 1.3), (40, 1.4), (35, 1.3), (36, 1.4), (70, 1.5)],
)
def test_ejemplos_del_enunciado(extra, esperado):
    assert multiplicador(100 + extra, 100) == esperado


# --- Bordes ---


@pytest.mark.parametrize(
    "extra,esperado_pct",
    [
        (0, 0),
        (5, 0),    # unidad 5 → baja
        (6, 10),   # unidad 6 → sube
        (15, 10),
        (16, 20),
        (45, 40),  # 45 → baja a 40
        (46, 50),  # 46 → sube a 50
        (50, 50),
        (56, 50),  # tope
        (200, 50),
    ],
)
def test_bordes(extra, esperado_pct):
    assert bonus(extra) == esperado_pct


def test_decimales_justo_por_encima_de_la_mitad_suben():
    # 35,5 % → sobra 5,5 > 5 → sube a 40 %; 35 % exacto baja a 30 %
    assert bonus_porcentaje(1355, 1000) == 40
    assert bonus_porcentaje(1350, 1000) == 30
    assert bonus_porcentaje(10501, 10000) == 10  # 5,01 % → sobra 5,01 > 5 → sube


def test_sin_errores_de_coma_flotante_en_los_limites():
    # 3 vacas sobre 20: 15 % exacto → sobra 5 → baja a 10 %
    assert bonus_porcentaje(23, 20) == 10
    # 7 sobre 20: 35 % exacto → baja a 30 %
    assert bonus_porcentaje(27, 20) == 30


# --- Quién multiplica ---


def test_solo_multiplica_el_bando_con_mas_vacas():
    a, b = multiplicadores(100, 150)
    assert (a, b) == (1.0, 1.5)


def test_empate_a_vacas_no_multiplica_nadie():
    assert multiplicadores(500, 500) == (1.0, 1.0)


def test_simetria_el_orden_de_los_argumentos_no_cambia_el_bonus():
    assert bonus_porcentaje(1300, 1000) == bonus_porcentaje(1000, 1300) == 30


def test_una_vaca_contra_muchas_da_el_tope():
    assert multiplicadores(1, 15204) == (1.0, 1.5)


@pytest.mark.parametrize("a,b", [(0, 5), (5, 0), (-1, 3)])
def test_vacas_menores_que_uno_fallan(a, b):
    with pytest.raises(ValueError):
        multiplicadores(a, b)


# --- Territorio con varios concellos ---


def estado_con_territorio():
    return {
        "a": {"vacas": 1200, "dono": "a"},   # A Coruña, que ha conquistado a b
        "b": {"vacas": 1500, "dono": "a"},   # Arteixo, ahora de a
        "c": {"vacas": 2000, "dono": "c"},
    }


def test_vacas_del_dueno_suma_todo_el_territorio():
    e = estado_con_territorio()
    assert vacas_de_dono(e, "a") == 2700
    assert vacas_de_dono(e, "c") == 2000


def test_el_multiplicador_usa_las_vacas_de_todo_el_territorio():
    e = estado_con_territorio()
    # Con solo el concello «a» (1200) frente a «c» (2000) ganaría c ×1,6→1,5.
    # Con el territorio completo de «a» (2700 vs 2000): 35 % → baja a 30 % → ×1,3 para a.
    assert multiplicadores(vacas_de_dono(e, "a"), vacas_de_dono(e, "c")) == (1.3, 1.0)
    assert multiplicadores(e["a"]["vacas"], vacas_de_dono(e, "c")) == (1.0, 1.5)
