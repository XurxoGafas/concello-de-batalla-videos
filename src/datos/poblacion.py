"""Población por concello (paso 4.7).

Lee `data/raw/poblacion_ige_tabla142.json` (ver `scripts/descargar_poblacion.py`) y genera
`data/processed/poblacion.json` con los habitantes de cada concello (1 de enero del último año),
indexados por el mismo id que `concellos.geojson`. Solo sirve para elegir el concello protagonista
de la portada del vídeo; no interviene en las reglas del juego.

Si falta el dato de algún concello vigente NO se inventa: el script se detiene y los lista.

Uso:
    python -m src.datos.poblacion
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "poblacion_ige_tabla142.json"
CONCELLOS = RAIZ / "data" / "processed" / "concellos.geojson"
SALIDA = RAIZ / "data" / "processed" / "poblacion.json"
CODIGO_GALICIA = "12"


def ultimo_anio(filas: list[list[str]]) -> str:
    return sorted({f[0] for f in filas})[-1]


def construir(ids: list[str], filas: list[list[str]], anio: str) -> dict:
    """Une la población con los ids del IGN (los 5 últimos dígitos son el código INE)."""
    por_ine = {f[4]: f[6] for f in filas if f[0] == anio and len(f[4]) == 5}
    sin_dato = [i for i in ids if por_ine.get(i[-5:], "") == ""]
    if sin_dato:
        raise ValueError(f"Concellos sin dato de población (resolver con el usuario): {sin_dato}")
    habitantes = {i: int(float(por_ine[i[-5:]])) for i in ids}
    total = sum(habitantes.values())
    oficial = next(int(float(f[6])) for f in filas if f[0] == anio and f[4] == CODIGO_GALICIA)
    if total != oficial:
        raise ValueError(f"El total de los concellos ({total}) no cuadra con el de Galicia ({oficial})")
    return {
        "anio": int(anio),
        "fuente": "IGE, táboa 142 (orixe: INE, Censo anual de poboación), 1 de xaneiro",
        "total_oficial_galicia": oficial,
        "poboacion": habitantes,
    }


def cargar(ruta: Path = SALIDA) -> dict[str, int]:
    """{id del concello: habitantes}."""
    return {k: int(v) for k, v in json.loads(ruta.read_text(encoding="utf-8"))["poboacion"].items()}


def main() -> None:
    filas = json.loads(RAW.read_text(encoding="utf-8"))["datos"]
    ids = [f["properties"]["id"] for f in json.loads(CONCELLOS.read_text(encoding="utf-8"))["features"]]
    out = construir(sorted(ids), filas, ultimo_anio(filas))
    SALIDA.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{len(ids)} concellos, total {out['total_oficial_galicia']:,} habitantes → {SALIDA}")


if __name__ == "__main__":
    main()
