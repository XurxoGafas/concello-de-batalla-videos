"""Descarga las imágenes de las banderas de los concellos de Galicia (paso 2.4).

Fuente: Wikidata (propiedad P41 «imagen de la bandera», datos CC0) y las imágenes alojadas
en Wikimedia Commons. Solo se usan para extraer sus colores; no se redistribuyen.
Ver docs/FUENTES.md.

Uso:
    python scripts/descargar_banderas.py

Guarda:
- data/raw/banderas_wikidata.json: {ine: {"nome": ..., "imagen": url o null}}
- data/raw/banderas/<ine>.<ext>: las imágenes (carpeta ignorada por git)

Es respetuoso con Wikimedia: una petición cada vez, con pausa, identificándose con un
User-Agent y esperando lo que pida el servidor si responde 429 (demasiadas peticiones).
Si se vuelve a ejecutar, no vuelve a bajar las imágenes que ya tiene ni a consultar la lista
de Wikidata (salvo con `--actualizar-lista`).
"""

import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LISTA = RAIZ / "data" / "raw" / "banderas_wikidata.json"
CARPETA = RAIZ / "data" / "raw" / "banderas"
UA = "ConcelloDeBatalla/1.0 (proyecto personal; GitHub XurxoGafas)"
PAUSA = 1.0

CONSULTA = """
SELECT ?ine ?itemLabel ?flag WHERE {
  ?item wdt:P772 ?ine .
  FILTER(REGEX(?ine, "^(15|27|32|36)[0-9]{3}$"))
  ?item wdt:P31/wdt:P279* wd:Q2074737 .
  OPTIONAL { ?item wdt:P41 ?flag . }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "gl,es,en". }
}
"""


def pedir(url: str, reintentos: int = 6) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    for intento in range(1, reintentos + 1):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                espera = int(e.headers.get("Retry-After", "30")) + 2
                print(f"  429, esperando {espera}s", file=sys.stderr)
                time.sleep(espera)
                continue
            raise
        except Exception as e:  # noqa: BLE001 - red inestable
            print(f"  intento {intento}: {e}", file=sys.stderr)
            time.sleep(3 * intento)
    raise RuntimeError(f"No se pudo descargar {url}")


def url_directa(url_commons: str) -> str:
    """Ruta directa en upload.wikimedia.org (evita la redirección de Special:FilePath).

    El servidor de archivos organiza las imágenes por los primeros caracteres del md5 del
    nombre del archivo (con guiones bajos en vez de espacios).
    """
    nombre = urllib.parse.unquote(url_commons.rsplit("/", 1)[-1]).replace(" ", "_")
    h = hashlib.md5(nombre.encode("utf-8")).hexdigest()
    return (
        f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/"
        f"{urllib.parse.quote(nombre)}"
    )


def lista_wikidata() -> dict:
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode(
        {"query": CONSULTA, "format": "json"}
    )
    filas = json.loads(pedir(url))["results"]["bindings"]
    res: dict[str, dict] = {}
    for f in filas:
        ine = f["ine"]["value"]
        e = res.setdefault(ine, {"nome": f["itemLabel"]["value"], "imagen": None})
        if "flag" in f and not e["imagen"]:
            e["imagen"] = f["flag"]["value"]
    return res


def main() -> int:
    # La consulta a Wikidata solo se hace si no existe ya la lista (o con --actualizar-lista),
    # para no cargar el servicio innecesariamente.
    if LISTA.exists() and "--actualizar-lista" not in sys.argv:
        lista = json.loads(LISTA.read_text(encoding="utf-8"))
    else:
        lista = lista_wikidata()
        LISTA.parent.mkdir(parents=True, exist_ok=True)
        LISTA.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    con = {k: v for k, v in lista.items() if v["imagen"]}
    print(f"{len(lista)} municipios en Wikidata, {len(con)} con imagen de bandera")

    CARPETA.mkdir(parents=True, exist_ok=True)
    for n, (ine, v) in enumerate(sorted(con.items()), 1):
        ext = v["imagen"].rsplit(".", 1)[-1].lower()
        destino = CARPETA / f"{ine}.{ext}"
        if destino.exists() and destino.stat().st_size > 0:
            continue
        url = url_directa(v["imagen"])
        destino.write_bytes(pedir(url))
        print(f"{n}/{len(con)} {ine} {v['nome']}")
        time.sleep(PAUSA)
    print("Hecho")
    return 0


if __name__ == "__main__":
    sys.exit(main())
