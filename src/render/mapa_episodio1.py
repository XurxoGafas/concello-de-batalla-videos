"""Mapa del episodio 1: Ordes ocupa ≈1/3 del territorio de Galicia y el resto de concellos, el suyo.

Genera (sin vídeo, solo imágenes y tablas):
- `output/muestras/mapa_episodio1.png`: fotograma vertical 1080×1920 (título, mapa y línea dorada).
- `output/muestras/mapa_episodio1_grande.png`: solo el mapa, a 2160 px de ancho, para revisar escudos y fronteras.
- `output/muestras/territorios_episodio1.tsv`: de quién es cada concello (dueño, tipo de símbolo y archivo).
- `data/processed/estado_episodio1.json`: el estado con Ordes ya expandido (no toca `data/partida/`).

El territorio de Ordes crece por contigüidad, siempre con el vecino cuyo centro queda más cerca del de
Ordes (forma compacta), hasta acercarse lo más posible a 1/3 de la superficie total (medida en UTM).

Uso: `python -m src.render.mapa_episodio1`
"""

from __future__ import annotations

import json
from pathlib import Path

from PIL import ImageDraw

from src.motor.estado import aplicar_conquista
from src.motor.persistencia import nueva_partida
from src.render import estilo as E
from src.render.fondo import fondo_foto
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"
MAPA_Y0 = 395
FRACCION = 1 / 3
DUENO = "Ordes"


def territorio_compacto(mapa: MapaGalicia, estado: dict, inicio: str, fraccion: float) -> list[str]:
    """Concellos que se anexiona `inicio` hasta alcanzar la `fraccion` de la superficie total."""
    areas = mapa.gdf.geometry.area
    objetivo = areas.sum() * fraccion
    centro = mapa.gdf.geometry[inicio].centroid
    dentro = [inicio]
    total = float(areas[inicio])
    while True:
        frontera = {v for i in dentro for v in estado["concellos"][i]["vecinos"]} - set(dentro)
        if not frontera:
            break
        cand = min(frontera, key=lambda v: mapa.gdf.geometry[v].centroid.distance(centro))
        nuevo = total + float(areas[cand])
        if abs(nuevo - objetivo) > abs(total - objetivo):
            break  # añadir otro concello nos aleja del objetivo
        dentro.append(cand)
        total = nuevo
    return dentro


def estado_episodio1(mapa: MapaGalicia, fraccion: float = FRACCION, dueno: str = DUENO) -> dict:
    estado = nueva_partida()
    id_dueno = next(i for i, c in estado["concellos"].items() if c["nome"] == dueno)
    for i in territorio_compacto(mapa, estado, id_dueno, fraccion)[1:]:
        estado = aplicar_conquista(estado, id_dueno, i)
    estado["donos"][id_dueno]["victorias"] = 0  # es un mapa de partida, no el resultado de batallas
    return estado


def tabla(estado: dict, ruta: Path) -> None:
    """Un concello por fila: de quién es, qué símbolo lleva su dueño y de qué archivo sale."""
    filas = ["ine\tconcello\tdono\tsimbolo_do_dono\tarquivo\tfonte"]
    for i, c in sorted(estado["concellos"].items(), key=lambda t: t[1]["nome"]):
        dono = estado["donos"][c["dono"]]
        cor = dono["cor"]
        fonte = cor["fonte"]
        arquivo = cor.get("escudo") or ("(cor da bandeira " + cor["colores"][0] + ")" if fonte == "bandeira" else "(cor provisional)")
        filas.append(f"{i[-5:]}\t{c['nome']}\t{dono['nome']}\t{fonte}\t{arquivo}\t{'propio' if i == c['dono'] else 'anexionado'}")
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("\n".join(filas) + "\n", encoding="utf-8")


def generar(carpeta: Path = CARPETA) -> list[Path]:
    mapa = MapaGalicia()
    estado = estado_episodio1(mapa)
    carpeta.mkdir(parents=True, exist_ok=True)

    alto = E.ALTO - E.MARGEN_INF - MAPA_Y0 - 6
    img = fondo_foto(E.ANCHO, E.ALTO)
    d = ImageDraw.Draw(img)
    E.texto_centrado(d, E.ANCHO / 2, 232, "CONCELLO DE BATALLA", E.T_TITULO, E.ORO, borde=9)
    E.texto_centrado(d, E.ANCHO / 2, 318, "Ep. 1", E.T_SUBTITULO, E.BLANCO, borde=7)
    banda = mapa.dibujar(estado, mapa.ventana_general(E.ANCHO / alto), E.ANCHO, alto, )
    img.paste(banda, (0, MAPA_Y0))
    d.rectangle((0, MAPA_Y0 - 6, E.ANCHO, MAPA_Y0 - 1), fill=E.ORO)
    d.rectangle((0, MAPA_Y0 + alto, E.ANCHO, MAPA_Y0 + alto + 5), fill=E.ORO)
    r1 = carpeta / "mapa_episodio1.png"
    img.save(r1)

    ancho = 2160
    ventana = mapa.ventana_general(1.0)
    prop = (ventana[2] - ventana[0]) / (ventana[3] - ventana[1])
    r2 = carpeta / "mapa_episodio1_grande.png"
    mapa.dibujar(estado, ventana, ancho, round(ancho / prop), ).save(r2)

    r3 = carpeta / "territorios_episodio1.tsv"
    tabla(estado, r3)
    r4 = E.RAIZ / "data" / "processed" / "estado_episodio1.json"
    r4.write_text(json.dumps(estado, ensure_ascii=False, indent=1), encoding="utf-8")

    ordes = next(i for i, c in estado["concellos"].items() if c["nome"] == DUENO)
    t = estado["donos"][ordes]["territorio"]
    total = mapa.gdf.geometry.area.sum()
    sup = mapa.geometria(t).area / total
    print(f"{DUENO}: {len(t)} concellos, {sup:.1%} de la superficie, {estado['donos'][ordes]['vacas']} vacas")
    print("Concellos:", ", ".join(sorted(estado["concellos"][i]["nome"] for i in t)))
    return [r1, r2, r3, r4]


if __name__ == "__main__":
    for r in generar():
        print(r)
