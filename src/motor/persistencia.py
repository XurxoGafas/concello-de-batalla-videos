"""Persistencia de la partida entre ejecuciones (paso 3.5).

Archivos (en `data/partida/`, se guardan con un commit en cada ejecución):

- `estado_actual.json`: el estado de la partida (concellos, dueños, victorias, episodio y
  `batallas_jugadas`).
- `historial.jsonl`: una línea JSON por batalla con todo lo necesario para repetirla o
  dibujarla (semilla de la batalla, enfrentamiento, todos los dados, puntuaciones, ganador).

Reproducibilidad (regla i) sin guardar el estado del generador aleatorio:

- Hay una **semilla de serie** secreta (variable de entorno `SEMILLA_SERIE`, no se guarda en el
  repositorio). Como el repositorio es público, guardarla permitiría a cualquiera simular
  los resultados futuros antes de que salgan los vídeos.
- Cada batalla usa su propia semilla, derivada con SHA-256 de `semilla_serie:número_de_batalla`.
  Esa semilla de batalla SÍ se guarda en el historial: con ella (o con los dados guardados)
  cualquier batalla pasada se puede repetir, pero no revela las futuras.
- Así, jugar 5 batallas en 5 procesos distintos es idéntico a jugarlas en uno solo: no hay
  estado aleatorio que arrastrar entre procesos.

Atomicidad: el estado se escribe en un archivo temporal y se renombra. El historial y el estado
se guardan al final de la ejecución y se suben en el mismo commit (ver fase 8); si la ejecución
falla antes de guardar, no se guarda nada y se puede repetir con la misma semilla de serie.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import os
import random
from pathlib import Path

from src.motor.estado import Episodio, jugar_batalla, partida_terminada
from src.motor.seleccion import NoHayEnfrentamiento

RAIZ = Path(__file__).resolve().parents[2]
RUTA_ESTADO = RAIZ / "data" / "partida" / "estado_actual.json"
RUTA_HISTORIAL = RAIZ / "data" / "partida" / "historial.jsonl"
RUTA_ESTADO_INICIAL = RAIZ / "data" / "processed" / "estado_inicial.json"
VARIABLE_SEMILLA = "SEMILLA_SERIE"
BATALLAS_POR_EPISODIO = 3


def semilla_de_serie_desde_entorno() -> str:
    """Lee la semilla de serie de la variable de entorno; falla si no está definida."""
    valor = os.environ.get(VARIABLE_SEMILLA, "").strip()
    if not valor:
        raise RuntimeError(
            f"Falta la variable de entorno {VARIABLE_SEMILLA} (semilla de la serie; "
            "ver .env.example). Sin ella no se pueden jugar batallas reproducibles."
        )
    return valor


def semilla_de_batalla(semilla_serie: str, numero_batalla: int) -> int:
    """Semilla (entero de 64 bits) de la batalla n-ésima de la serie; estable entre versiones."""
    h = hashlib.sha256(f"{semilla_serie}:{numero_batalla}".encode("utf-8")).digest()
    return int.from_bytes(h[:8], "big")


# --- Lectura y escritura ---


def nueva_partida(ruta_inicial: Path = RUTA_ESTADO_INICIAL) -> dict:
    """Estado de una partida nueva a partir del estado inicial (0 batallas jugadas)."""
    estado = json.loads(Path(ruta_inicial).read_text(encoding="utf-8"))
    estado["batallas_jugadas"] = 0
    return estado


def cargar_estado(ruta: Path = RUTA_ESTADO) -> dict:
    estado = json.loads(Path(ruta).read_text(encoding="utf-8"))
    estado.setdefault("batallas_jugadas", 0)
    return estado


def guardar_estado(estado: dict, ruta: Path = RUTA_ESTADO) -> None:
    """Guarda el estado de forma atómica y con formato estable (diffs pequeños en git)."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_text(
        json.dumps(estado, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    tmp.replace(ruta)


def registro_de_batalla(ep: Episodio, numero_batalla: int, episodio: int, semilla: int) -> dict:
    """Línea del historial: todo lo necesario para repetir o dibujar la batalla."""
    f = ep.enfrentamiento
    r = dataclasses.asdict(ep.resultado)
    r["semilla"] = semilla
    return {
        "batalla": numero_batalla,
        "episodio": episodio,
        "semilla": semilla,
        "atacante": f.atacante,
        "defensor": f.defensor,
        "concello_atacante": f.concello_atacante,
        "concello_defensor": f.concello_defensor,
        "vacas_atacante": ep.vacas_atacante,
        "vacas_defensor": ep.vacas_defensor,
        "ganador": ep.ganador,
        "perdedor": ep.perdedor,
        "resultado": r,
    }


def anadir_al_historial(registros: list[dict], ruta: Path = RUTA_HISTORIAL) -> None:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as fh:
        for reg in registros:
            fh.write(json.dumps(reg, ensure_ascii=False, sort_keys=True) + "\n")


def leer_historial(ruta: Path = RUTA_HISTORIAL) -> list[dict]:
    ruta = Path(ruta)
    if not ruta.exists():
        return []
    return [json.loads(x) for x in ruta.read_text(encoding="utf-8").splitlines() if x.strip()]


# --- Jugar un episodio ---


def jugar_episodio_detallado(
    estado: dict, semilla_serie: str, n_batallas: int = BATALLAS_POR_EPISODIO
) -> tuple[dict, list[dict], list[tuple[dict, Episodio]]]:
    """Como `jugar_episodio`, pero devuelve además, por cada batalla, el estado **previo** y el `Episodio`.

    Lo usa el render del vídeo: para dibujar cada batalla hacen falta el mapa antes de ella y el
    resultado. El estado posterior de una batalla es el previo de la siguiente (o el final)."""
    if partida_terminada(estado):
        raise NoHayEnfrentamiento("La partida ya ha terminado: queda un único dueño")
    nuevo = copy.deepcopy(estado)
    nuevo.setdefault("batallas_jugadas", 0)
    nuevo["episodio"] += 1
    registros: list[dict] = []
    pasos: list[tuple[dict, Episodio]] = []
    for _ in range(n_batallas):
        if partida_terminada(nuevo):
            break
        numero = nuevo["batallas_jugadas"] + 1
        semilla = semilla_de_batalla(semilla_serie, numero)
        previo = nuevo
        nuevo, ep = jugar_batalla(previo, random.Random(semilla))
        nuevo["batallas_jugadas"] = numero
        registros.append(registro_de_batalla(ep, numero, nuevo["episodio"], semilla))
        pasos.append((previo, ep))
    return nuevo, registros, pasos


def jugar_episodio(
    estado: dict, semilla_serie: str, n_batallas: int = BATALLAS_POR_EPISODIO
) -> tuple[dict, list[dict]]:
    """Juega hasta `n_batallas` batallas encadenadas y avanza el número de episodio.

    Devuelve el estado nuevo (sin modificar el recibido) y los registros del historial. Si la
    partida termina antes de completar las batallas, se detiene ahí. Lanza
    `NoHayEnfrentamiento` si la partida ya había terminado al empezar.
    """
    nuevo, registros, _ = jugar_episodio_detallado(estado, semilla_serie, n_batallas)
    return nuevo, registros


def jugar_y_guardar(
    semilla_serie: str,
    n_batallas: int = BATALLAS_POR_EPISODIO,
    ruta_estado: Path = RUTA_ESTADO,
    ruta_historial: Path = RUTA_HISTORIAL,
) -> tuple[dict, list[dict]]:
    """Carga la partida (o la crea si no existe), juega un episodio y guarda todo."""
    ruta_estado = Path(ruta_estado)
    estado = cargar_estado(ruta_estado) if ruta_estado.exists() else nueva_partida()
    nuevo, registros = jugar_episodio(estado, semilla_serie, n_batallas)
    anadir_al_historial(registros, ruta_historial)
    guardar_estado(nuevo, ruta_estado)
    return nuevo, registros
