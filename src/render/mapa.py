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

from collections.abc import Iterable

import geopandas as gpd
from PIL import Image, ImageDraw
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from src.motor.seleccion import territorio, vecinos_enemigos
from src.render import estilo as E

GEOJSON = E.RAIZ / "data" / "processed" / "concellos.geojson"
SUPERMUESTREO = 2
MIN_ETIQUETA = 30  # por debajo no se lee bien en un móvil: mejor no poner el nombre
MAX_ETIQUETA = 52
HOLGURA = 0.9  # fracción del ancho/alto del territorio que puede ocupar el nombre


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
    ) -> Image.Image:
        """Imagen RGB `ancho`×`alto` con la `ventana` del mapa (el «mar» es azul marino).

        `nombres`: ids de los dueños cuyo nombre se escribe sobre su territorio (los que están
        en conflicto). Por defecto, ninguno.
        """
        k = SUPERMUESTREO
        img = Image.new("RGB", (ancho * k, alto * k), E.FONDO)
        d = ImageDraw.Draw(img)
        f = transformar(ventana, ancho, k)
        for i, geom in self.gdf.geometry.items():
            dono = estado["concellos"][i]["dono"]
            pintar(d, geom, f, estado["donos"][dono]["cor"]["colores"][0], E.CONTORNO_MAPA, k)
        for geom, color, grosor in contornos:
            pintar(d, geom, f, None, color, grosor * k)
        img = img.resize((ancho, alto), Image.LANCZOS)
        self._etiquetar(img, estado, transformar(ventana, ancho, 1), list(nombres))
        return img

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
