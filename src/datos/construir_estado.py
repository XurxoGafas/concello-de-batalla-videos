"""Construye el estado inicial del juego (paso 2.4).

Une los datos ya preparados en `data/processed/`:
- `concellos.geojson`  → id, nombre y provincia (la geometría se queda allí, ver nota)
- `adyacencias.json`   → vecinos
- `vacas.json`         → vacas
- `colores_bandera.json` → colores de la bandera

y escribe `data/processed/estado_inicial.json`.

Nota de diseño: la geometría NO se copia al estado. Es estática y pesa unos 2,5 MB, mientras
que el estado se guardará con un commit en cada ejecución diaria (paso 3.5). El estado
referencia cada concello por su id y la geometría se lee de `concellos.geojson`.

Estructura:
- `concellos[id]`: datos fijos del concello (nombre, provincia, vecinos, vacas propias,
  colores de su bandera) y `dono`, el id del dueño actual (al principio, él mismo).
- `donos[id]`: estado de cada dueño (territorio, vacas totales del territorio, victorias
  acumuladas en la serie, colores con los que se pinta).
- `episodio`: número del último episodio publicado (0 = aún ninguno).

Si un concello no tiene bandera en los datos, recibe un color provisional (marcado con
`"fonte": "provisional"`) hasta que se resuelva.

Uso:
    python -m src.datos.construir_estado
"""

from __future__ import annotations

import colorsys
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PROC = RAIZ / "data" / "processed"
SALIDA = PROC / "estado_inicial.json"


def color_provisional(n: int) -> str:
    """Color distinto y estable para el concello número `n`.

    Tono, saturación y brillo siguen una secuencia de baja discrepancia (R3), de modo que los
    313 colores son distintos entre sí y no se repiten al redondear a 8 bits.
    """
    h = (0.5 + n * 0.8191725134) % 1.0
    sat = 0.45 + 0.4 * ((0.5 + n * 0.6710436067) % 1.0)
    val = 0.7 + 0.25 * ((0.5 + n * 0.5497004779) % 1.0)
    r, g, b = colorsys.hsv_to_rgb(h, sat, val)
    return "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))


def construir(
    nombres: dict[str, tuple[str, str]],
    vecinos: dict[str, list[str]],
    vacas: dict[str, int],
    colores: dict[str, dict],
    escudos: dict[str, dict] | None = None,
) -> dict:
    """Devuelve el estado inicial. `nombres` = {id: (nome, provincia)}."""
    ids = sorted(nombres)
    if not (set(ids) == set(vecinos) == set(vacas)):
        raise ValueError("Los ids de concellos, vecinos y vacas no coinciden")

    concellos: dict[str, dict] = {}
    donos: dict[str, dict] = {}
    for n, i in enumerate(ids):
        if escudos and i in escudos:  # solo hay escudo: territorio blanco y el escudo encima
            cor = {"colores": ["#ffffff"], "pesos": [1.0], "fonte": "escudo", "escudo": escudos[i]["escudo"]}
        elif i in colores:
            cor = {"colores": colores[i]["colores"], "pesos": colores[i]["pesos"], "fonte": "bandeira"}
        else:
            cor = {"colores": [color_provisional(n)], "pesos": [1.0], "fonte": "provisional"}
        nome, provincia = nombres[i]
        concellos[i] = {
            "nome": nome,
            "provincia": provincia,
            "vecinos": vecinos[i],
            "vacas": vacas[i],
            "cor": cor,
            "dono": i,
        }
        donos[i] = {
            "nome": nome,
            "territorio": [i],
            "vacas": vacas[i],
            "victorias": 0,
            "cor": cor,
        }
    return {"version": 1, "episodio": 0, "concellos": concellos, "donos": donos}


def main() -> None:
    g = json.loads((PROC / "concellos.geojson").read_text(encoding="utf-8"))["features"]
    nombres = {f["properties"]["id"]: (f["properties"]["nome"], f["properties"]["provincia"]) for f in g}
    vecinos = json.loads((PROC / "adyacencias.json").read_text(encoding="utf-8"))
    vacas = json.loads((PROC / "vacas.json").read_text(encoding="utf-8"))["vacas"]
    ruta_col = PROC / "colores_bandera.json"
    datos_col = json.loads(ruta_col.read_text(encoding="utf-8")) if ruta_col.exists() else {}
    colores, escudos = datos_col.get("con_bandera", {}), datos_col.get("con_escudo", {})
    estado = construir(nombres, vecinos, vacas, colores, escudos)
    SALIDA.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")
    prov = sum(1 for c in estado["concellos"].values() if c["cor"]["fonte"] == "provisional")
    esc = sum(1 for c in estado["concellos"].values() if c["cor"]["fonte"] == "escudo")
    print(f"{len(estado['concellos'])} concellos, {esc} con escudo sobre blanco, {prov} con color provisional")
    print(f"Escrito {SALIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
