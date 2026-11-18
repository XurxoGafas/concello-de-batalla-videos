"""Multiplicador por vacas (paso 3.1).

Regla (ver docs/DECISIONES.md y PLAN.md):

1. Solo multiplica el bando con MÁS vacas; el otro bando multiplica por 1.
2. Porcentaje = (vacas_mayor − vacas_menor) / vacas_menor × 100.
3. Se redondea a la decena: si la unidad es ≤ 5 se baja, si es > 5 se sube
   (35 % → 30 % → ×1,3 · 36 % → 40 % → ×1,4 · 25 % → 20 % → ×1,2).
4. Tope del 50 %: ×1,5.
5. Las «vacas» de cada bando son las de TODO su territorio (suma de los concellos que
   posee), no solo las del concello que combate.

Los cálculos se hacen con fracciones exactas para que los casos límite (5 %, 35 %...) no
dependan de errores de coma flotante.

Decisión sobre los decimales (no estaba cubierta por los ejemplos): el porcentaje exacto
se compara con la decena; si lo que sobra de la decena es **más de 5** (aunque sea 5,01)
se sube, y si es 5 o menos se baja. Así 35 % → ×1,3 y 35,5 % → ×1,4.
"""

from __future__ import annotations

from fractions import Fraction

TOPE_PORCENTAJE = 50


def vacas_de_dono(concellos: dict[str, dict], dono: str) -> int:
    """Vacas del territorio completo de un dueño: suma de las de todos sus concellos.

    `concellos` es el diccionario `estado["concellos"]` (cada uno con `vacas` y `dono`).
    """
    return sum(c["vacas"] for c in concellos.values() if c["dono"] == dono)


def bonus_porcentaje(vacas_a: int, vacas_b: int) -> int:
    """Bonus, en puntos porcentuales (0, 10, 20, 30, 40 o 50), del bando con más vacas."""
    for v in (vacas_a, vacas_b):
        if v < 1:
            raise ValueError(f"Las vacas deben ser al menos 1 (recibido {v})")
    mayor, menor = max(vacas_a, vacas_b), min(vacas_a, vacas_b)
    pct = Fraction((mayor - menor) * 100, menor)  # exacto
    decena = (pct // 10) * 10
    sobra = pct - decena
    bonus = decena + 10 if sobra > 5 else decena
    return int(min(bonus, TOPE_PORCENTAJE))


def multiplicador(vacas_propias: int, vacas_rivales: int) -> float:
    """Multiplicador del bando con `vacas_propias` frente a otro con `vacas_rivales`.

    Es 1,0 si no tiene más vacas que el rival (o si hay empate a vacas).
    """
    if vacas_propias <= vacas_rivales:
        bonus_porcentaje(vacas_propias, vacas_rivales)  # solo para validar las entradas
        return 1.0
    return 1 + bonus_porcentaje(vacas_propias, vacas_rivales) / 100


def multiplicadores(vacas_a: int, vacas_b: int) -> tuple[float, float]:
    """(multiplicador de A, multiplicador de B). Solo uno puede ser mayor que 1."""
    return multiplicador(vacas_a, vacas_b), multiplicador(vacas_b, vacas_a)


def diferencia_porcentual(vacas_a: int, vacas_b: int) -> int:
    """Diferencia real de vacas, en % entero, para MOSTRARLA en pantalla (no es el bonus).

    Es `(mayor − menor) / menor × 100` redondeado al entero más cercano (la mitad sube); no
    tiene el tope del 50 %: 143 vacas contra 3 es +4.667 %, aunque el multiplicador sea ×1,5.
    """
    for v in (vacas_a, vacas_b):
        if v < 1:
            raise ValueError(f"Las vacas deben ser al menos 1 (recibido {v})")
    mayor, menor = max(vacas_a, vacas_b), min(vacas_a, vacas_b)
    pct = Fraction((mayor - menor) * 100, menor)
    return int(pct + Fraction(1, 2))  # pct >= 0, así que int() equivale a floor
