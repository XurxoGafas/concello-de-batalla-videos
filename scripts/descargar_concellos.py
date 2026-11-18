"""Descarga los límites de los concellos de Galicia desde el API-Features del IGN.

Fuente: Instituto Geográfico Nacional (IGN), «Unidades administrativas»,
https://api-features.ign.es/collections/administrativeunit
Licencia: CC BY 4.0 (citar «CC-BY 4.0 ign.es»). Ver docs/FUENTES.md.

Uso:
    python scripts/descargar_concellos.py

Guarda el resultado en data/raw/concellos.geojson (carpeta ignorada por git).
Reintenta cada página, porque el túnel de red a veces corta la conexión.
"""

import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

URL = "https://api-features.ign.es/collections/administrativeunit/items"
PAGINA = 20
REINTENTOS = 6
DESTINO = Path(__file__).resolve().parent.parent / "data" / "raw" / "concellos.geojson"


def pedir(offset: int) -> dict:
    params = {
        "f": "json",
        "limit": PAGINA,
        "offset": offset,
        "codnut2": "ES11",  # Galicia
        "nationallevelname": "Municipio",
    }
    url = f"{URL}?{urllib.parse.urlencode(params)}"
    for intento in range(1, REINTENTOS + 1):
        try:
            with urllib.request.urlopen(url, timeout=90) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 - red inestable, se reintenta
            print(f"  offset {offset}, intento {intento}: {e}", file=sys.stderr)
            time.sleep(3 * intento)
    raise RuntimeError(f"No se pudo descargar la página con offset {offset}")


def main() -> int:
    features: list[dict] = []
    offset = 0
    total = None
    while total is None or offset < total:
        d = pedir(offset)
        total = d["numberMatched"]
        features.extend(d["features"])
        offset += PAGINA
        print(f"{min(offset, total)}/{total}")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}),
        encoding="utf-8",
    )
    print(f"Guardados {len(features)} concellos en {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
