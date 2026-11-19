"""Descarga la tabla 142 del IGE (cifras de población por concello, Censo anual del INE).

Fuente: IGE, API de datos, tabla 142. Ver docs/FUENTES.md para las condiciones de uso.

Uso:
    python scripts/descargar_poblacion.py

Guarda solo las filas «Total sexo / Total edad» en data/raw/poblacion_ige_tabla142.json
(carpeta ignorada por git). La tabla completa pesa 15 MB; se descarga una sola vez.
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

URL = "https://www.ige.gal/igebdt/igeapi/json/datos/142/"
DESTINO = Path(__file__).resolve().parent.parent / "data" / "raw" / "poblacion_ige_tabla142.json"
REINTENTOS = 5


def main() -> int:
    for intento in range(1, REINTENTOS + 1):
        try:
            with urllib.request.urlopen(URL, timeout=180) as r:
                datos = json.loads(r.read().decode("latin-1"))  # el IGE sirve ISO-8859-1
            break
        except Exception as e:  # noqa: BLE001 - red inestable, se reintenta
            print(f"intento {intento}: {e}", file=sys.stderr)
            time.sleep(3 * intento)
    else:
        raise RuntimeError("No se pudo descargar la tabla 142 del IGE")
    # fila: [año, año, sexo, edad, código, nombre, valor, valor con puntos]
    filas = [f for f in datos["datos"] if f[2] == "Total" and f[3] == "Total"]
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps({"variables": datos["variables"], "datos": filas}, ensure_ascii=False),
                       encoding="utf-8")
    print(f"Guardadas {len(filas)} filas en {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
