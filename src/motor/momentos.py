"""Momento singular del episodio y frase gancho de la portada (paso 4.7).

1. `detectar_momentos` recorre las 3 batallas del episodio y lista, por concello, los momentos que
   se pueden anunciar (morte súbita, bonus grande de vacas, ser atacante o defensor…).
2. `elegir_portada` decide el protagonista: en el 70 % de los episodios, el concello con más
   habitantes de las 3 batallas; en el 30 %, otro concello con un momento más singular (también si
   el más poblado no tiene ningún momento singular). Después elige una frase de la batería para ese
   tipo de momento, sin repetir las usadas hace poco. Todo con un `random.Random` (reproducible).
3. `expandir` rellena la plantilla de la frase con el nombre del concello, con las contracciones
   gallegas («da Coruña», «ao Porriño») y la concordancia de género y número.

Las frases son ambiguas a propósito: nunca dicen quién gana.
"""

from __future__ import annotations

import json
import random
import re
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
FRASES = RAIZ / "data" / "frases.json"
HISTORIAL = RAIZ / "data" / "partida" / "portadas.jsonl"

PROB_GRANDE = 0.70           # episodios cuyo protagonista es el concello más poblado
SINGULAR = 3.0               # peso desde el que un momento cuenta como «singular»
PESO = {"morte_subita": 4.0, "multiplicador": 3.0, "defensor": 1.2, "atacante": 1.0, "dados": 0.5}
BONUS_GRANDE = 1.4           # el multiplicador solo se anuncia desde ×1,4
EPISODIOS_SIN_REPETIR = 10
MARCA_A, MARCA_B = "⟦", "⟧"  # delimitan el nombre del concello dentro de la frase


# ---------- Gallego: artículo, contracciones y concordancia ----------

def _articulo(nombre: str) -> tuple[str | None, str]:
    """(artículo en minúscula o None, nombre sin el artículo): «A Coruña» → («a», «Coruña»)."""
    primera, _, resto = nombre.partition(" ")
    if primera in ("A", "O", "As", "Os") and resto:
        return primera.lower(), resto
    return None, nombre


def es_plural(nombre: str) -> bool:
    return _articulo(nombre)[0] in ("as", "os")


def es_femenino(nombre: str) -> bool:
    return _articulo(nombre)[0] in ("a", "as")


_CONTRACCION = {
    "a": {"a": "á", "o": "ao", "as": "ás", "os": "aos", None: "a"},
    "de": {"a": "da", "o": "do", "as": "das", "os": "dos", None: "de"},
}


def expandir(plantilla: str, nombre: str) -> str:
    """Rellena la plantilla. El nombre queda entre MARCA_A y MARCA_B (para resaltarlo al dibujar)."""
    art, resto = _articulo(nombre)
    plural, fem = es_plural(nombre), es_femenino(nombre)

    def sustituir(m: re.Match) -> str:
        clave, _, cuerpo = m.group(1).partition(":")
        if clave == "concello":
            if not cuerpo:
                return f"{MARCA_A}{nombre}{MARCA_B}"
            contraccion = _CONTRACCION[cuerpo][art]
            return f"{contraccion} {MARCA_A}{resto}{MARCA_B}" if art else f"{contraccion} {MARCA_A}{nombre}{MARCA_B}"
        formas = cuerpo.split("|")
        if clave == "n":
            return formas[1] if plural else formas[0]
        if clave == "g":
            return formas[(2 if plural else 0) + (1 if fem else 0)]
        raise ValueError(f"Marca desconocida en la plantilla: {m.group(0)}")

    return re.sub(r"\{([^{}]+)\}", sustituir, plantilla)


def sin_marcas(texto: str) -> str:
    return texto.replace(MARCA_A, "").replace(MARCA_B, "")


# ---------- Momentos ----------

@dataclass(frozen=True)
class Momento:
    concello: str      # id del concello (= id de su dueño original)
    nombre: str
    habitantes: int
    tipo: str          # atacante | defensor | dados | multiplicador | morte_subita
    peso: float        # lo singular que es
    batalla: int       # 1, 2 o 3


@dataclass(frozen=True)
class Portada:
    concello: str
    nombre: str
    tipo: str
    batalla: int
    rama: str          # «grande» (el más poblado) u «otro»
    frase_id: int
    texto: str         # frase ya rellena, con el nombre entre MARCA_A y MARCA_B


def detectar_momentos(batallas: list, poblacion: dict[str, int]) -> list[Momento]:
    """`batallas`: lista de (estado_previo, Episodio) como la de `jugar_episodio_detallado`."""
    momentos: list[Momento] = []
    for n, (estado, ep) in enumerate(batallas, start=1):
        r, enf = ep.resultado, ep.enfrentamiento
        lados = ((enf.atacante, "atacante", r.mult_a), (enf.defensor, "defensor", r.mult_b))
        for dono, papel, mult in lados:
            nombre = estado["donos"][dono]["nome"]
            hab = poblacion[dono]

            def nuevo(tipo, peso):
                momentos.append(Momento(dono, nombre, hab, tipo, peso, n))
            nuevo(papel, PESO[papel])
            nuevo("dados", PESO["dados"])
            if r.muerte_subita:
                nuevo("morte_subita", PESO["morte_subita"])
            if mult >= BONUS_GRANDE:
                nuevo("multiplicador", PESO["multiplicador"] + (0.5 if mult >= 1.5 else 0))
    return momentos


def _mejor(momentos: list[Momento], rng: random.Random) -> Momento:
    """El de más peso; los empates los decide el generador."""
    tope = max(m.peso for m in momentos)
    return rng.choice(sorted((m for m in momentos if m.peso == tope), key=lambda m: (m.batalla, m.concello, m.tipo)))


def elegir_momento(momentos: list[Momento], rng: random.Random) -> tuple[Momento, str]:
    grande = max(momentos, key=lambda m: (m.habitantes, m.concello)).concello
    if rng.random() < PROB_GRANDE:
        suyos = [m for m in momentos if m.concello == grande]
        if max(m.peso for m in suyos) >= SINGULAR:
            return _mejor(suyos, rng), "grande"
    resto = [m for m in momentos if m.concello != grande]
    return _mejor(resto, rng), "otro"


def cargar_frases(ruta: Path = FRASES) -> list[dict]:
    return json.loads(ruta.read_text(encoding="utf-8"))["frases"]


def elegir_frase(tipo: str, nombre: str, frases: list[dict], recientes: list[int], rng: random.Random) -> dict:
    """Frase del tipo dado que valga para el nombre y no se haya usado en los últimos episodios."""
    posibles = [f for f in frases if f["tipo"] == tipo and (f["plural"] or not es_plural(nombre))]
    if not posibles:
        raise ValueError(f"No hay frases de tipo {tipo!r} para {nombre!r}")
    ultimas = recientes[-EPISODIOS_SIN_REPETIR:]
    libres = [f for f in posibles if f["id"] not in ultimas]
    if libres:
        return rng.choice(libres)
    # todas usadas hace poco: la que lleva más tiempo sin salir
    return max(posibles, key=lambda f: recientes[::-1].index(f["id"]))


def elegir_portada(batallas: list, poblacion: dict[str, int], frases: list[dict], recientes: list[int],
                   rng: random.Random) -> Portada:
    momento, rama = elegir_momento(detectar_momentos(batallas, poblacion), rng)
    frase = elegir_frase(momento.tipo, momento.nombre, frases, recientes, rng)
    return Portada(momento.concello, momento.nombre, momento.tipo, momento.batalla, rama, frase["id"],
                   expandir(frase["texto"], momento.nombre))


# ---------- Historial de frases usadas ----------

def leer_recientes(ruta: Path = HISTORIAL) -> list[int]:
    if not ruta.exists():
        return []
    return [json.loads(l)["frase"] for l in ruta.read_text(encoding="utf-8").splitlines() if l.strip()]


def anadir_al_historial(episodio: int, p: Portada, ruta: Path = HISTORIAL) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with ruta.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"episodio": episodio, "frase": p.frase_id, "concello": p.nombre, "tipo": p.tipo,
                            "rama": p.rama}, ensure_ascii=False) + "\n")
