"""Prepara las banderas y escudos de los concellos (paso 2.5).

Uso:  python scripts/preparar_banderas.py <carpeta con las imágenes del usuario>

Para cada concello elige una imagen (prefiere el PNG con transparencia al JPG), decide si es una
**bandera** (rectángulo que llena la imagen) o solo un **escudo**, y guarda:
  - `assets/banderas/<INE>.png`  miniatura de la bandera (de ella sale la paleta de colores);
  - `assets/escudos/<INE>.png`   escudo recortado y con fondo transparente;
  - `data/processed/colores_bandera.json`  paleta de las banderas y lista de escudos.
Un concello con solo escudo se pinta de **blanco** y el escudo va encima (decisión del usuario).
Los concellos sin imagen conservan su color provisional.
"""
from __future__ import annotations

import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from src.datos.colores import paleta  # noqa: E402

ESTADO = RAIZ / "data" / "processed" / "estado_inicial.json"
SALIDA = RAIZ / "data" / "processed" / "colores_bandera.json"
DIR_BANDERAS, DIR_ESCUDOS = RAIZ / "assets" / "banderas", RAIZ / "assets" / "escudos"
ALTO_ESCUDO, ANCHO_BANDERA = 300, 240
ANCHO_BANDERA_MAPA = 720  # la bandera se dibuja recortada sobre el territorio: necesita más resolución que la paleta
RELACION_BANDERA = 1.25  # una imagen más ancha que alta (≥ 1,25) con el fondo lleno o blanco es una bandera

# nombres de archivo que no siguen el patrón «nombre-del-concello»
ALIAS = {
    "Escudo_As_Nogais.jpg": "as-nogais",
    "Escudo_de_As_Neves.svg.webp": "as-neves",
    "Escudo_de_Barreiros.svg.webp": "barreiros",
    "a veiga escudo poner fondo blanco.webp": "a-veiga",
}
IGNORAR = {"_origen.tsv", "boveda-arquitectura.png"}  # el segundo es una foto de piedra, no el escudo
FORZAR_ESCUDO = {"Lugo", "Camariñas"}   # imágenes anchas o sin borde claro que son escudos
FORZAR_BANDERA = {"Petín"}              # bandera casi cuadrada con fondo blanco
SIN_USO = {"Carral": "solo hay una foto de un escudo de piedra (no sirve como bandera ni como escudo)"}


def slug(s: str) -> str:
    s = re.sub(r"#U([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def elegir(archivos: list[str]) -> str:
    """Prefiere el PNG sin espacios en el nombre (viene de Wikimedia, con transparencia)."""
    png = [f for f in archivos if f.endswith(".png") and " " not in f]
    return (png or sorted(archivos))[0]


def borde(a: np.ndarray) -> tuple[float, float]:
    """(fracción del borde transparente, fracción del borde blanco)."""
    b = np.concatenate([a[0, :], a[-1, :], a[:, 0], a[:, -1]]).astype(int)
    return float((b[:, 3] < 40).mean()), float(((b[:, 3] >= 40) & (b[:, :3].min(1) > 235)).mean())


def es_escudo(nombre: str, im: Image.Image) -> bool:
    if nombre in FORZAR_ESCUDO:
        return True
    if nombre in FORZAR_BANDERA:
        return False
    transp, blanco = borde(np.asarray(im))
    return (transp > 0.5 or blanco > 0.5) and im.width / im.height < RELACION_BANDERA


def quitar_fondo_blanco(im: Image.Image) -> Image.Image:
    """Hace transparente el blanco conectado con el borde (para escudos en JPG o PNG con fondo blanco)."""
    a = np.asarray(im.convert("RGBA")).copy()
    if (a[..., 3] < 40).mean() > 0.1:
        return Image.fromarray(a)           # ya tiene transparencia
    blanco = (a[..., :3].min(2) > 232) & (a[..., 3] > 0)
    h, w = blanco.shape
    visto = np.zeros_like(blanco)
    pila = [(y, x) for y in (0, h - 1) for x in range(w) if blanco[y, x]] + \
           [(y, x) for x in (0, w - 1) for y in range(h) if blanco[y, x]]
    while pila:
        y, x = pila.pop()
        if visto[y, x] or not blanco[y, x]:
            continue
        visto[y, x] = True
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not visto[ny, nx]:
                pila.append((ny, nx))
    a[visto, 3] = 0
    return Image.fromarray(a)


def recortar(im: Image.Image) -> Image.Image:
    caja = Image.fromarray((np.asarray(im)[..., 3] > 10).astype("uint8") * 255).getbbox()
    im = im.crop(caja) if caja else im
    if im.height > ALTO_ESCUDO:
        im = im.resize((max(1, round(im.width * ALTO_ESCUDO / im.height)), ALTO_ESCUDO), Image.LANCZOS)
    return im


def main(carpeta: Path) -> None:
    estado = json.loads(ESTADO.read_text(encoding="utf-8"))["concellos"]
    por_slug = {slug(v["nome"]): k for k, v in estado.items()}
    cand: dict[str, list[str]] = collections.defaultdict(list)
    for f in sorted(p.name for p in carpeta.iterdir()):
        if f in IGNORAR:
            continue
        s = ALIAS.get(f) or slug(Path(f).stem)
        if s not in por_slug:
            print("  sin concello:", f)
            continue
        cand[por_slug[s]].append(f)
    DIR_BANDERAS.mkdir(parents=True, exist_ok=True)
    DIR_ESCUDOS.mkdir(parents=True, exist_ok=True)
    con_bandera, escudos, sin_uso = {}, {}, {}
    for i, fs in sorted(cand.items()):
        nombre, ine = estado[i]["nome"], i[-5:]
        if nombre in SIN_USO:
            sin_uso[i] = {"nome": nombre, "motivo": SIN_USO[nombre]}
            continue
        f = elegir(fs)
        im = Image.open(carpeta / f).convert("RGBA")
        if es_escudo(nombre, im):
            recortar(quitar_fondo_blanco(im)).quantize(256, Image.Quantize.FASTOCTREE).save(DIR_ESCUDOS / f"{ine}.png", optimize=True)
            escudos[i] = {"nome": nombre, "escudo": f"assets/escudos/{ine}.png", "origen": f}
        else:
            grande = im
            if grande.width > ANCHO_BANDERA_MAPA:
                grande = grande.resize((ANCHO_BANDERA_MAPA, max(1, round(grande.height * ANCHO_BANDERA_MAPA / grande.width))), Image.LANCZOS)
            grande.quantize(256, Image.Quantize.FASTOCTREE).convert("RGBA").save(DIR_BANDERAS / f"{ine}.png", optimize=True)
            if im.width > ANCHO_BANDERA:  # la paleta se calcula como siempre, con la miniatura
                im = im.resize((ANCHO_BANDERA, max(1, round(im.height * ANCHO_BANDERA / im.width))), Image.LANCZOS)
            pal = paleta(im)
            con_bandera[i] = {"nome": nombre, "colores": [c for c, _ in pal], "pesos": [p for _, p in pal],
                              "origen": f}
    sin = {i: estado[i]["nome"] for i in estado if i not in cand}
    SALIDA.write_text(json.dumps({"con_bandera": con_bandera, "con_escudo": escudos, "sin_uso": sin_uso,
                                  "sin_imagen": sin}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(con_bandera)} con bandera, {len(escudos)} solo con escudo, {len(sin_uso)} sin uso, "
          f"{len(sin)} sin imagen: {sorted(sin.values())}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
