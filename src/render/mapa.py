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
MIN_LADO_ESCUDO = 26    # un concello más pequeño que esto (en px) no lleva escudo
FRAC_ESCUDO = 1.0       # alto del escudo respecto al «lado» del concello (raíz de su área en px)
MAX_ESCUDO = 230        # alto máximo del escudo (px)
MAX_ESCUDO_TERRITORIO = 420  # alto máximo del escudo único de un territorio de varios concellos (px)


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
        unir_territorios: bool = False,
        banderas: bool = False,
    ) -> Image.Image:
        """Imagen RGB `ancho`×`alto` con la `ventana` del mapa (el «mar» es azul marino).

        `nombres`: ids de los dueños cuyo nombre se escribe sobre su territorio (los que están
        en conflicto). Por defecto, ninguno.

        `unir_territorios`: si es True, cada dueño con varios concellos se dibuja como UN territorio:
        sin fronteras interiores y con su escudo una sola vez (grande, en el punto más «ancho» del
        territorio). Si es False (vídeo), se mantiene el comportamiento anterior.
        """
        k = SUPERMUESTREO
        img = Image.new("RGB", (ancho * k, alto * k), E.MAR)
        d = ImageDraw.Draw(img)
        f = transformar(ventana, ancho, k)
        vx0, vy0, vx1, vy1 = ventana
        visibles = []
        for i, geom in self.gdf.geometry.items():
            gx0, gy0, gx1, gy1 = geom.bounds
            if gx1 < vx0 or gx0 > vx1 or gy1 < vy0 or gy0 > vy1:
                continue  # fuera de la vista (acelera los zooms)
            dono = estado["concellos"][i]["dono"]
            pintar(d, geom, f, estado["donos"][dono]["cor"]["colores"][0], None, k)
            visibles.append(geom)
        if banderas:
            self._banderas(img, estado, ventana, k)
        # el escudo va entre el relleno y las fronteras: puede quedar recortado por el límite del
        # concello, pero las fronteras se ven siempre (decisión del usuario)
        self._escudos(img, estado, ventana, list(nombres), k, unir_territorios)
        if unir_territorios:
            for dono, info in estado["donos"].items():
                if len(info["territorio"]) == 1:
                    geom = self.gdf.geometry[info["territorio"][0]]
                else:
                    geom = self.geometria(info["territorio"])
                gx0, gy0, gx1, gy1 = geom.bounds
                if gx1 < vx0 or gx0 > vx1 or gy1 < vy0 or gy0 > vy1:
                    continue
                pintar(d, geom, f, None, E.CONTORNO_MAPA, k)
        else:
            for geom in visibles:
                pintar(d, geom, f, None, E.CONTORNO_MAPA, k)
        for geom, color, grosor in contornos:
            pintar(d, geom, f, None, color, grosor * k)
        img = img.resize((ancho, alto), Image.LANCZOS)
        self._etiquetar(img, estado, transformar(ventana, ancho, 1), list(nombres))
        return img

    def _centro(self, i: str) -> tuple[float, float, float]:
        """(x, y, área) de un punto interior del concello `i` (cacheado)."""
        if i not in self._centros:
            g = self.gdf.geometry[i]
            p = g.representative_point()
            self._centros[i] = (p.x, p.y, g.area)
        return self._centros[i]

    def _banderas(self, img: Image.Image, estado: dict, ventana, k: int) -> None:
        """Pinta la imagen de la bandera de cada dueño con bandera, cubriendo la caja de su territorio
        (sin deformarla) y recortada por el contorno del territorio. `img` está a escala ×k."""
        x0, y0, x1, y1 = ventana
        esc = img.width / (x1 - x0)
        for dono, info in estado["donos"].items():
            if info["cor"].get("fonte") != "bandeira":
                continue
            bandera = _bandera(dono[-5:])
            if bandera is None:
                continue
            ids = info["territorio"]
            geom = self.gdf.geometry[ids[0]] if len(ids) == 1 else self.geometria(ids)
            gx0, gy0, gx1, gy1 = geom.bounds
            if gx1 < x0 or gx0 > x1 or gy1 < y0 or gy0 > y1:
                continue
            bx0, by0 = round((gx0 - x0) * esc), round((y1 - gy1) * esc)
            w, h = max(1, round((gx1 - gx0) * esc)), max(1, round((gy1 - gy0) * esc))
            if w < 3 or h < 3:
                continue
            fac = max(w / bandera.width, h / bandera.height)
            grande = bandera.resize((max(w, round(bandera.width * fac)), max(h, round(bandera.height * fac))), Image.LANCZOS)
            izq, arr = (grande.width - w) // 2, (grande.height - h) // 2
            grande = grande.crop((izq, arr, izq + w, arr + h))
            mascara = Image.new("L", (w, h), 0)
            md = ImageDraw.Draw(mascara)
            for p in poligonos(geom):
                md.polygon([((x - x0) * esc - bx0, (y1 - y) * esc - by0) for x, y in p.exterior.coords], fill=255)
            mascara = ImageChops.multiply(mascara, grande.getchannel("A"))
            img.paste(grande, (bx0, by0), mascara)

    def _escudo_territorio(self, img: Image.Image, estado: dict, dono: str, ventana, k: int) -> None:
        """Un único escudo para todo el territorio de `dono` (varios concellos), centrado en el punto
        interior más alejado de las fronteras y recortado por el contorno del territorio."""
        ruta = estado["donos"][dono]["cor"]["escudo"]
        geom = self.geometria(estado["donos"][dono]["territorio"])
        poli = max(poligonos(geom), key=lambda g: g.area)
        punto = polylabel(poli, tolerance=50)
        radio = poli.boundary.distance(punto)
        x0, y0, x1, y1 = ventana
        esc = img.width / (x1 - x0)
        alto = round(min(MAX_ESCUDO_TERRITORIO, 2 * radio * esc / k * 1.1) * k)
        if alto < MIN_LADO_ESCUDO * k:
            return
        sprite = E.escudo(ruta, alto)
        px, py = (punto.x - x0) * esc, (y1 - punto.y) * esc
        ox, oy = round(px - sprite.width / 2), round(py - sprite.height / 2)
        mascara = Image.new("L", sprite.size, 0)
        md = ImageDraw.Draw(mascara)
        for p in poligonos(geom):
            md.polygon([((x - x0) * esc - ox, (y1 - y) * esc - oy) for x, y in p.exterior.coords], fill=255)
        mascara = ImageChops.multiply(mascara, sprite.getchannel("A"))
        img.paste(sprite, (ox, oy), mascara)

    def _escudos(self, img: Image.Image, estado: dict, ventana, nombres: list[str], k: int,
                 unir: bool = False) -> None:
        """Dibuja el escudo del dueño sobre cada concello suyo que tenga solo escudo (territorio blanco),
        recortado por el límite del concello. Los concellos demasiado pequeños se quedan sin escudo.
        `img` está a escala ×k."""
        x0, y0, x1, y1 = ventana
        esc = img.width / (x1 - x0)
        for i, c in estado["concellos"].items():
            ruta = estado["donos"][c["dono"]]["cor"].get("escudo")
            if not ruta:
                continue
            if unir and len(estado["donos"][c["dono"]]["territorio"]) > 1:
                continue  # su escudo se dibuja una sola vez, abajo
            cx, cy, area = self._centro(i)
            if not (x0 <= cx <= x1 and y0 <= cy <= y1):
                continue
            lado = (area ** 0.5) * esc / k
            if lado < MIN_LADO_ESCUDO:
                continue
            alto = round(min(MAX_ESCUDO, lado * FRAC_ESCUDO) * k)
            sprite = E.escudo(ruta, alto)
            px, py = (cx - x0) * esc, (y1 - cy) * esc
            if c["dono"] in nombres:
                py -= alto * 0.15  # deja sitio al nombre
            ox, oy = round(px - sprite.width / 2), round(py - sprite.height / 2)
            mascara = Image.new("L", sprite.size, 0)
            md = ImageDraw.Draw(mascara)
            for poli in poligonos(self.gdf.geometry[i]):
                md.polygon([((x - x0) * esc - ox, (y1 - y) * esc - oy) for x, y in poli.exterior.coords], fill=255)
            mascara = ImageChops.multiply(mascara, sprite.getchannel("A"))
            img.paste(sprite, (ox, oy), mascara)
        if unir:
            for dono, info in estado["donos"].items():
                if len(info["territorio"]) > 1 and info["cor"].get("escudo"):
                    self._escudo_territorio(img, estado, dono, ventana, k)

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
