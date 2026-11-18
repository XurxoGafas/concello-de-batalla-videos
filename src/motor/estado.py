"""Conquista y actualización del estado (paso 3.4).

Reglas (ver docs/DECISIONES.md, fase 6 del vídeo):

- Gana quien tenga más puntuación (ya resuelto en `batalla.py`); el ganador conquista siempre
  al perdedor, sea este el atacante o el defensor.
- El ganador absorbe TODO el territorio y TODAS las vacas del perdedor (no solo el concello
  atacado). El dueño perdedor desaparece.
- El territorio conquistado se muestra con el nombre y los colores del ganador: el color
  efectivo de un concello es el de su dueño actual (`color_de_concello`).
- Contador de victorias (para el ranking): el ganador suma 1 por la batalla ganada. Las
  victorias del perdedor NO se heredan: desaparecen con él (decisión del usuario, 2026-11-18).
  Así, un dueño solo cuenta las batallas que ha ganado él mismo.
- La partida termina cuando queda un único dueño.

Todas las funciones devuelven un estado NUEVO; el recibido no se modifica.
"""

from __future__ import annotations

import copy
import random
from dataclasses import dataclass

from src.motor.batalla import ResultadoBatalla, simular_batalla
from src.motor.seleccion import Enfrentamiento, NoHayEnfrentamiento, elegir_enfrentamiento


def partida_terminada(estado: dict) -> bool:
    """True si queda un único dueño con todo el territorio."""
    return len(estado["donos"]) <= 1


def ganador_de_la_serie(estado: dict) -> str | None:
    """Id del dueño único si la partida ha terminado; si no, None."""
    if partida_terminada(estado):
        return next(iter(estado["donos"]))
    return None


def color_de_concello(estado: dict, concello: str) -> dict:
    """Color con el que se pinta un concello: el de su dueño actual (bandera del ganador)."""
    return estado["donos"][estado["concellos"][concello]["dono"]]["cor"]


def aplicar_conquista(estado: dict, ganador: str, perdedor: str) -> dict:
    """Devuelve el estado tras la conquista de `perdedor` por `ganador` (ids de dueños)."""
    if ganador == perdedor:
        raise ValueError("Un dueño no puede conquistarse a sí mismo")
    for d in (ganador, perdedor):
        if d not in estado["donos"]:
            raise KeyError(f"El dueño {d} no existe (o ya fue eliminado)")

    nuevo = copy.deepcopy(estado)
    g, p = nuevo["donos"][ganador], nuevo["donos"][perdedor]

    for i in p["territorio"]:
        nuevo["concellos"][i]["dono"] = ganador
    g["territorio"] = sorted(g["territorio"] + p["territorio"])
    g["vacas"] += p["vacas"]
    g["victorias"] += 1  # las victorias del perdedor no se heredan
    del nuevo["donos"][perdedor]
    return nuevo


@dataclass(frozen=True)
class Episodio:
    """Registro completo de una batalla: lo que necesitarán el render y el audio."""

    enfrentamiento: Enfrentamiento
    resultado: ResultadoBatalla
    ganador: str  # id del dueño que gana
    perdedor: str  # id del dueño que pierde
    vacas_atacante: int
    vacas_defensor: int


def jugar_batalla(estado: dict, rng: random.Random) -> tuple[dict, Episodio]:
    """Sortea un enfrentamiento, lo simula y aplica la conquista.

    Orden de sorteos (parte del contrato de reproducibilidad): primero la selección
    (atacante, concello defensor, concello atacante) y después los dados de la batalla,
    todos del mismo `rng`. Lanza `NoHayEnfrentamiento` si la partida ya había terminado.
    """
    if partida_terminada(estado):
        raise NoHayEnfrentamiento("La partida ya ha terminado: queda un único dueño")
    f = elegir_enfrentamiento(estado, rng)
    vacas_a = estado["donos"][f.atacante]["vacas"]
    vacas_d = estado["donos"][f.defensor]["vacas"]
    r = simular_batalla(vacas_a, vacas_d, rng=rng)
    ganador, perdedor = (f.atacante, f.defensor) if r.ganador == "a" else (f.defensor, f.atacante)
    nuevo = aplicar_conquista(estado, ganador, perdedor)
    return nuevo, Episodio(f, r, ganador, perdedor, vacas_a, vacas_d)
