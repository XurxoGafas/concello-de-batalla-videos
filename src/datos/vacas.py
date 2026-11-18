"""Censo de vacas por concello (paso 2.3).

Lee `data/raw/vacas_ige_tabla62.json` (ver `scripts/descargar_vacas.py`) y genera
`data/processed/vacas.json` con las vacas de cada concello, indexadas por el mismo id
que `concellos.geojson` (código `nationalcode` del IGN).

Decisiones (ver docs/DECISIONES.md):
- «Vacas» = variable «Número de vacas» del IGE (vacas de muxidura + non muxidura);
  no se cuentan los «outros bovinos» (terneros, novillas...).
- Año: el último con datos para todos los concellos de la tabla.
- Si un concello tiene oficialmente 0 vacas, se usa 1 (evita dividir por cero al
  calcular el multiplicador). Los ajustados quedan registrados en `ajustados_cero_a_uno`.
- Si falta el dato de un concello, NO se inventa: el script se detiene y lista cuáles.

Uso:
    python -m src.datos.vacas
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "vacas_ige_tabla62.json"
CONCELLOS = RAIZ / "data" / "processed" / "concellos.geojson"
SALIDA = RAIZ / "data" / "processed" / "vacas.json"

VARIABLE = "Número de vacas"
CODIGO_GALICIA = "12"


def ultimo_anio(filas: list[list[str]]) -> str:
    """Último año que aparece en la tabla para la variable de vacas."""
    anios = sorted({f[1] for f in filas if f[0] == VARIABLE})
    return anios[-1]


def vacas_por_ine(filas: list[list[str]], anio: str) -> dict[str, str]:
    """{código INE de 5 dígitos: dato en texto ('' si falta)} para el año dado."""
    return {
        f[3]: f[5]
        for f in filas
        if f[0] == VARIABLE and f[1] == anio and len(f[3]) == 5
    }


def total_galicia(filas: list[list[str]], anio: str) -> int:
    for f in filas:
        if f[0] == VARIABLE and f[1] == anio and f[3] == CODIGO_GALICIA:
            return int(float(f[5]))
    raise ValueError("No aparece el total de Galicia en la tabla")


def construir(ids: list[str], filas: list[list[str]], anio: str) -> dict:
    """Une el censo con los ids del IGN (los 5 últimos dígitos son el código INE)."""
    por_ine = vacas_por_ine(filas, anio)
    sin_dato = [i for i in ids if por_ine.get(i[-5:], "") == ""]
    if sin_dato:
        raise ValueError(f"Concellos sin dato de vacas (resolver con el usuario): {sin_dato}")

    vacas: dict[str, int] = {}
    ajustados: list[str] = []
    total_oficial = 0
    for i in ids:
        n = int(float(por_ine[i[-5:]]))
        total_oficial += n
        if n == 0:
            n = 1
            ajustados.append(i)
        vacas[i] = n

    oficial_galicia = total_galicia(filas, anio)
    if total_oficial != oficial_galicia:
        raise ValueError(
            f"El total de los concellos ({total_oficial}) no cuadra con el total "
            f"publicado para Galicia ({oficial_galicia})"
        )
    return {
        "anio": int(anio),
        "variable": "Número de vacas (muxidura + non muxidura)",
        "fuente": "IGE, táboa 62 (orixe: IGE-CMR, rexistro de gando bovino)",
        "total_oficial_galicia": oficial_galicia,
        "ajustados_cero_a_uno": sorted(ajustados),
        "vacas": vacas,
    }


def main() -> None:
    filas = json.loads(RAW.read_text(encoding="utf-8"))["datos"]
    ids = [f["properties"]["id"] for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"]]
    anio = ultimo_anio(filas)
    resultado = construir(ids, filas, anio)
    SALIDA.write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    print(
        f"Año {anio}: {len(ids)} concellos, total oficial {resultado['total_oficial_galicia']} vacas, "
        f"{len(resultado['ajustados_cero_a_uno'])} con 0 vacas ajustados a 1"
    )
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
