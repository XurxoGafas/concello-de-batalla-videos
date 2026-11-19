"""Tests del paso 4.7: población por concello (solo para elegir al protagonista de la portada)."""

import pytest

from src.datos import poblacion as P

IDS = ["34121511111", "34121522222"]


def fila(codigo, dato, anio="2025"):
    return [anio, anio, "Total", "Total", codigo, f"{codigo} X", dato, dato]


def test_une_por_codigo_ine_y_cuadra_con_galicia():
    filas = [fila("11111", "100"), fila("22222", "50"), fila("12", "150"), fila("11111", "1", "2024")]
    r = P.construir(IDS, filas, "2025")
    assert r["poboacion"] == {IDS[0]: 100, IDS[1]: 50} and r["anio"] == 2025


def test_el_dato_que_falta_no_se_inventa():
    with pytest.raises(ValueError, match="sin dato"):
        P.construir(IDS, [fila("11111", "100"), fila("22222", ""), fila("12", "100")], "2025")


def test_total_que_no_cuadra_falla():
    with pytest.raises(ValueError, match="no cuadra"):
        P.construir(IDS, [fila("11111", "100"), fila("22222", "50"), fila("12", "999")], "2025")


def test_datos_reales():
    h = P.cargar()
    assert len(h) == 313 and min(h.values()) > 0
    assert sum(h.values()) == 2_714_741
    est_nombres = {i: n for i, n in __import__("json").load(open(P.RAIZ / "data/processed/estado_inicial.json"))["donos"].items()}
    mayor = max(h, key=h.get)
    assert est_nombres[mayor]["nome"] == "Vigo"
