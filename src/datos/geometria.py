"""Geometría de los concellos: simplificación y adyacencias (paso 2.2).

Lee `data/raw/concellos.geojson` (ver `scripts/descargar_concellos.py`) y genera:

- `data/processed/concellos.geojson`: polígonos simplificados para dibujar rápido
  (EPSG:4326), con las propiedades `id`, `nome` y `provincia`.
- `data/processed/adyacencias.json`: para cada id, la lista ordenada de ids vecinos.

Regla de vecindad (decidida por el usuario el 2026-11-18): dos concellos son vecinos
si sus fronteras se tocan, **aunque solo coincidan en una esquina (un único punto)**.
Además se admiten vecindades manuales (`data/vecindades_manuales.json`) para casos
sin contacto físico, como las islas.

Uso:
    python -m src.datos.geometria
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import shapely

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data" / "raw" / "concellos.geojson"
PROCESADO = RAIZ / "data" / "processed" / "concellos.geojson"
ADYACENCIAS = RAIZ / "data" / "processed" / "adyacencias.json"
MANUALES = RAIZ / "data" / "vecindades_manuales.json"

CRS_METROS = 25829  # ETRS89 / UTM 29N: metros, adecuado para Galicia
TOLERANCIA_M = 30.0  # simplificación para dibujar (en metros)
N_CONCELLOS = 313

PROVINCIAS = {"15": "A Coruña", "27": "Lugo", "32": "Ourense", "36": "Pontevedra"}


def cargar_raw(ruta: Path = RAW) -> gpd.GeoDataFrame:
    """Carga los polígonos originales, proyectados a metros, con columnas id/nome."""
    g = gpd.read_file(ruta).to_crs(CRS_METROS)
    g = g.rename(columns={"nationalcode": "id", "nameunit": "nome"})
    g["provincia"] = g["id"].str[4:6].map(PROVINCIAS)
    g = g[["id", "nome", "provincia", "geometry"]].sort_values("id")
    return g.reset_index(drop=True)


def calcular_adyacencias(
    g: gpd.GeoDataFrame, manuales: list[tuple[str, str]] | None = None
) -> dict[str, list[str]]:
    """Devuelve {id: [ids vecinos]} usando las geometrías ORIGINALES (no simplificadas).

    Vecinos = las fronteras se tocan (`intersects`), sea en una línea o en un solo punto,
    sin contar el solape de interiores como caso aparte. `manuales` añade parejas de ids
    sin contacto físico. La relación es simétrica y nadie es vecino de sí mismo.
    """
    ids = g["id"].tolist()
    vecinos: dict[str, set[str]] = {i: set() for i in ids}
    # Consulta por índice espacial: devuelve pares (i, j) de posiciones que se intersectan.
    pos_a, pos_b = g.sindex.query(g.geometry, predicate="intersects")
    for a, b in zip(pos_a, pos_b):
        if a != b:
            vecinos[ids[a]].add(ids[b])
            vecinos[ids[b]].add(ids[a])
    for a, b in manuales or []:
        if a not in vecinos or b not in vecinos:
            raise ValueError(f"Vecindad manual con id desconocido: {a}, {b}")
        vecinos[a].add(b)
        vecinos[b].add(a)
    return {i: sorted(v) for i, v in vecinos.items()}


def simplificar(g: gpd.GeoDataFrame, tolerancia: float = TOLERANCIA_M) -> gpd.GeoDataFrame:
    """Simplifica los polígonos conservando las fronteras compartidas.

    Usa `coverage_simplify`, que simplifica cada frontera común una sola vez, de modo que
    dos concellos vecinos siguen encajando sin huecos ni solapes (a diferencia de
    simplificar cada polígono por separado).
    """
    s = g.copy()
    s["geometry"] = shapely.coverage_simplify(g.geometry.values, tolerancia)
    return s


def leer_manuales(ruta: Path = MANUALES) -> list[tuple[str, str, str]]:
    """Lee las vecindades manuales. Devuelve [(nombre_a, nombre_b, motivo)]."""
    if not ruta.exists():
        return []
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    return [(d["a"], d["b"], d.get("motivo", "")) for d in datos["vecindades"]]


def nombres_a_ids(g: gpd.GeoDataFrame, parejas: list[tuple[str, str, str]]) -> list[tuple[str, str]]:
    por_nombre = dict(zip(g["nome"], g["id"]))
    salida = []
    for a, b, _ in parejas:
        for n in (a, b):
            if n not in por_nombre:
                raise ValueError(f"Concello desconocido en vecindades manuales: {n!r}")
        salida.append((por_nombre[a], por_nombre[b]))
    return salida


def main() -> None:
    g = cargar_raw()
    if len(g) != N_CONCELLOS:
        raise SystemExit(f"Se esperaban {N_CONCELLOS} concellos y hay {len(g)}")

    manuales = nombres_a_ids(g, leer_manuales())
    ady = calcular_adyacencias(g, manuales)

    sin_vecinos = [i for i, v in ady.items() if not v]
    if sin_vecinos:
        nombres = g.set_index("id").loc[sin_vecinos, "nome"].tolist()
        raise SystemExit(f"Concellos sin ningún vecino: {nombres}")

    simple = simplificar(g).to_crs(4326)
    PROCESADO.parent.mkdir(parents=True, exist_ok=True)
    simple.to_file(PROCESADO, driver="GeoJSON", COORDINATE_PRECISION=6)
    ADYACENCIAS.write_text(
        json.dumps(ady, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8"
    )

    n_pares = sum(len(v) for v in ady.values()) // 2
    print(f"{len(g)} concellos, {n_pares} parejas de vecinos")
    print(f"Escrito {PROCESADO.relative_to(RAIZ)} y {ADYACENCIAS.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
