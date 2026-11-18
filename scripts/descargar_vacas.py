"""Descarga la tabla 62 del IGE (efectivos y explotaciones de gando bovino por concello).

Fuente: Instituto Galego de Estatística (IGE), API de datos, tabla 62
https://www.ige.gal/igebdt/selector.jsp?COD=62 (origen de los datos: IGE-CMR, rexistro de
gando bovino da Consellería do Medio Rural). Ver docs/FUENTES.md para las condiciones de uso.

Uso:
    python scripts/descargar_vacas.py

Guarda el resultado en data/raw/vacas_ige_tabla62.json (carpeta ignorada por git).
"""

import json
import sys
import time
import urllib.request
from pathlib import Path

URL = "https://www.ige.gal/igebdt/igeapi/json/datos/62/"
DESTINO = Path(__file__).resolve().parent.parent / "data" / "raw" / "vacas_ige_tabla62.json"
REINTENTOS = 5


def main() -> int:
    for intento in range(1, REINTENTOS + 1):
        try:
            with urllib.request.urlopen(URL, timeout=120) as r:
                # El IGE sirve este JSON en ISO-8859-1.
                datos = json.loads(r.read().decode("latin-1"))
            break
        except Exception as e:  # noqa: BLE001 - red inestable, se reintenta
            print(f"intento {intento}: {e}", file=sys.stderr)
            time.sleep(3 * intento)
    else:
        raise RuntimeError("No se pudo descargar la tabla 62 del IGE")
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    print(f"Guardadas {len(datos['datos'])} filas en {DESTINO}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
