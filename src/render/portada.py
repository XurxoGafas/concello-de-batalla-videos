"""Portada-gancho (paso 4.7): escena 0, antes del mapa.

Fondo negro, silueta grande del concello protagonista con los colores de su bandera y una frase gancho
ambigua en gallego (el nombre del concello va en dorado). El primer fotograma es la portada del vídeo
(se exporta también como PNG). Tras `D_FIJA` segundos, la silueta encoge y vuela hasta su sitio en el
mapa de Galicia mientras el negro se abre al mapa de la intro: es un único plano continuo y el último
fotograma de la portada es exactamente el primero de la intro.
"""

from __future__ import annotations

import math

from PIL import Image, ImageDraw

from src.motor.momentos import MARCA_A, MARCA_B, Portada
from src.render import enfrentamiento as M
from src.render import estilo as E
from src.render.mapa import MapaGalicia, pintar, transformar

D_FIJA, D_VUELO = 2.0, 0.8
CX = 510                      # centro horizontal dentro de las zonas seguras (60 … 140 px)
SIL_ANCHO, SIL_ALTO, SIL_Y = 860, 700, 600   # caja de la silueta (centro vertical SIL_Y)
TEXTO_ANCHO, TEXTO_Y0, TEXTO_Y1 = 860, 1010, 1490
TAM_MAX, TAM_MIN, MAX_LINEAS = 104, 58, 4
NEGRO = "#000000"
K = 2  # supermuestreo de la silueta


def _facil(u: float) -> float:
    u = max(0.0, min(1.0, u))
    return u * u * u * (u * (6 * u - 15) + 10)


def partir_frase(texto: str, tam_max: int = TAM_MAX, tam_min: int = TAM_MIN, ancho: int = TEXTO_ANCHO,
                 max_lineas: int = MAX_LINEAS) -> tuple[list[list[tuple[str, bool]]], int]:
    """Reparte la frase en líneas de palabras (palabra, ¿es el nombre?) que quepan en `ancho`.
    Devuelve las líneas y el tamaño de letra: el mayor (≤ tam_max) con el que caben en `max_lineas`."""
    palabras: list[tuple[str, bool]] = []
    dentro = False
    for trozo in texto.replace(MARCA_A, f" {MARCA_A} ").replace(MARCA_B, f" {MARCA_B} ").split():
        if trozo == MARCA_A:
            dentro = True
        elif trozo == MARCA_B:
            dentro = False
        else:
            palabras.append((trozo, dentro))
    tam = tam_max
    while True:
        lineas: list[list[tuple[str, bool]]] = [[]]
        for p in palabras:
            prueba = " ".join(w for w, _ in lineas[-1] + [p])
            if lineas[-1] and E.ancho_texto(prueba, tam) > ancho:
                lineas.append([p])
            else:
                lineas[-1].append(p)
        if len(lineas) <= max_lineas or tam <= tam_min:
            return lineas, tam
        tam -= 2


def _silueta(geom, ancho: int, alto: int, color: str) -> Image.Image:
    """Silueta RGBA de `ancho`×`alto` que encaja exactamente en la caja de la geometría (sin aire)."""
    minx, miny, maxx, maxy = geom.bounds
    esc = ancho * K / (maxx - minx)
    f = lambda x, y: ((x - minx) * esc, (maxy - y) * esc)  # noqa: E731
    im = Image.new("RGBA", (ancho * K, alto * K), (0, 0, 0, 0))
    pintar(ImageDraw.Draw(im), geom, f, color, E.BLANCO, 5 * K)
    return im.resize((ancho, alto), Image.LANCZOS)


class EscenaPortada:
    fundido = 0.0
    duracion = D_FIJA + D_VUELO

    def __init__(self, estado: dict, portada: Portada, mapa: MapaGalicia, intro: Image.Image, ventana_general,
                 alto_mapa: int) -> None:
        self.intro = intro
        geom = mapa.geometria([portada.concello])
        minx, miny, maxx, maxy = geom.bounds
        # --- tamaño de la silueta en la portada: encaja en la caja SIL_ANCHO × SIL_ALTO
        esc = min(SIL_ANCHO / (maxx - minx), SIL_ALTO / (maxy - miny))
        w0, h0 = max(8, round((maxx - minx) * esc)), max(8, round((maxy - miny) * esc))
        color = estado["concellos"][portada.concello]["cor"]["colores"][0]
        self.sil = _silueta(geom, w0, h0, color)
        self.caja0 = (CX - w0 / 2, SIL_Y - h0 / 2, CX + w0 / 2, SIL_Y + h0 / 2)
        # --- dónde está ese concello en el mapa general de la intro
        t = transformar(ventana_general, E.ANCHO)
        (ax, ay), (bx, by) = t(minx, maxy), t(maxx, miny)
        self.caja1 = (ax, M.MAPA_Y0 + ay, bx, M.MAPA_Y0 + by)
        # --- fotograma de texto (fondo negro + frase)
        self.texto_img = self._texto(portada)
        self.fondo = self.texto_img
        self.negro = Image.new("RGB", (E.ANCHO, E.ALTO), NEGRO)

    def _texto(self, portada: Portada) -> Image.Image:
        img = Image.new("RGB", (E.ANCHO, E.ALTO), NEGRO)
        d = ImageDraw.Draw(img)
        lineas, tam = partir_frase(portada.texto)
        tiene_nombre = any(es for l in lineas for _, es in l)
        if not tiene_nombre:  # frase sin el nombre (p. ej. «Carallo, que tirada!»): se pone debajo, en dorado
            lineas = lineas + [[(portada.nombre, True)]]
        paso = round(tam * 1.12)
        alto_bloque = paso * (len(lineas) - 1) + tam
        y = TEXTO_Y0 + max(0, (TEXTO_Y1 - TEXTO_Y0 - alto_bloque) / 2) + tam * 0.8
        f = E.fuente(tam)
        for linea in lineas:
            ancho_l = E.ancho_texto(" ".join(w for w, _ in linea), tam)
            x = CX - ancho_l / 2
            for w, es in linea:
                E.texto_con_borde(d, (x, y), w, f, E.ORO if es else E.BLANCO, "ls", 0, NEGRO)
                x += E.ancho_texto(w + " ", tam)
            y += paso
        return img

    def _poner_silueta(self, img: Image.Image, caja, opacidad: float = 1.0) -> None:
        w, h = max(1, round(caja[2] - caja[0])), max(1, round(caja[3] - caja[1]))
        s = self.sil.resize((w, h), Image.LANCZOS)
        if opacidad < 1.0:
            s = s.copy()
            s.putalpha(s.getchannel("A").point(lambda v: round(v * opacidad)))
        img.paste(s, (round(caja[0]), round(caja[1])), s)

    def fotograma(self, t: float) -> Image.Image:
        if t >= self.duracion:
            return self.intro.copy()
        if t < D_FIJA:  # latido suave de la silueta (en t = 0 es exactamente la portada)
            img = self.texto_img.copy()
            p = 1 + 0.025 * math.sin(2 * math.pi * t / 1.0) if t > 0 else 1.0
            cx, cy = CX, SIL_Y
            w, h = (self.caja0[2] - self.caja0[0]) * p, (self.caja0[3] - self.caja0[1]) * p
            self._poner_silueta(img, (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))
            return img
        u = _facil((t - D_FIJA) / D_VUELO)
        # texto: se apaga en el primer tercio; fondo: se abre al mapa
        texto = Image.blend(self.texto_img, self.negro, min(1.0, u / 0.35))
        a = _facil((u - 0.15) / 0.85)
        img = Image.blend(texto, self.intro, a)
        # al llegar a su sitio se funde con el concello real del mapa (sin salto de color)
        self._poner_silueta(img, _caja_vuelo(self.caja0, self.caja1, u), 1 - _facil((u - 0.6) / 0.4))
        return img


def _caja_vuelo(c0, c1, u: float):
    """Caja intermedia: tamaño exponencial y centro proporcional al zoom (como el zoom del mapa)."""
    w0, h0, w1, h1 = c0[2] - c0[0], c0[3] - c0[1], c1[2] - c1[0], c1[3] - c1[1]
    cx0, cy0, cx1, cy1 = (c0[0] + c0[2]) / 2, (c0[1] + c0[3]) / 2, (c1[0] + c1[2]) / 2, (c1[1] + c1[3]) / 2
    w, h = w0 * (w1 / w0) ** u, h0 * (h1 / h0) ** u
    s = u if abs(w1 - w0) < 1e-6 * w0 else (1 / w - 1 / w0) / (1 / w1 - 1 / w0)
    cx, cy = cx0 + (cx1 - cx0) * s, cy0 + (cy1 - cy0) * s
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
