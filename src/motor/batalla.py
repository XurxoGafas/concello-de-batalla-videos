"""Batalla entre dos bandos: dados, multiplicador y muerte súbita (paso 3.2).

Reglas (ver docs/DECISIONES.md):

- 3 tiradas. En cada una, cada bando saca un dado; la diferencia entre ambos se suma
  a favor de quien saque más (si empatan en esa tirada, nadie suma). Se acumulan las 3.
- El bando con MÁS vacas (las de todo su territorio) multiplica su total acumulado por el
  multiplicador de `multiplicador.py`; el otro no multiplica.
- Las puntuaciones se comparan CON DECIMALES, sin redondear (decisión del usuario). Como el
  multiplicador tiene un solo decimal y los puntos son enteros, la puntuación tiene como
  mucho un decimal; se guarda en décimas (enteros) para que la comparación sea exacta.
- Si tras el multiplicador hay empate: muerte súbita, con 1 dado por bando, repetida hasta
  desempatar.
- Toda la aleatoriedad sale de un generador con semilla (regla i de CLAUDE.md). Orden de
  los sorteos (parte del contrato de reproducibilidad): para cada una de las 3 tiradas,
  dado del bando A y luego dado del bando B; después, por cada ronda de muerte súbita, dado
  de A y luego de B. Además, el resultado guarda todos los dados, de modo que una batalla se
  puede reproducir o dibujar sin volver a sortear.

El bando A es el atacante y el B el defensor.
"""

from __future__ import annotations

import random
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field

from src.motor.multiplicador import multiplicadores

N_TIRADAS = 3
CARAS = 6


@dataclass(frozen=True)
class Tirada:
    """Una de las 3 tiradas: los dados y los puntos que suma cada bando."""

    dado_a: int
    dado_b: int
    puntos_a: int  # diferencia a favor de A (0 si no saca más)
    puntos_b: int  # diferencia a favor de B (0 si no saca más)


@dataclass(frozen=True)
class RondaMuerteSubita:
    dado_a: int
    dado_b: int


@dataclass(frozen=True)
class ResultadoBatalla:
    semilla: int | None
    vacas_a: int
    vacas_b: int
    tiradas: tuple[Tirada, ...]
    puntos_a: int  # suma de las diferencias, antes del multiplicador
    puntos_b: int
    mult_a: float
    mult_b: float
    decimas_a: int  # puntuación final en décimas (p. ej. 91 = 9,1)
    decimas_b: int
    muerte_subita: tuple[RondaMuerteSubita, ...] = field(default_factory=tuple)
    ganador: str = ""  # "a" o "b"

    @property
    def puntuacion_a(self) -> float:
        return self.decimas_a / 10

    @property
    def puntuacion_b(self) -> float:
        return self.decimas_b / 10

    @property
    def hubo_empate(self) -> bool:
        """True si, tras el multiplicador, hubo que ir a muerte súbita."""
        return bool(self.muerte_subita)


def _decimas(puntos: int, multiplicador: float) -> int:
    """Puntuación en décimas, exacta: puntos × multiplicador × 10."""
    return puntos * round(multiplicador * 100) // 10


def _validar_dado(d: int) -> int:
    if not isinstance(d, int) or not 1 <= d <= CARAS:
        raise ValueError(f"Dado fuera de rango: {d!r}")
    return d


def resolver(
    dados_a: Iterable[int],
    dados_b: Iterable[int],
    vacas_a: int,
    vacas_b: int,
    dados_muerte_subita: Iterable[tuple[int, int]] = (),
    semilla: int | None = None,
) -> ResultadoBatalla:
    """Resuelve una batalla con unos dados ya conocidos (sin aleatoriedad).

    `dados_muerte_subita` proporciona, por orden, los pares (dado A, dado B) que se usarían
    en las rondas de desempate; solo se consumen los necesarios.
    """
    da, db = tuple(map(_validar_dado, dados_a)), tuple(map(_validar_dado, dados_b))
    if len(da) != N_TIRADAS or len(db) != N_TIRADAS:
        raise ValueError(f"Hacen falta {N_TIRADAS} dados por bando")

    tiradas = tuple(
        Tirada(x, y, max(x - y, 0), max(y - x, 0)) for x, y in zip(da, db)
    )
    puntos_a = sum(t.puntos_a for t in tiradas)
    puntos_b = sum(t.puntos_b for t in tiradas)
    mult_a, mult_b = multiplicadores(vacas_a, vacas_b)
    dec_a, dec_b = _decimas(puntos_a, mult_a), _decimas(puntos_b, mult_b)

    rondas: list[RondaMuerteSubita] = []
    if dec_a != dec_b:
        ganador = "a" if dec_a > dec_b else "b"
    else:
        pares: Iterator[tuple[int, int]] = iter(dados_muerte_subita)
        while True:
            try:
                x, y = next(pares)
            except StopIteration:
                raise ValueError("Empate y no quedan dados de muerte súbita") from None
            rondas.append(RondaMuerteSubita(_validar_dado(x), _validar_dado(y)))
            if x != y:
                ganador = "a" if x > y else "b"
                break

    return ResultadoBatalla(
        semilla=semilla,
        vacas_a=vacas_a,
        vacas_b=vacas_b,
        tiradas=tiradas,
        puntos_a=puntos_a,
        puntos_b=puntos_b,
        mult_a=mult_a,
        mult_b=mult_b,
        decimas_a=dec_a,
        decimas_b=dec_b,
        muerte_subita=tuple(rondas),
        ganador=ganador,
    )


def _pares_infinitos(rng: random.Random) -> Iterator[tuple[int, int]]:
    while True:
        yield rng.randint(1, CARAS), rng.randint(1, CARAS)


def simular_batalla(
    vacas_a: int, vacas_b: int, semilla: int | None = None, rng: random.Random | None = None
) -> ResultadoBatalla:
    """Simula una batalla sorteando los dados.

    Con `semilla`, el resultado es siempre el mismo. Si se pasa un `rng` ya creado (para
    encadenar varias batallas con una sola semilla) se usa ese y la semilla no se registra.
    """
    if rng is None:
        if semilla is None:
            raise ValueError("Hace falta una semilla (o un generador): regla de reproducibilidad")
        rng = random.Random(semilla)
    dados_a: list[int] = []
    dados_b: list[int] = []
    for _ in range(N_TIRADAS):  # por tirada: dado de A y luego dado de B
        dados_a.append(rng.randint(1, CARAS))
        dados_b.append(rng.randint(1, CARAS))
    return resolver(
        dados_a, dados_b, vacas_a, vacas_b, _pares_infinitos(rng), semilla=semilla
    )
