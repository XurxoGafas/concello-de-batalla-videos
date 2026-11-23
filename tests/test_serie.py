"""Tests del guardado de la serie (`src/render/serie.py`): el resultado de un episodio queda registrado."""

import json

import pytest

from src.motor.persistencia import cargar_estado, leer_historial, nueva_partida
from src.render import escenas as ES
from src.render import serie as SE
from src.render.mapa import MapaGalicia


@pytest.fixture(scope="module")
def montaje():
    return ES.construir_episodio(nueva_partida(), "prueba-serie", MapaGalicia())


def _rutas(tmp_path):
    return dict(ruta_estado=tmp_path / "estado.json", ruta_historial=tmp_path / "historial.jsonl",
                carpeta_estados=tmp_path / "episodios", ruta_resumen=tmp_path / "EPISODIOS.md",
                ruta_portadas=tmp_path / "portadas.jsonl")


def test_registrar_guarda_estado_historial_portada_y_resumen(tmp_path, montaje):
    r = _rutas(tmp_path)
    final = SE.registrar(nueva_partida(), "prueba-serie", montaje, **r)
    assert cargar_estado(r["ruta_estado"]) == final == cargar_estado(r["carpeta_estados"] / "estado_001.json")
    assert final["episodio"] == 1 and final["batallas_jugadas"] == 3
    assert [x["batalla"] for x in leer_historial(r["ruta_historial"])] == [1, 2, 3]
    assert json.loads(r["ruta_portadas"].read_text().splitlines()[0])["episodio"] == 1
    texto = r["ruta_resumen"].read_text(encoding="utf-8")
    assert "## Episodio 1" in texto and texto.count("- Batalla ") == 3


def test_registrar_no_guarda_nada_si_el_montaje_no_corresponde(tmp_path, montaje):
    r = _rutas(tmp_path)
    with pytest.raises(RuntimeError):
        SE.registrar(nueva_partida(), "otra-semilla", montaje, **r)
    assert not r["ruta_estado"].exists() and not r["ruta_historial"].exists() and not r["ruta_resumen"].exists()
