"""Tests del paso 3.6: simulación por consola."""

import io
import subprocess
import sys
from pathlib import Path

import pytest

from src.cli import _dec, _num, main, simular

RAIZ = Path(__file__).resolve().parent.parent


def ejecutar(*args: str) -> str:
    r = subprocess.run(
        [sys.executable, "-m", "src.cli", *args],
        capture_output=True, text=True, encoding="utf-8", cwd=RAIZ, check=True,
    )
    return r.stdout


def test_comando_del_plan_imprime_10_batallas_legibles():
    salida = ejecutar("simular", "--batallas", "10", "--semilla", "42")
    for n in range(1, 11):
        assert f"Batalla {n}:" in salida
    assert "Batalla 11:" not in salida
    assert salida.count("GANA ") == 10
    assert salida.count("Tirada 1:") == salida.count("Tirada 3:") == 10
    assert "Puntuación final:" in salida


def test_misma_semilla_misma_salida_y_otra_semilla_otra_salida():
    a = ejecutar("simular", "--batallas", "10", "--semilla", "42")
    assert a == ejecutar("simular", "--batallas", "10", "--semilla", "42")
    assert a != ejecutar("simular", "--batallas", "10", "--semilla", "43")


def test_las_primeras_batallas_no_dependen_de_cuantas_se_pidan():
    cinco = ejecutar("simular", "--batallas", "5", "--semilla", "7")
    diez = ejecutar("simular", "--batallas", "10", "--semilla", "7")
    assert diez.startswith(cinco)


def test_no_guarda_nada_en_la_partida():
    antes = sorted(p.name for p in (RAIZ / "data" / "partida").iterdir())
    ejecutar("simular", "--batallas", "3", "--semilla", "1")
    assert sorted(p.name for p in (RAIZ / "data" / "partida").iterdir()) == antes


def test_simulacion_completa_termina_con_ganador():
    buf = io.StringIO()
    jugadas = simular(400, "fin", buf)
    assert jugadas == 312
    assert "La partida ha terminado: gana" in buf.getvalue()
    assert "quedan 1 dueños" in buf.getvalue()


def test_argumentos_invalidos_fallan():
    with pytest.raises(SystemExit):
        main(["simular", "--batallas", "0", "--semilla", "1"])
    with pytest.raises(SystemExit):
        main(["simular", "--batallas", "3"])  # falta la semilla
    with pytest.raises(SystemExit):
        main([])


def test_formato_de_numeros():
    assert _num(1234567) == "1.234.567" and _num(85) == "85"
    assert _dec(5.0) == "5" and _dec(10.5) == "10,5" and _dec(0.0) == "0"
