"""Guía visual del proyecto (paso 4.1): constantes y utilidades de dibujo.

Todo el aspecto de los vídeos sale de aquí para que cambiarlo sea tocar un solo archivo.
Ver `docs/ESTILO.md` para la explicación de cada decisión.
"""

from __future__ import annotations

from pathlib import Path

from PIL import ImageDraw, ImageFont

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
