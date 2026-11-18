"""Línea de comandos del proyecto (paso 3.6).

Uso:
    python -m src.cli simular --batallas 10 --semilla 42

Simula N batallas desde el estado inicial de Galicia y las imprime en texto legible. Es solo
una prueba: **no guarda nada** en `data/partida/` (la partida real se guarda con la
persistencia del paso 3.5). Con la misma semilla la salida es siempre idéntica.
Más adelante (fase 6) este mismo archivo tendrá los comandos `generar` y `publicar`.
"""

from __future__ import annotations

import argparse
import random
import sys

from src.motor.estado import ganador_de_la_serie, jugar_batalla, partida_terminada
from src.motor.persistencia import nueva_partida, registro_de_batalla, semilla_de_batalla


def _num(n: int) -> str:
    """Número entero con punto de millares (1.234)."""
    return f"{n:,}".replace(",", ".")


def _dec(x: float) -> str:
    """Decimal con coma y sin ceros sobrantes (5; 10,5)."""
    return f"{x:.1f}".replace(".", ",").removesuffix(",0")


def _bando(estado: dict, dono: str, concello: str) -> str:
    """Nombre legible de un bando: el concello que da la cara y, si tiene más, su tamaño."""
    nome = estado["concellos"][concello]["nome"]
    n = len(estado["donos"][dono]["territorio"])
    return nome if n == 1 else f"{nome} [{n} concellos]"


def formatear_batalla(estado: dict, reg: dict) -> str:
    """Texto de una batalla a partir del estado ANTES de jugarla y su registro del historial."""
    r = reg["resultado"]
    a = _bando(estado, reg["atacante"], reg["concello_atacante"])
    d = _bando(estado, reg["defensor"], reg["concello_defensor"])
    na = estado["concellos"][reg["concello_atacante"]]["nome"]
    nd = estado["concellos"][reg["concello_defensor"]]["nome"]
    lineas = [
        f"Batalla {reg['batalla']}: {a} ataca a {d}",
        f"  Vacas: {_num(reg['vacas_atacante'])} contra {_num(reg['vacas_defensor'])}",
    ]
    for i, t in enumerate(r["tiradas"], 1):
        if t["puntos_a"]:
            res = f"+{t['puntos_a']} para {na}"
        elif t["puntos_b"]:
            res = f"+{t['puntos_b']} para {nd}"
        else:
            res = "empate, 0 puntos"
        lineas.append(f"  Tirada {i}: {t['dado_a']} contra {t['dado_b']} ({res})")
    lineas.append(f"  Puntos: {r['puntos_a']} contra {r['puntos_b']}")
    if r["mult_a"] > 1:
        lineas.append(f"  Multiplicador: {na} ×{_dec(r['mult_a'])}")
    elif r["mult_b"] > 1:
        lineas.append(f"  Multiplicador: {nd} ×{_dec(r['mult_b'])}")
    else:
        lineas.append("  Multiplicador: ninguno (×1)")
    lineas.append(f"  Puntuación final: {_dec(r['decimas_a'] / 10)} contra {_dec(r['decimas_b'] / 10)}")
    for i, m in enumerate(r["muerte_subita"], 1):
        lineas.append(f"  Muerte súbita {i}: {m['dado_a']} contra {m['dado_b']}")
    gana = a if reg["ganador"] == reg["atacante"] else d
    pierde = d if gana == a else a
    lineas.append(f"  GANA {gana}, conquista a {pierde}")
    return "\n".join(lineas)


def simular(n_batallas: int, semilla: str, salida=None) -> int:
    """Simula `n_batallas` desde el estado inicial e imprime cada una. Devuelve las jugadas."""
    salida = salida or sys.stdout
    estado = nueva_partida()
    estado["batallas_jugadas"] = 0
    jugadas = 0
    for numero in range(1, n_batallas + 1):
        if partida_terminada(estado):
            break
        s = semilla_de_batalla(semilla, numero)
        nuevo, ep = jugar_batalla(estado, random.Random(s))
        reg = registro_de_batalla(ep, numero, 0, s)
        print(formatear_batalla(estado, reg), file=salida)
        d = nuevo["donos"][ep.ganador]
        print(
            f"  Ahora {d['nome']} tiene {len(d['territorio'])} concellos y {_num(d['vacas'])} vacas;"
            f" quedan {len(nuevo['donos'])} dueños\n",
            file=salida,
        )
        estado, jugadas = nuevo, numero
    unico = ganador_de_la_serie(estado)
    if unico is not None:
        print(f"La partida ha terminado: gana {estado['donos'][unico]['nome']}", file=salida)
    return jugadas


def _entero_positivo(texto: str) -> int:
    n = int(texto)
    if n < 1:
        raise argparse.ArgumentTypeError("debe ser al menos 1")
    return n


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m src.cli", description="Concello de Batalla")
    sub = p.add_subparsers(dest="orden", required=True)
    s = sub.add_parser("simular", help="simula N batallas desde el estado inicial (no guarda nada)")
    s.add_argument("--batallas", type=_entero_positivo, default=10, help="número de batallas")
    s.add_argument("--semilla", required=True, help="semilla de la simulación (texto o número)")
    args = p.parse_args(argv)
    if args.orden == "simular":
        simular(args.batallas, args.semilla)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
