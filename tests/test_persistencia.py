"""Tests del paso 3.5: persistencia de la partida entre ejecuciones."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.motor.estado import partida_terminada
from src.motor.persistencia import (
    VARIABLE_SEMILLA,
    anadir_al_historial,
    cargar_estado,
    guardar_estado,
    jugar_episodio,
    jugar_y_guardar,
    leer_historial,
    nueva_partida,
    semilla_de_batalla,
    semilla_de_serie_desde_entorno,
)
from src.motor.seleccion import NoHayEnfrentamiento

RAIZ = Path(__file__).resolve().parent.parent
SERIE = "serie-de-prueba"


def sintetico() -> dict:
    grafo = {"a": ["b"], "b": ["a", "c"], "c": ["b", "d"], "d": ["c"]}
    vacas = {"a": 10, "b": 20, "c": 30, "d": 40}
    cor = {"colores": ["#000000"], "pesos": [1.0]}
    return {
        "version": 1,
        "episodio": 0,
        "concellos": {i: {"nome": i, "vecinos": v, "vacas": vacas[i], "dono": i, "cor": cor}
                      for i, v in grafo.items()},
        "donos": {i: {"nome": i, "territorio": [i], "vacas": vacas[i], "victorias": 0, "cor": cor}
                  for i in grafo},
        "batallas_jugadas": 0,
    }


def nucleo(e: dict) -> dict:
    """Lo que debe coincidir entre ejecuciones (el número de episodio depende de cómo se agrupe)."""
    return {k: e[k] for k in ("concellos", "donos", "batallas_jugadas")}


# --- Semillas ---


def test_semilla_de_batalla_es_estable_y_distinta_por_batalla_y_serie():
    # Valor fijado a mano: si cambia, se rompe la reproducibilidad de todas las series.
    assert semilla_de_batalla("x", 1) == semilla_de_batalla("x", 1)
    assert semilla_de_batalla("x", 1) != semilla_de_batalla("x", 2)
    assert semilla_de_batalla("x", 1) != semilla_de_batalla("y", 1)
    assert 0 <= semilla_de_batalla("x", 1) < 2**64
    assert semilla_de_batalla("x", 1) == 826551786981313646


def test_sin_semilla_de_serie_en_el_entorno_falla(monkeypatch):
    monkeypatch.delenv(VARIABLE_SEMILLA, raising=False)
    with pytest.raises(RuntimeError, match=VARIABLE_SEMILLA):
        semilla_de_serie_desde_entorno()
    monkeypatch.setenv(VARIABLE_SEMILLA, "  ")
    with pytest.raises(RuntimeError):
        semilla_de_serie_desde_entorno()
    monkeypatch.setenv(VARIABLE_SEMILLA, "abc")
    assert semilla_de_serie_desde_entorno() == "abc"


# --- Episodios ---


def test_un_episodio_juega_tres_batallas_y_avanza_el_numero():
    e = sintetico()
    n, regs = jugar_episodio(e, SERIE)
    assert len(regs) == 3
    assert n["episodio"] == 1 and n["batallas_jugadas"] == 3
    assert [r["batalla"] for r in regs] == [1, 2, 3]
    assert all(r["episodio"] == 1 for r in regs)
    assert e["episodio"] == 0 and e["batallas_jugadas"] == 0  # original intacto


def test_el_episodio_se_detiene_si_la_partida_termina():
    n, regs = jugar_episodio(sintetico(), SERIE, n_batallas=10)
    assert len(regs) == 3  # 4 dueños → 3 batallas
    assert partida_terminada(n)
    with pytest.raises(NoHayEnfrentamiento):
        jugar_episodio(n, SERIE)


def test_el_registro_guarda_la_semilla_y_todos_los_dados():
    _, regs = jugar_episodio(sintetico(), SERIE, n_batallas=1)
    r = regs[0]
    assert r["semilla"] == semilla_de_batalla(SERIE, 1) == r["resultado"]["semilla"]
    assert len(r["resultado"]["tiradas"]) == 3
    assert r["ganador"] != r["perdedor"]
    json.dumps(r)  # serializable


def test_repetir_con_la_misma_serie_da_lo_mismo_y_otra_serie_da_otra_cosa():
    a = jugar_episodio(sintetico(), SERIE)
    assert a == jugar_episodio(sintetico(), SERIE)
    distintos = {json.dumps(jugar_episodio(sintetico(), f"s{i}")[1], sort_keys=True)
                 for i in range(20)}
    assert len(distintos) > 1


def test_una_batalla_del_historial_se_puede_repetir_con_su_semilla():
    from src.motor.batalla import simular_batalla
    import random

    e = sintetico()
    n, regs = jugar_episodio(e, SERIE, n_batallas=1)
    r = regs[0]
    rng = random.Random(r["semilla"])
    # reproducir selección + dados desde cero, igual que jugar_batalla
    from src.motor.seleccion import elegir_enfrentamiento

    f = elegir_enfrentamiento(e, rng)
    res = simular_batalla(r["vacas_atacante"], r["vacas_defensor"], rng=rng)
    assert (f.atacante, f.defensor) == (r["atacante"], r["defensor"])
    assert res.decimas_a == r["resultado"]["decimas_a"]
    assert res.decimas_b == r["resultado"]["decimas_b"]


# --- Archivos ---


def test_guardar_y_cargar_es_identico(tmp_path):
    e = sintetico()
    ruta = tmp_path / "p" / "estado.json"
    guardar_estado(e, ruta)
    assert cargar_estado(ruta) == e
    assert not (tmp_path / "p" / "estado.json.tmp").exists()
    # formato estable: guardar dos veces da el mismo texto
    t1 = ruta.read_text(encoding="utf-8")
    guardar_estado(cargar_estado(ruta), ruta)
    assert ruta.read_text(encoding="utf-8") == t1


def test_historial_se_va_anadiendo_sin_borrar(tmp_path):
    ruta = tmp_path / "h.jsonl"
    anadir_al_historial([{"batalla": 1}, {"batalla": 2}], ruta)
    anadir_al_historial([{"batalla": 3}], ruta)
    assert [r["batalla"] for r in leer_historial(ruta)] == [1, 2, 3]
    assert leer_historial(tmp_path / "no_existe.jsonl") == []


def test_jugar_y_guardar_continua_donde_se_dejo(tmp_path):
    est, hist = tmp_path / "e.json", tmp_path / "h.jsonl"
    guardar_estado(sintetico(), est)
    jugar_y_guardar(SERIE, 1, est, hist)
    jugar_y_guardar(SERIE, 1, est, hist)
    regs = leer_historial(hist)
    assert [r["batalla"] for r in regs] == [1, 2]
    assert [r["episodio"] for r in regs] == [1, 2]
    assert cargar_estado(est)["batallas_jugadas"] == 2


# --- Hecho cuando: 5 batallas en 5 procesos = 5 batallas en un proceso ---

CODIGO_UN_PROCESO = """
import sys
from pathlib import Path
from src.motor.persistencia import jugar_y_guardar, nueva_partida, guardar_estado
est, hist, serie = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
if not est.exists():
    guardar_estado(nueva_partida(), est)
jugar_y_guardar(serie, 1, est, hist)
"""


def test_cinco_batallas_en_cinco_procesos_igual_que_en_uno(tmp_path):
    est5, hist5 = tmp_path / "e5.json", tmp_path / "h5.jsonl"
    for _ in range(5):
        subprocess.run(
            [sys.executable, "-I", "-c", "import sys; sys.path.insert(0, %r)\n" % str(RAIZ)
             + CODIGO_UN_PROCESO, str(est5), str(hist5), SERIE],
            check=True, cwd=RAIZ,
        )
    e5, regs5 = cargar_estado(est5), leer_historial(hist5)

    # un solo proceso: las mismas 5 batallas seguidas
    uno, regs1 = jugar_episodio(nueva_partida(), SERIE, n_batallas=5)

    assert nucleo(e5) == nucleo(uno)
    assert e5["batallas_jugadas"] == 5 and e5["episodio"] == 5
    # (los registros de un proceso pasan por JSON: se comparan igual tras ese viaje)
    regs1 = [json.loads(json.dumps(r)) for r in regs1]
    assert [{k: v for k, v in r.items() if k != "episodio"} for r in regs5] == \
           [{k: v for k, v in r.items() if k != "episodio"} for r in regs1]

    # contador de victorias correcto: cada dueño vivo solo tiene las que ganó él mismo
    ganadas = {}
    for r in regs5:
        ganadas[r["ganador"]] = ganadas.get(r["ganador"], 0) + 1
    for d, datos in e5["donos"].items():
        assert datos["victorias"] == ganadas.get(d, 0)
    assert sum(d["victorias"] for d in e5["donos"].values()) <= 5
    assert len(e5["donos"]) == 313 - 5
