"""Guía visual del proyecto (paso 4.1): constantes y utilidades de dibujo.

Todo el aspecto de los vídeos sale de aquí para que cambiarlo sea tocar un solo archivo.
Ver `docs/ESTILO.md` para la explicación de cada decisión.
"""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[2]
FUENTE_TTF = RAIZ / "assets" / "fonts" / "LilitaOne-Regular.ttf"

# --- Formato de vídeo ---
ANCHO, ALTO = 1080, 1920  # vertical 9:16
FPS = 30

# --- Zonas seguras (píxeles que la interfaz de TikTok / Reels / Shorts puede tapar) ---
# Valores prudentes que cubren las tres redes; se revisarán con un vídeo real en el paso 6.3.
MARGEN_SUP = 220  # barra superior y buscador
MARGEN_INF = 420  # descripción, nombre de la cuenta, música y botones
MARGEN_IZQ = 60
MARGEN_DER = 140  # columna de botones (me gusta, comentar...)
ZONA_SEGURA = (MARGEN_IZQ, MARGEN_SUP, ANCHO - MARGEN_DER, ALTO - MARGEN_INF)  # x0, y0, x1, y1

# --- Paleta ---
FONDO = "#0B1730"  # azul marino oscuro
PANEL = "#13244D"
PANEL_BORDE = "#22376B"
ORO = "#F5B82E"  # títulos, multiplicador y línea divisoria
BLANCO = "#FFFFFF"
GRIS_AZUL = "#A9BAE0"  # texto secundario
VERDE = "#3DDC84"  # ganador
ROJO = "#FF5470"  # perdedor
MAR = "#0F2347"  # fondo del mapa (el territorio que no es Galicia)
CONTORNO_MAPA = "#0B1730"  # borde fino entre concellos
DADO_CARA = "#FFFFFF"
DADO_PUNTO = "#0B1730"
VACA_BLANCO = "#FFFFFF"  # todo lo relacionado con las vacas va «pintado como una vaca»:
VACA_MANCHA = "#141414"  # blanco con manchas negras
CONFLICTO = "#FF2D55"  # contorno rojo de los concellos que se pelean

# --- Tamaños de texto (px sobre 1080 de ancho; mínimo 44 para leerse en el móvil) ---
T_TITULO = 78
T_SUBTITULO = 52
T_NOMBRE = 56
T_DATO = 46
T_MARCADOR = 96
T_MIN = 44


def fuente(tam: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FUENTE_TTF), tam)


def ancho_texto(texto: str, tam: int) -> float:
    return fuente(tam).getlength(texto)


def texto_centrado(
    d: ImageDraw.ImageDraw, centro_x: float, y: float, texto: str, tam: int,
    color: str = BLANCO, borde: int = 0, color_borde: str = FONDO,
) -> None:
    """Dibuja `texto` centrado en `centro_x`, con `y` como borde superior del texto."""
    d.text((centro_x, y), texto, font=fuente(tam), fill=color, anchor="mt",
           stroke_width=borde, stroke_fill=color_borde)


def ajustar_tamano(texto: str, tam: int, ancho_max: float, minimo: int = T_MIN) -> int:
    """Reduce el tamaño hasta que el texto quepa en `ancho_max` (nombres largos de concello)."""
    while tam > minimo and ancho_texto(texto, tam) > ancho_max:
        tam -= 2
    return tam


def dividir_nombre(nombre: str, tam: int, ancho_max: float) -> tuple[list[str], int]:
    """Parte un nombre largo en 1 o 2 líneas que quepan en `ancho_max`.

    Si cabe en una línea no se toca; si no, se prueba cada espacio como punto de corte y se
    elige el que deja las dos líneas más equilibradas. Si aun así no cabe, se reduce el tamaño
    (hasta `T_MIN`). Devuelve las líneas y el tamaño final.
    """
    palabras = nombre.split()
    while True:
        if ancho_texto(nombre, tam) <= ancho_max:
            return [nombre], tam
        mejor = None
        for i in range(1, len(palabras)):
            a, b = " ".join(palabras[:i]), " ".join(palabras[i:])
            peor = max(ancho_texto(a, tam), ancho_texto(b, tam))
            if mejor is None or peor < mejor[0]:
                mejor = (peor, [a, b])
        if mejor and mejor[0] <= ancho_max:
            return mejor[1], tam
        if tam <= T_MIN:
            return (mejor[1] if mejor else [nombre]), tam
        tam -= 2


def luminancia(hex_color: str) -> float:
    """Luminancia relativa WCAG de un color #RRGGBB."""
    def canal(v: int) -> float:
        c = v / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def contraste(a: str, b: str) -> float:
    """Relación de contraste WCAG entre dos colores (1 a 21)."""
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def dibujar_dado(d: ImageDraw.ImageDraw, x: float, y: float, lado: int, valor: int,
                 resaltado: bool = False) -> None:
    """Dado de cara blanca con puntos oscuros; `resaltado` le pone borde dorado."""
    d.rounded_rectangle((x, y, x + lado, y + lado), radius=lado // 5, fill=DADO_CARA,
                        outline=ORO if resaltado else PANEL_BORDE, width=6 if resaltado else 3)
    c1, c2, c3 = lado * 0.27, lado * 0.5, lado * 0.73
    pos = {1: [(c2, c2)], 2: [(c1, c1), (c3, c3)], 3: [(c1, c1), (c2, c2), (c3, c3)],
           4: [(c1, c1), (c3, c1), (c1, c3), (c3, c3)],
           5: [(c1, c1), (c3, c1), (c2, c2), (c1, c3), (c3, c3)],
           6: [(c1, c1), (c3, c1), (c1, c2), (c3, c2), (c1, c3), (c3, c3)]}[valor]
    pr = lado * 0.085
    for px, py in pos:
        d.ellipse((x + px - pr, y + py - pr, x + px + pr, y + py + pr), fill=DADO_PUNTO)


def texto_centrado_exacto(
    d: ImageDraw.ImageDraw, cx: float, cy: float, texto: str, tam: int, color: str = BLANCO,
    borde: int = 0, color_borde: str = FONDO,
) -> None:
    """Centra la tinta real del texto (no su caja tipográfica) en (cx, cy), en ambos ejes."""
    f = fuente(tam)
    x0, y0, x1, y1 = d.textbbox((0, 0), texto, font=f, anchor="ls", stroke_width=borde)
    d.text((cx - (x0 + x1) / 2, cy - (y0 + y1) / 2), texto, font=f, fill=color, anchor="ls",
           stroke_width=borde, stroke_fill=color_borde)


def _mancha(rng: random.Random, cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    """Polígono irregular, más ancho que alto, como una mancha de vaca."""
    n = 11
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * rng.uniform(0.7, 1.15)
        pts.append((cx + math.cos(a) * rr * 1.35, cy + math.sin(a) * rr))
    return pts


def tamano_pastilla(texto: str | list[str], tam: int, pad_x: int = 30) -> tuple[int, int]:
    """(ancho, alto) en píxeles de `pastilla_vaca` para ese texto (una o varias líneas)."""
    lineas = [texto] if isinstance(texto, str) else texto
    w = int(max(ancho_texto(x, tam) for x in lineas) + 2 * pad_x)
    h = int(tam * 1.4 + (len(lineas) - 1) * tam * 1.15)
    return w, h


def pastilla_vaca(
    img: Image.Image, cx: float, cy: float, texto: str | list[str], tam: int,
    pad_x: int = 30, semilla: str | None = None,
) -> tuple[int, int, int, int]:
    """Pastilla blanca con manchas negras (piel de vaca pinta) con `texto` exactamente centrado.

    `texto` puede ser una lista de líneas. Las manchas salen por los bordes (arriba y abajo)
    para no quitar legibilidad al texto, que además lleva un halo blanco. Es determinista: las
    mismas manchas para el mismo texto. Devuelve la caja (x0, y0, x1, y1) ocupada.
    """
    lineas = [texto] if isinstance(texto, str) else list(texto)
    k = 3  # supermuestreo para bordes suaves
    w, h = tamano_pastilla(lineas, tam, pad_x)
    base = Image.new("RGBA", (w * k, h * k), VACA_BLANCO)
    db = ImageDraw.Draw(base)
    rng = random.Random(semilla if semilla is not None else "|".join(lineas))
    n = max(2, round(w / 75))
    for i in range(n):
        x = (i + 0.5) * w / n + rng.uniform(-0.2, 0.2) * w / n
        y = (rng.choice((0.0, 1.0)) + rng.uniform(-0.1, 0.1)) * h
        r = rng.uniform(0.2, 0.3) * min(h, 64)
        db.polygon([(a * k, b * k) for a, b in _mancha(rng, x, y, r)], fill=VACA_MANCHA)
    radio = min(h // 2, 34) * k
    mascara = Image.new("L", (w * k, h * k), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=radio, fill=255)
    db.rounded_rectangle((0, 0, w * k - 1, h * k - 1), radius=radio, outline=FONDO, width=3 * k)
    base.putalpha(mascara)
    pequena = base.resize((w, h), Image.LANCZOS)
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    img.paste(pequena.convert("RGB"), (x0, y0), pequena.getchannel("A"))
    d = ImageDraw.Draw(img)
    paso = tam * 1.15
    for i, linea in enumerate(lineas):
        y = y0 + h / 2 + (i - (len(lineas) - 1) / 2) * paso
        texto_centrado_exacto(d, x0 + w / 2, y, linea, tam, FONDO, borde=5, color_borde=VACA_BLANCO)
    return x0, y0, x0 + w, y0 + h


def caja_de_zoom(
    limites: tuple[float, float, float, float], proporcion: float,
    margen: float = 0.2, minimo: float = 40_000.0,
) -> tuple[float, float, float, float]:
    """Ventana del mapa (en metros UTM) que encuadra `limites` con aire alrededor.

    - `margen`: aire a cada lado, como fracción del tamaño (para ver los vecinos).
    - `minimo`: lado mínimo en metros, para que dos concellos pequeños no se amplíen sin
      sentido y se vea el entorno.
    - `proporcion`: ancho/alto de la zona de pantalla; la ventana se amplía (nunca se recorta)
      hasta tener esa proporción, así un territorio muy grande se ve entero con menos zoom.
    """
    minx, miny, maxx, maxy = limites
    cx, cy = (minx + maxx) / 2, (miny + maxy) / 2
    w = max((maxx - minx) * (1 + 2 * margen), minimo)
    h = max((maxy - miny) * (1 + 2 * margen), minimo)
    if w / h < proporcion:
        w = h * proporcion
    else:
        h = w / proporcion
    return cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2
