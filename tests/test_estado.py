"""Tests del paso 3.4: conquista y actualización del estado."""

import copy
import json
import random
from pathlib import Path

import pytest

from src.motor.estado import (
    aplicar_conquista,
    color_de_concello,
    ganador_de_la_serie,
    jugar_batalla,
    partida_terminada,
)
from src.motor.seleccion import NoHayEnfrentamiento
from src.motor.multiplicador import vacas_de_dono

INICIAL = Path(__file__).resolve().parent.parent / "data" / "processed" / "estado_inicial.json"


def sintetico() -> dict:
    """a — b — c — d en línea, con vacas y colores distintos."""
    grafo = {"a": ["b"], "b": ["a", "c"], "c": ["b", "d"], "d": ["c"]}
    vacas = {"a": 10, "b": 20, "c": 30, "d": 40}
    return {
        "version": 1,
        "episodio": 0,
        "concellos": {
            i: {"nome": i.upper(), "vecinos": v, "vacas": vacas[i], "dono": i,
                "cor": {"colores": [f"#00000{n}"], "pesos": [1.0]}}
            for n, (i, v) in enumerate(grafo.items())
        },
        "donos": {
            i: {"nome": i.upper(), "territorio": [i], "vacas": vacas[i], "victorias": 0,
                "cor": {"colores": [f"#00000{n}"], "pesos": [1.0]}}
            for n, i in enumerate(grafo)
        },
    }


def coherente(e: dict) -> None:
    """Invariantes: cada concello pertenece a un dueño vivo y los totales cuadran."""
    todos = [i for d in e["donos"].values() for i in d["territorio"]]
    assert sorted(todos) == sorted(e["concellos"])  # sin repetidos ni huérfanos
    for d, datos in e["donos"].items():
        assert datos["territorio"]
        assert all(e["concellos"][i]["dono"] == d for i in datos["territorio"])
        assert datos["vacas"] == vacas_de_dono(e["concellos"], d)


# --- Conquista ---


def test_el_ganador_absorbe_territorio_y_vacas():
    e = sintetico()
    n = aplicar_conquista(e, "c", "b")
    assert n["donos"]["c"]["territorio"] == ["b", "c"]
    assert n["donos"]["c"]["vacas"] == 50
    assert "b" not in n["donos"]
    assert n["concellos"]["b"]["dono"] == "c"
    coherente(n)


def test_gana_el_atacante_o_el_defensor_conquista_igual():
    e = sintetico()
    assert "a" not in aplicar_conquista(e, "b", "a")["donos"]
    assert "b" not in aplicar_conquista(e, "a", "b")["donos"]


def test_se_absorbe_todo_el_territorio_del_perdedor_no_solo_el_concello_atacado():
    e = aplicar_conquista(sintetico(), "b", "a")  # b = {a, b}
    n = aplicar_conquista(e, "c", "b")
    assert n["donos"]["c"]["territorio"] == ["a", "b", "c"]
    assert n["donos"]["c"]["vacas"] == 60
    coherente(n)


def test_el_territorio_conquistado_se_pinta_con_el_color_del_ganador():
    e = sintetico()
    n = aplicar_conquista(e, "c", "b")
    assert color_de_concello(n, "b") == e["donos"]["c"]["cor"]
    assert color_de_concello(n, "c") == e["donos"]["c"]["cor"]
    assert color_de_concello(n, "a") == e["donos"]["a"]["cor"]  # sin tocar


def test_victorias_suma_una_y_no_hereda_las_del_perdedor():
    e = sintetico()
    e["donos"]["c"]["victorias"] = 2
    e["donos"]["b"]["victorias"] = 10  # el perdedor tenía 10: no pasan al ganador
    n = aplicar_conquista(e, "c", "b")
    assert n["donos"]["c"]["victorias"] == 3
    assert n["donos"]["a"]["victorias"] == 0


def test_ganar_a_un_dueno_con_muchas_victorias_solo_cuenta_una():
    """Ejemplo del usuario: si O Porriño gana a Ordes (10 victorias), O Porriño tiene 1."""
    e = sintetico()
    e["donos"]["b"]["victorias"] = 10
    n = aplicar_conquista(e, "a", "b")
    assert n["donos"]["a"]["victorias"] == 1


def test_no_modifica_el_estado_original():
    e = sintetico()
    copia = copy.deepcopy(e)
    aplicar_conquista(e, "c", "b")
    assert e == copia


def test_conquistas_invalidas_fallan():
    e = sintetico()
    with pytest.raises(ValueError):
        aplicar_conquista(e, "a", "a")
    with pytest.raises(KeyError):
        aplicar_conquista(e, "a", "zzz")
    n = aplicar_conquista(e, "c", "b")
    with pytest.raises(KeyError):  # b ya fue eliminado
        aplicar_conquista(n, "c", "b")


def test_fin_de_partida_con_un_unico_dueno():
    e = sintetico()
    assert not partida_terminada(e) and ganador_de_la_serie(e) is None
    for g, p in (("b", "a"), ("c", "b"), ("d", "c")):
        e = aplicar_conquista(e, g, p)
    assert partida_terminada(e)
    assert ganador_de_la_serie(e) == "d"
    assert e["donos"]["d"]["vacas"] == 100
    coherente(e)


def test_no_se_puede_jugar_con_la_partida_terminada():
    e = sintetico()
    for g, p in (("b", "a"), ("c", "b"), ("d", "c")):
        e = aplicar_conquista(e, g, p)
    with pytest.raises(NoHayEnfrentamiento):
        jugar_batalla(e, random.Random(0))


# --- jugar_batalla ---


def test_jugar_batalla_aplica_el_resultado_del_dado():
    e = sintetico()
    rng = random.Random(3)
    n, ep = jugar_batalla(e, rng)
    assert ep.ganador in (ep.enfrentamiento.atacante, ep.enfrentamiento.defensor)
    assert {ep.ganador, ep.perdedor} == {ep.enfrentamiento.atacante, ep.enfrentamiento.defensor}
    assert (ep.resultado.ganador == "a") == (ep.ganador == ep.enfrentamiento.atacante)
    assert ep.perdedor not in n["donos"]
    assert ep.vacas_atacante == e["donos"][ep.enfrentamiento.atacante]["vacas"]
    coherente(n)


def test_las_vacas_del_combate_son_las_de_todo_el_territorio():
    e = aplicar_conquista(sintetico(), "b", "a")  # b = {a,b} con 30 vacas
    _, ep = jugar_batalla(e, random.Random(1))
    for dueno, vacas in ((ep.enfrentamiento.atacante, ep.vacas_atacante),
                         (ep.enfrentamiento.defensor, ep.vacas_defensor)):
        assert vacas == vacas_de_dono(e["concellos"], dueno)


# --- Simulaciones completas ---


def simular(estado: dict, semilla: int):
    rng = random.Random(semilla)
    historial = []
    while not partida_terminada(estado):
        antes = sum(d["vacas"] for d in estado["donos"].values())
        estado, ep = jugar_batalla(estado, rng)
        assert sum(d["vacas"] for d in estado["donos"].values()) == antes  # se conservan
        historial.append((ep.ganador, ep.perdedor))
    return estado, historial


def test_simulacion_sintetica_termina_con_un_unico_ganador():
    for semilla in range(50):
        e, hist = simular(sintetico(), semilla)
        assert len(hist) == 3  # n dueños → n−1 batallas
        assert len(e["donos"]) == 1
        coherente(e)


def test_misma_semilla_misma_serie():
    assert simular(sintetico(), 8)[1] == simular(sintetico(), 8)[1]
    series = {tuple(simular(sintetico(), s)[1]) for s in range(30)}
    assert len(series) > 1  # semillas distintas dan series distintas


@pytest.fixture(scope="module")
def real():
    return json.loads(INICIAL.read_text(encoding="utf-8"))


def test_simulacion_completa_de_galicia_con_semilla_fija(real):
    total = sum(c["vacas"] for c in real["concellos"].values())
    e, hist = simular(real, 42)
    assert len(hist) == 312  # 313 dueños → 312 conquistas
    assert len(e["donos"]) == 1
    unico = ganador_de_la_serie(e)
    assert len(e["donos"][unico]["territorio"]) == 313
    assert e["donos"][unico]["vacas"] == total
    # solo cuentan las batallas ganadas por el propio dueño (no se heredan)
    propias = sum(1 for g, _ in hist if g == unico)
    assert e["donos"][unico]["victorias"] == propias
    assert 1 <= propias <= 312
    assert all(c["dono"] == unico for c in e["concellos"].values())
    coherente(e)
    # reproducible
    assert simular(real, 42)[1] == hist
    # el estado inicial no se ha tocado
    assert len(real["donos"]) == 313 and real["episodio"] == 0
