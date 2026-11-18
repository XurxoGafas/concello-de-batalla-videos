"""Tests del paso 3.3: selección de atacante y defensor."""

import collections
import json
import random
from pathlib import Path

import pytest

from src.motor.seleccion import (
    NoHayEnfrentamiento,
    duenos_vivos,
    elegir_atacante,
    elegir_defensor,
    elegir_enfrentamiento,
    territorio,
    vecinos_enemigos,
)

ESTADO_INICIAL = Path(__file__).resolve().parent.parent / "data" / "processed" / "estado_inicial.json"


def estado(grafo: dict[str, list[str]], duenos: dict[str, str] | None = None) -> dict:
    """Estado mínimo: cada concello con sus vecinos y su dueño (por defecto, él mismo)."""
    duenos = duenos or {}
    return {
        "concellos": {i: {"vecinos": v, "dono": duenos.get(i, i)} for i, v in grafo.items()}
    }


# a — b — c — d  (una línea)
LINEA = {"a": ["b"], "b": ["a", "c"], "c": ["b", "d"], "d": ["c"]}


# --- Vecinos enemigos y dueños vivos ---


def test_vecinos_enemigos_en_una_linea():
    e = estado(LINEA)
    assert vecinos_enemigos(e, "a") == ["b"]
    assert vecinos_enemigos(e, "b") == ["a", "c"]


def test_el_territorio_de_varios_concellos_cuenta_entero():
    # a y b son del dueño «a»; sus vecinos enemigos son c (vecino de b)
    e = estado(LINEA, {"b": "a"})
    assert territorio(e, "a") == ["a", "b"]
    assert vecinos_enemigos(e, "a") == ["c"]  # b ya no es enemigo; c toca con b
    assert duenos_vivos(e) == ["a", "c", "d"]


def test_no_se_cuentan_como_enemigos_los_propios_concellos():
    e = estado(LINEA, {"b": "a", "c": "a"})
    assert vecinos_enemigos(e, "a") == ["d"]


# --- El defensor siempre es colindante y de otro dueño ---


def test_el_defensor_siempre_es_colindante_y_de_otro_dueno():
    e = estado(LINEA, {"b": "a"})
    rng = random.Random(1)
    for _ in range(500):
        f = elegir_enfrentamiento(e, rng)
        assert f.atacante != f.defensor
        assert e["concellos"][f.concello_defensor]["dono"] == f.defensor
        assert e["concellos"][f.concello_atacante]["dono"] == f.atacante
        assert f.concello_defensor in e["concellos"][f.concello_atacante]["vecinos"]


def test_el_concello_atacante_es_uno_de_los_que_tocan_al_defensor():
    # El dueño «a» tiene a, b y e; solo b y e tocan al concello c
    grafo = {"a": ["x"], "b": ["c"], "c": ["b", "e"], "e": ["c"], "x": ["a"]}
    e = estado(grafo, {"b": "a", "e": "a"})
    rng = random.Random(3)
    vistos = set()
    for _ in range(200):
        d = elegir_defensor(e, "a", rng)
        if d == "c":
            f = elegir_enfrentamiento(e, random.Random(len(vistos)))
            vistos.add((f.atacante, f.concello_atacante, f.concello_defensor))
    # cuando «a» ataca a «c», el concello que lo toca es b o e, nunca a
    assert all(ca in ("b", "e") for at, ca, cd in vistos if at == "a" and cd == "c")


# --- Nunca se elige un atacante sin vecinos enemigos ---


def test_un_dueno_sin_vecinos_enemigos_nunca_ataca():
    # «z» está aislado (sin vecinos): nunca puede ser atacante
    grafo = {**LINEA, "z": []}
    e = estado(grafo)
    rng = random.Random(5)
    atacantes = {elegir_atacante(e, rng) for _ in range(500)}
    assert "z" not in atacantes
    assert atacantes == {"a", "b", "c", "d"}


def test_dueno_cuyos_vecinos_son_todos_propios_no_ataca():
    # a, b, c, d: todo del mismo dueño salvo d. El dueño «a» solo tiene a d como enemigo.
    e = estado(LINEA, {"b": "a", "c": "a"})
    assert vecinos_enemigos(e, "a") == ["d"]


def test_partida_terminada_si_queda_un_unico_dueno():
    e = estado(LINEA, {"b": "a", "c": "a", "d": "a"})
    assert duenos_vivos(e) == ["a"]
    with pytest.raises(NoHayEnfrentamiento):
        elegir_atacante(e, random.Random(0))
    with pytest.raises(NoHayEnfrentamiento):
        elegir_enfrentamiento(e, random.Random(0))


def test_elegir_defensor_sin_enemigos_falla():
    e = estado(LINEA, {"b": "a", "c": "a", "d": "a"})
    with pytest.raises(NoHayEnfrentamiento):
        elegir_defensor(e, "a", random.Random(0))


# --- Equiprobabilidad entre dueños (sin importar su tamaño) ---


def test_cada_dueno_ataca_con_la_misma_probabilidad_sea_grande_o_pequeno():
    # «g» posee 3 concellos y «p» solo uno; ambos tienen enemigos
    grafo = {"g1": ["g2", "p"], "g2": ["g1", "g3"], "g3": ["g2", "q"], "p": ["g1"], "q": ["g3"]}
    e = estado(grafo, {"g2": "g1", "g3": "g1"})
    rng = random.Random(11)
    cuentas = collections.Counter(elegir_atacante(e, rng) for _ in range(30000))
    assert set(cuentas) == {"g1", "p", "q"}
    for d in cuentas:
        assert cuentas[d] / 30000 == pytest.approx(1 / 3, abs=0.02)


def test_el_defensor_se_elige_entre_todos_los_vecinos_enemigos_por_igual():
    # «a» tiene tres vecinos enemigos
    grafo = {"a": ["x", "y", "z"], "x": ["a"], "y": ["a"], "z": ["a"]}
    e = estado(grafo)
    rng = random.Random(13)
    cuentas = collections.Counter(elegir_defensor(e, "a", rng) for _ in range(30000))
    for d in ("x", "y", "z"):
        assert cuentas[d] / 30000 == pytest.approx(1 / 3, abs=0.02)


# --- Reproducibilidad ---


def test_misma_semilla_mismo_enfrentamiento():
    e = estado(LINEA)
    seq = lambda s: [elegir_enfrentamiento(e, random.Random(s)) for _ in range(1)]  # noqa: E731
    assert seq(7) == seq(7)
    rng1, rng2 = random.Random(9), random.Random(9)
    assert [elegir_enfrentamiento(e, rng1) for _ in range(20)] == [
        elegir_enfrentamiento(e, rng2) for _ in range(20)
    ]


def test_no_depende_del_orden_del_diccionario():
    e1 = estado(LINEA)
    e2 = {"concellos": dict(reversed(list(e1["concellos"].items())))}
    r1, r2 = random.Random(21), random.Random(21)
    assert [elegir_enfrentamiento(e1, r1) for _ in range(20)] == [
        elegir_enfrentamiento(e2, r2) for _ in range(20)
    ]


# --- Con los datos reales de Galicia ---


@pytest.fixture(scope="module")
def real():
    return json.loads(ESTADO_INICIAL.read_text(encoding="utf-8"))


def test_el_mapa_de_galicia_es_conexo(real):
    """Si no fuera conexo, la partida no podría terminar con un único dueño."""
    c = real["concellos"]
    visto, pendientes = set(), [next(iter(c))]
    while pendientes:
        i = pendientes.pop()
        if i not in visto:
            visto.add(i)
            pendientes.extend(c[i]["vecinos"])
    assert visto == set(c)


def test_al_empezar_todos_los_duenos_tienen_enemigos(real):
    assert all(vecinos_enemigos(real, d) for d in duenos_vivos(real))


def test_miles_de_enfrentamientos_reales_son_validos(real):
    rng = random.Random(2026)
    c = real["concellos"]
    for _ in range(5000):
        f = elegir_enfrentamiento(real, rng)
        assert f.atacante != f.defensor
        assert f.concello_defensor in c[f.concello_atacante]["vecinos"]
        assert c[f.concello_defensor]["dono"] == f.defensor
