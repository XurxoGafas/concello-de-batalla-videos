"""Tests del paso 2.2: adyacencias y geometría simplificada."""

import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import box

from src.datos.geometria import N_CONCELLOS, calcular_adyacencias

PROCESADO = Path(__file__).resolve().parent.parent / "data" / "processed"


@pytest.fixture(scope="module")
def datos():
    g = gpd.read_file(PROCESADO / "concellos.geojson")
    ady = json.loads((PROCESADO / "adyacencias.json").read_text(encoding="utf-8"))
    nombre_a_id = dict(zip(g["nome"], g["id"]))
    return g, ady, nombre_a_id


def son_vecinos(datos, a, b):
    _, ady, ids = datos
    return ids[b] in ady[ids[a]]


# --- Lógica de vecindad sobre geometrías sintéticas (no dependen de los datos) ---


def _cuadrados(**cajas):
    return gpd.GeoDataFrame({"id": list(cajas), "geometry": list(cajas.values())})


def test_comparten_linea_son_vecinos():
    g = _cuadrados(a=box(0, 0, 1, 1), b=box(1, 0, 2, 1))
    assert calcular_adyacencias(g) == {"a": ["b"], "b": ["a"]}


def test_solo_una_esquina_tambien_son_vecinos():
    g = _cuadrados(a=box(0, 0, 1, 1), b=box(1, 1, 2, 2))
    assert calcular_adyacencias(g) == {"a": ["b"], "b": ["a"]}


def test_separados_no_son_vecinos():
    g = _cuadrados(a=box(0, 0, 1, 1), b=box(1.1, 0, 2, 1))
    assert calcular_adyacencias(g) == {"a": [], "b": []}


def test_vecindad_manual_es_simetrica():
    g = _cuadrados(a=box(0, 0, 1, 1), b=box(5, 5, 6, 6))
    assert calcular_adyacencias(g, [("a", "b")]) == {"a": ["b"], "b": ["a"]}


def test_vecindad_manual_con_id_desconocido_falla():
    g = _cuadrados(a=box(0, 0, 1, 1))
    with pytest.raises(ValueError):
        calcular_adyacencias(g, [("a", "z")])


# --- Datos reales de Galicia ---


def test_hay_313_concellos(datos):
    g, ady, _ = datos
    assert len(g) == N_CONCELLOS == len(ady)


@pytest.mark.parametrize(
    "a,b",
    [("Ordes", "Cerceda"), ("Arteixo", "A Coruña"), ("Vigo", "Redondela")],
)
def test_parejas_vecinas_conocidas(datos, a, b):
    assert son_vecinos(datos, a, b)


@pytest.mark.parametrize(
    "a,b",
    [("Ordes", "Vigo"), ("A Coruña", "Ourense"), ("Lugo", "Pontevedra")],
)
def test_parejas_no_vecinas_conocidas(datos, a, b):
    assert not son_vecinos(datos, a, b)


def test_pareja_que_solo_toca_en_un_punto_es_vecina(datos):
    # Moraña y Pontevedra solo coinciden en una esquina (regla del usuario: vale)
    assert son_vecinos(datos, "Moraña", "Pontevedra")


def test_isla_conectada_a_mano(datos):
    assert son_vecinos(datos, "A Illa de Arousa", "Vilanova de Arousa")


def test_todo_concello_tiene_al_menos_un_vecino(datos):
    _, ady, _ = datos
    assert all(len(v) >= 1 for v in ady.values())


def test_relacion_simetrica_y_sin_autovecinos(datos):
    _, ady, _ = datos
    for i, vecinos in ady.items():
        assert i not in vecinos
        for j in vecinos:
            assert i in ady[j]


def test_ids_de_adyacencias_coinciden_con_geometrias(datos):
    g, ady, _ = datos
    assert set(g["id"]) == set(ady)
    assert all(j in set(g["id"]) for v in ady.values() for j in v)


def test_geometrias_simplificadas_validas(datos):
    g, _, _ = datos
    assert g.is_valid.all() and not g.is_empty.any()
