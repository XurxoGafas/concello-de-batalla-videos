"""Tests del estado inicial del juego (paso 2.4)."""

import json
from pathlib import Path

import pytest

from src.datos.construir_estado import color_provisional, construir

PROC = Path(__file__).resolve().parent.parent / "data" / "processed"


def datos_sinteticos():
    nombres = {"a": ("Alfa", "Lugo"), "b": ("Beta", "Lugo"), "c": ("Gamma", "Ourense")}
    vecinos = {"a": ["b"], "b": ["a", "c"], "c": ["b"]}
    vacas = {"a": 10, "b": 20, "c": 1}
    colores = {"a": {"colores": ["#003399", "#ffcc00"], "pesos": [0.7, 0.3]}}
    return nombres, vecinos, vacas, colores


def test_cada_concello_es_su_propio_dueno():
    e = construir(*datos_sinteticos())
    assert all(c["dono"] == i for i, c in e["concellos"].items())
    assert e["donos"]["b"]["territorio"] == ["b"]
    assert e["donos"]["b"]["vacas"] == 20


def test_contador_de_victorias_a_cero_y_episodio_cero():
    e = construir(*datos_sinteticos())
    assert e["episodio"] == 0
    assert all(d["victorias"] == 0 for d in e["donos"].values())


def test_color_de_bandera_y_provisional_se_distinguen():
    e = construir(*datos_sinteticos())
    assert e["concellos"]["a"]["cor"]["fonte"] == "bandeira"
    assert e["concellos"]["a"]["cor"]["colores"] == ["#003399", "#ffcc00"]
    assert e["concellos"]["b"]["cor"]["fonte"] == "provisional"


def test_ids_incoherentes_fallan():
    nombres, vecinos, vacas, colores = datos_sinteticos()
    del vacas["c"]
    with pytest.raises(ValueError):
        construir(nombres, vecinos, vacas, colores)


def test_colores_provisionales_distintos():
    assert len({color_provisional(n) for n in range(313)}) == 313


@pytest.fixture(scope="module")
def estado():
    return json.loads((PROC / "estado_inicial.json").read_text(encoding="utf-8"))


def test_estado_real_coherente_con_los_demas_datos(estado):
    g = json.loads((PROC / "concellos.geojson").read_text(encoding="utf-8"))["features"]
    ids = {f["properties"]["id"] for f in g}
    ady = json.loads((PROC / "adyacencias.json").read_text(encoding="utf-8"))
    vacas = json.loads((PROC / "vacas.json").read_text(encoding="utf-8"))["vacas"]
    assert set(estado["concellos"]) == set(estado["donos"]) == ids == set(ady) == set(vacas)
    for i, c in estado["concellos"].items():
        assert c["vecinos"] == ady[i]
        assert c["vacas"] == vacas[i] >= 1
        assert c["dono"] == i
        assert estado["donos"][i]["victorias"] == 0
        assert c["cor"]["colores"] and len(c["cor"]["colores"]) == len(c["cor"]["pesos"])


def test_vecinos_del_estado_son_simetricos(estado):
    for i, c in estado["concellos"].items():
        assert all(i in estado["concellos"][j]["vecinos"] for j in c["vecinos"])
