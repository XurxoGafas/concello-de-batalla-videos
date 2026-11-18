"""Selección de atacante y defensor (paso 3.3).

Reglas (ver docs/DECISIONES.md, fases 2 y 3 del vídeo):

- El atacante se elige al azar entre los dueños vivos, **con la misma probabilidad para cada
  dueño** (sin importar su tamaño), pero solo entre los que tienen al menos un vecino enemigo.
- El defensor es un concello al azar entre los vecinos de TODO el territorio del atacante
  que pertenecen a otro dueño (cada concello vecino con la misma probabilidad).
- Además se elige cuál de los concellos del atacante hace frontera con el defensor, que es el
  que saldrá en pantalla junto al defensor (si solo hay uno, no hay nada que elegir).

La fuente de verdad del dueño de un concello es `estado["concellos"][id]["dono"]`.

Reproducibilidad (regla i): toda la aleatoriedad sale del `random.Random` que se pasa. Orden de
los sorteos (parte del contrato): primero el atacante, luego el concello defensor y por último
el concello atacante que lo toca. Las listas se ordenan por id antes de sortear para que el
resultado no dependa del orden de los diccionarios.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


class NoHayEnfrentamiento(Exception):
    """No queda ningún dueño con vecinos enemigos (la partida ha terminado)."""


@dataclass(frozen=True)
class Enfrentamiento:
    atacante: str  # id del dueño atacante
    defensor: str  # id del dueño defensor (el que posee `concello_defensor`)
    concello_atacante: str  # concello del atacante que hace frontera con el defensor
    concello_defensor: str  # concello atacado


def territorio(estado: dict, dono: str) -> list[str]:
    """Ids de los concellos que posee un dueño, ordenados."""
    return sorted(i for i, c in estado["concellos"].items() if c["dono"] == dono)


def duenos_vivos(estado: dict) -> list[str]:
    """Ids de los dueños que aún tienen territorio, ordenados."""
    return sorted({c["dono"] for c in estado["concellos"].values()})


def vecinos_enemigos(estado: dict, dono: str) -> list[str]:
    """Concellos de otros dueños que hacen frontera con el territorio de `dono`, ordenados."""
    concellos = estado["concellos"]
    enemigos = {
        v
        for i in territorio(estado, dono)
        for v in concellos[i]["vecinos"]
        if concellos[v]["dono"] != dono
    }
    return sorted(enemigos)


def elegir_atacante(estado: dict, rng: random.Random) -> str:
    """Dueño atacante al azar, con la misma probabilidad cada uno, entre los que tienen enemigos."""
    candidatos = [d for d in duenos_vivos(estado) if vecinos_enemigos(estado, d)]
    if not candidatos:
        raise NoHayEnfrentamiento("No queda ningún dueño con vecinos enemigos")
    return rng.choice(candidatos)


def elegir_defensor(estado: dict, atacante: str, rng: random.Random) -> str:
    """Concello defensor al azar entre los vecinos enemigos de todo el territorio del atacante."""
    candidatos = vecinos_enemigos(estado, atacante)
    if not candidatos:
        raise NoHayEnfrentamiento(f"El dueño {atacante} no tiene vecinos enemigos")
    return rng.choice(candidatos)


def elegir_enfrentamiento(estado: dict, rng: random.Random) -> Enfrentamiento:
    """Sortea un enfrentamiento completo (atacante, concello defensor y concello atacante)."""
    concellos = estado["concellos"]
    atacante = elegir_atacante(estado, rng)
    concello_defensor = elegir_defensor(estado, atacante, rng)
    tocan = sorted(
        v for v in concellos[concello_defensor]["vecinos"] if concellos[v]["dono"] == atacante
    )
    concello_atacante = rng.choice(tocan)
    return Enfrentamiento(
        atacante=atacante,
        defensor=concellos[concello_defensor]["dono"],
        concello_atacante=concello_atacante,
        concello_defensor=concello_defensor,
    )
