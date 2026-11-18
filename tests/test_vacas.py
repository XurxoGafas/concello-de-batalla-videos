"""Tests del paso 2.3: censo de vacas por concello."""

import json
from pathlib import Path

import pytest

from src.datos.vacas import construir

PROCESADO = Path(__file__).resolve().parent.parent / "data" / "processed"
V = "Número de vacas"


def fila(codigo, dato, anio="2025"):
    return [V, anio, anio, codigo, f"{codigo} X", dato, dato]


# --- Lógica con datos sintéticos (ids IGN = 6 dígitos de prefijo + código INE) ---

IDS = ["34121511111", "34121522222", "34121533333"]


def filas_ok():
    return [
        fila("11111", "10"),
        fila("22222", "0"),
        fila("33333", "5"),
        fila("12", "15"),  # total oficial de Galicia
    ]


def test_cero_vacas_se_convierte_en_una():
    r = construir(IDS, filas_ok(), "2025")
    assert r["vacas"] == {"34121511111": 10, "34121522222": 1, "34121533333": 5}
    assert r["ajustados_cero_a_uno"] == ["34121522222"]


def test_dato_que_falta_no_se_inventa():
    filas = [fila("11111", "10"), fila("22222", ""), fila("33333", "5"), fila("12", "15")]
    with pytest.raises(ValueError, match="sin dato"):
        construir(IDS, filas, "2025")


def test_total_que_no_cuadra_falla():
    filas = filas_ok()[:-1] + [fila("12", "99")]
    with pytest.raises(ValueError, match="no cuadra"):
        construir(IDS, filas, "2025")


def test_ignora_otros_anios_y_codigos_no_municipales():
    filas = filas_ok() + [fila("11111", "777", anio="2024"), fila("1501", "9")]
    assert construir(IDS, filas, "2025")["vacas"]["34121511111"] == 10


# --- Datos reales ---


@pytest.fixture(scope="module")
def datos():
    vacas = json.loads((PROCESADO / "vacas.json").read_text(encoding="utf-8"))
    g = json.loads((PROCESADO / "concellos.geojson").read_text(encoding="utf-8"))
    nombres = {f["properties"]["id"]: f["properties"]["nome"] for f in g["features"]}
    return vacas, nombres


def test_todos_los_concellos_tienen_vacas_mayor_o_igual_a_1(datos):
    vacas, nombres = datos
    assert set(vacas["vacas"]) == set(nombres)
    assert len(vacas["vacas"]) == 313
    assert all(isinstance(n, int) and n >= 1 for n in vacas["vacas"].values())


def test_el_total_cuadra_con_el_oficial_mas_los_ajustes(datos):
    vacas, _ = datos
    total = sum(vacas["vacas"].values())
    assert total == vacas["total_oficial_galicia"] + len(vacas["ajustados_cero_a_uno"])


def test_concellos_ajustados_son_los_de_cero_vacas(datos):
    vacas, nombres = datos
    ajustados = {nombres[i] for i in vacas["ajustados_cero_a_uno"]}
    assert "A Illa de Arousa" in ajustados
    assert all(vacas["vacas"][i] == 1 for i in vacas["ajustados_cero_a_uno"])
