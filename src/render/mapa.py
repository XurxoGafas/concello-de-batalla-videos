"""Mapa de Galicia (paso 4.2): coloreado por dueño, con nombres y vistas con zoom.

`MapaGalicia` carga una vez las geometrías (ya simplificadas, en UTM 29N) y dibuja cualquier
ventana del mapa sobre un estado de la partida:

- Cada concello se rellena con el color de su **dueño actual** (bandera o provisional).
- **Nombres (decisión del usuario):** con 313 concellos no se leerían, así que el mapa general
  NO lleva nombres. Solo se escriben, en las vistas con zoom, los de los concellos en conflicto
  (`nombres=[...]`): el del dueño, una sola vez sobre su territorio completo (un territorio
  conquistado muestra el nombre del ganador), entre `MIN_ETIQUETA` y `MAX_ETIQUETA` px, en una
  o dos líneas, y siempre dentro de la imagen.
- `contornos` permite resaltar cualquier geometría (el atacante en dorado, los concellos en
  conflicto en rojo...).
- `ventana_general` y `ventana_atacante` calculan el encuadre; la segunda enseña todo el
  territorio del atacante y todos los vecinos enemigos entre los que saldrá el defensor.
"""

from __future__ import annotations

import functools
import math
from collections.abc import Iterable

import geopandas as gpd
from PIL import Image, ImageChops, ImageDraw
from shapely.geometry.base import BaseGeometry
from shapely.ops import polylabel, unary_union

from src.motor.seleccion import territorio, vecinos_enemigos
from src.render import estilo as E

GEOJSON = E.RAIZ / "data" / "processed" / "concellos.geojson"
SUPERMUESTREO = 2
MIN_ETIQUETA = 30  # por debajo no se lee bien en un móvil: mejor no poner el nombre
MAX_ETIQUETA = 52
HOLGURA = 0.9  # fracción del ancho/alto del territorio que puede ocupar el nombre
MIN_ESCUDO_PX = 4       # un escudo más pequeño que esto (en px) no se dibuja
FRAC_ESCUDO = 1.0       # alto del escudo respecto al diámetro del mayor círculo que cabe en el territorio
MAX_ESCUDO_PX = 1400    # alto máximo del escudo (px)


@functools.lru_cache(maxsize=None)
def _bandera(ine: str) -> Image.Image | None:
    """Imagen RGBA de la bandera del concello `ine` (None si no hay archivo)."""
    ruta = E.RAIZ / "assets" / "banderas" / f"{ine}.png"
    return Image.open(ruta).convert("RGBA") if ruta.exists() else None


def poligonos(geom: BaseGeometry) -> list:
    return list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]


def pintar(d: ImageDraw.ImageDraw, geom: BaseGeometry, f, relleno, contorno, ancho: int = 1) -> None:
    for poli in poligonos(geom):
        d.polygon([f(*p) for p in poli.exterior.coords], fill=relleno, outline=contorno, width=ancho)


def transformar(ventana: tuple[float, float, float, float], ancho_px: float, k: int = 1):
    """Función UTM → píxeles (×k) para que `ventana` ocupe `ancho_px` de ancho."""
    x0, y0, x1, y1 = ventana
    esc = ancho_px * k / (x1 - x0)
    return lambda x, y: ((x - x0) * esc, (y1 - y) * esc)


class MapaGalicia:
    def __init__(self, geojson=GEOJSON) -> None:
        self.gdf = gpd.read_file(geojson).to_crs(25829).set_index("id")
        self._uniones: dict[tuple, BaseGeometry] = {}
        self._centros: dict[str, tuple[float, float, float]] = {}

    # --- Geometría ---

    def geometria(self, ids: Iterable[str]) -> BaseGeometry:
        """Unión de los concellos indicados (cacheada)."""
        clave = tuple(sorted(ids))
        if clave not in self._uniones:
            geoms = [self.gdf.geometry[i] for i in clave]
            self._uniones[clave] = geoms[0] if len(geoms) == 1 else unary_union(geoms)
        return self._uniones[clave]

    def limites(self, ids: Iterable[str]) -> tuple[float, float, float, float]:
        return tuple(self.geometria(ids).bounds)  # type: ignore[return-value]

    # --- Encuadres ---

    def ventana_general(self, proporcion: float) -> tuple[float, float, float, float]:
        """Toda Galicia, con poco aire."""
        return E.caja_de_zoom(tuple(self.gdf.total_bounds), proporcion, margen=0.04)

    def ventana_atacante(self, estado: dict, dono: str, proporcion: float):
        """Territorio completo del atacante y todos sus vecinos enemigos (fase 2)."""
        ids = territorio(estado, dono) + vecinos_enemigos(estado, dono)
        return E.caja_de_zoom(self.limites(ids), proporcion)

    def ventana_enfrentamiento(self, estado: dict, atacante: str, defensor: str, proporcion: float):
        """Territorios completos de los dos bandos (fases 3 a 6)."""
        ids = territorio(estado, atacante) + territorio(estado, defensor)
        return E.caja_de_zoom(self.limites(ids), proporcion)

    # --- Dibujo ---

    def dibujar(
        self,
        estado: dict,
        ventana: tuple[float, float, float, float],
        ancho: int,
        alto: int,
        contornos: Iterable[tuple[BaseGeometry, str, int]] = (),
        nombres: Iterable[str] = (),
        unir_territorios: bool = True,
        banderas: bool = True,
        disposicion: dict[str, Iterable[str]] | None = None,
    ) -> Image.Image:
        """Imagen RGB `ancho`×`alto` con la `ventana` del mapa (el «mar» es azul cielo).

        `nombres`: ids de los dueños cuyo nombre se escribe sobre su territorio (los que están
        en conflicto). Por defecto, ninguno.

        `unir_territorios` (por defecto sí): cada dueño con varios concellos es UN territorio, sin
        fronteras interiores y con una sola bandera o un solo escudo. Con False, cada concello se
        dibuja por separado (bandera/escudo repetidos en cada uno).

        `banderas` (por defecto sí): los dueños con bandera se pintan con su imagen, escalada para
        cubrir su territorio y recortada por él; si no, solo con su color principal.

        `disposicion`: {dueño: ids de concellos} sobre los que se COLOCA la bandera o el escudo del
        dueño (en vez de sobre su territorio actual). Sirve para que, mientras un territorio crece
        (conquista), su bandera no cambie de escala ni de sitio: el recorte lo marca el territorio
        actual y la colocación, la disposición final.

        Colocación y tamaño de banderas y escudos dependen solo de la geometría, no del zoom: el mapa
        se ve igual al acercar o alejar la vista.
        """
        k = SUPERMUESTREO
        img = Image.new("RGB", (ancho * k, alto * k), E.MAR)
        d = ImageDraw.Draw(img)
        f = transformar(ventana, ancho, k)
        vx0, vy0, vx1, vy1 = ventana
        for i, geom in self.gdf.geometry.items():
            gx0, gy0, gx1, gy1 = geom.bounds
            if gx1 < vx0 or gx0 > vx1 or gy1 < vy0 or gy0 > vy1:
                continue  # fuera de la vista (acelera los zooms)
            dono = estado["concellos"][i]["dono"]
            pintar(d, geom, f, estado["donos"][dono]["cor"]["colores"][0], None, k)
        unidades = self._unidades(estado, unir_territorios, disposicion)
        if banderas:
            self._banderas(img, estado, unidades, ventana)
        # el escudo va entre el relleno y las fronteras: puede quedar recortado por el límite del
        # territorio, pero las fronteras se ven siempre (decisión del usuario)
        self._escudos(img, estado, unidades, ventana, k)
        for dono, ids, _ in unidades:
            geom = self._geom(ids)
            gx0, gy0, gx1, gy1 = geom.bounds
            if gx1 < vx0 or gx0 > vx1 or gy1 < vy0 or gy0 > vy1:
                continue
            pintar(d, geom, f, None, E.CONTORNO_MAPA, k)
        for geom, color, grosor in contornos:
            pintar(d, geom, f, None, color, grosor * k)
        img = img.resize((ancho, alto), Image.LANCZOS)
        self._etiquetar(img, estado, transformar(ventana, ancho, 1), list(nombres))
        return img

    # --- Piezas del dibujo ---

    def _geom(self, ids: Iterable[str]) -> BaseGeometry:
        ids = tuple(ids)
        return self.gdf.geometry[ids[0]] if len(ids) == 1 else self.geometria(ids)

    @staticmethod
    def _unidades(estado: dict, unir: bool, disposicion) -> list[tuple[str, tuple, tuple]]:
        """Piezas a dibujar: (dueño, concellos que se recortan, concellos sobre los que se coloca)."""
        if not unir:
            return [(c["dono"], (i,), (i,)) for i, c in estado["concellos"].items()]
        terr: dict[str, list[str]] = {}
        for i, c in estado["concellos"].items():
            terr.setdefault(c["dono"], []).append(i)
        disposicion = disposicion or {}
        return [(d, tuple(sorted(ids)), tuple(sorted(disposicion.get(d, ids)))) for d, ids in terr.items()]

    def _disposicion(self, ids: tuple) -> tuple[float, float, float]:
        """(x, y, radio) del punto más alejado de las fronteras del territorio `ids` (cacheado)."""
        if ids not in self._centros:
            poli = max(poligonos(self._geom(ids)), key=lambda g: g.area)
            p = polylabel(poli, tolerance=50)
            self._centros[ids] = (p.x, p.y, poli.boundary.distance(p))
        return self._centros[ids]

    @staticmethod
    def _en_vista(geom: BaseGeometry, ventana) -> bool:
        gx0, gy0, gx1, gy1 = geom.bounds
        return not (gx1 < ventana[0] or gx0 > ventana[2] or gy1 < ventana[1] or gy0 > ventana[3])

    def _mascara(self, geom: BaseGeometry, ventana, esc: float, caja: tuple[int, int, int, int]) -> Image.Image:
        """Máscara L del territorio `geom` en la región `caja` (x0, y0, x1, y1) de la imagen."""
        x0, _, _, y1 = ventana
        mascara = Image.new("L", (caja[2] - caja[0], caja[3] - caja[1]), 0)
        md = ImageDraw.Draw(mascara)
        for poli in poligonos(geom):
            md.polygon([((x - x0) * esc - caja[0], (y1 - y) * esc - caja[1]) for x, y in poli.exterior.coords], fill=255)
        return mascara

    def _banderas(self, img: Image.Image, estado: dict, unidades: list, ventana) -> None:
        """Pinta la bandera de cada dueño con bandera: escalada (sin deformar) para cubrir la caja de su
        disposición y recortada por su territorio. Solo se escala la parte visible."""
        x0, y0, x1, y1 = ventana
        esc = img.width / (x1 - x0)
        for dono, ids, lay in unidades:
            if estado["donos"][dono]["cor"].get("fonte") != "bandeira":
                continue
            bandera = _bandera(dono[-5:])
            clip = self._geom(ids)
            if bandera is None or not self._en_vista(clip, ventana):
                continue
            lx0, ly0, lx1, ly1 = self._geom(lay).bounds
            bx0, by0 = (lx0 - x0) * esc, (y1 - ly1) * esc
            w, h = (lx1 - lx0) * esc, (ly1 - ly0) * esc
            if w < 3 or h < 3:
                continue
            fac = max(w / bandera.width, h / bandera.height)
            izq, arr = (bandera.width * fac - w) / 2, (bandera.height * fac - h) / 2
            cx0, cy0, cx1, cy1 = clip.bounds
            vx0, vy0 = max(0, math.floor((cx0 - x0) * esc)), max(0, math.floor((y1 - cy1) * esc))
            vx1, vy1 = min(img.width, math.ceil((cx1 - x0) * esc)), min(img.height, math.ceil((y1 - cy0) * esc))
            if vx1 <= vx0 or vy1 <= vy0:
                continue
            caja = ((vx0 - bx0 + izq) / fac, (vy0 - by0 + arr) / fac, (vx1 - bx0 + izq) / fac, (vy1 - by0 + arr) / fac)
            caja = (max(0.0, caja[0]), max(0.0, caja[1]), min(float(bandera.width), caja[2]), min(float(bandera.height), caja[3]))
            if caja[2] - caja[0] < 1 or caja[3] - caja[1] < 1:
                continue
            trozo = bandera.resize((vx1 - vx0, vy1 - vy0), Image.LANCZOS, box=caja)
            mascara = ImageChops.multiply(self._mascara(clip, ventana, esc, (vx0, vy0, vx1, vy1)), trozo.getchannel("A"))
            img.paste(trozo, (vx0, vy0), mascara)

    def _escudos(self, img: Image.Image, estado: dict, unidades: list, ventana, k: int) -> None:
        """Un escudo por pieza (dueño con solo escudo): centrado en el punto más ancho de su disposición,
        con tamaño proporcional a ese ancho y recortado por el territorio. No depende del zoom."""
        x0, y0, x1, y1 = ventana
        esc = img.width / (x1 - x0)
        for dono, ids, lay in unidades:
            ruta = estado["donos"][dono]["cor"].get("escudo")
            clip = self._geom(ids)
            if not ruta or not self._en_vista(clip, ventana):
                continue
            cx, cy, radio = self._disposicion(lay)
            diametro = 2 * radio * esc
            alto = round(min(MAX_ESCUDO_PX * k, diametro * FRAC_ESCUDO))
            if alto < MIN_ESCUDO_PX * k:
                continue
            sprite = E.escudo(ruta, alto)
            if sprite.width > diametro * 1.1:  # escudo muy ancho: que quepa en el círculo inscrito
                sprite = E.escudo(ruta, max(1, round(alto * diametro * 1.1 / sprite.width)))
            ox = round((cx - x0) * esc - sprite.width / 2)
            oy = round((y1 - cy) * esc - sprite.height / 2)
            caja = (max(0, ox), max(0, oy), min(img.width, ox + sprite.width), min(img.height, oy + sprite.height))
            if caja[2] <= caja[0] or caja[3] <= caja[1]:
                continue
            trozo = sprite.crop((caja[0] - ox, caja[1] - oy, caja[2] - ox, caja[3] - oy))
            mascara = ImageChops.multiply(self._mascara(clip, ventana, esc, caja), trozo.getchannel("A"))
            img.paste(trozo, caja[:2], mascara)

    def _etiquetar(self, img: Image.Image, estado: dict, f, duenos: list[str]) -> list[str]:
        """Escribe el nombre de cada dueño de `duenos` sobre su territorio; devuelve los nombres."""
        ancho, alto = img.size
        d = ImageDraw.Draw(img)
        escritos: list[str] = []
        for dono in duenos:
            nombre = estado["donos"][dono]["nome"]
            geom = self.geometria(estado["donos"][dono]["territorio"])
            xa, _ = f(geom.bounds[0], geom.bounds[3])
            xb, _ = f(geom.bounds[2], geom.bounds[1])
            cx, cy = f(*geom.representative_point().coords[0])
            lineas, tam = E.dividir_nombre(nombre, MAX_ETIQUETA, HOLGURA * (xb - xa), minimo=MIN_ETIQUETA)
            paso = tam * 1.05
            w = max(E.ancho_texto(x, tam) for x in lineas)
            h = paso * len(lineas)
            # dentro de la imagen aunque el territorio quede cortado por el borde de la vista
            cx = min(max(cx, w / 2 + 10), ancho - w / 2 - 10)
            cy = min(max(cy, h / 2 + 10), alto - h / 2 - 10)
            escritos.append(nombre)
            for n, linea in enumerate(lineas):
                y = cy + (n - (len(lineas) - 1) / 2) * paso
                E.texto_centrado_exacto(d, cx, y, linea, tam, E.BLANCO, borde=5, color_borde=E.FONDO)
        return escritos
