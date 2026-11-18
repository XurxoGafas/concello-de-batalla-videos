"""Dados y utilidades de animación (paso 4.4).

Sprites RGBA (dado, insignia «+N», espadas cruzadas), funciones de suavizado y la geometría de
las dos columnas de dados (una por bando, tres filas), que debe coincidir con la de las
muestras estáticas (`muestra_estilo.py`).
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageDraw

from src.render import estilo as E

# Geometría de las columnas de dados (y de la zona de dados en el panel)
LADO, SEP, Y0 = 80, 10, 1222
COL_A, COL_D = 235, E.ANCHO - 235
ALTO_ZONA = 3 * LADO + 2 * SEP  # 260
Y_MEDIO = Y0 + ALTO_ZONA // 2


def y_fila(i: int) -> int:
    """Y superior del dado de la fila i (0..2)."""
    return Y0 + i * (LADO + SEP)


# ---------- Suavizado ----------

def limitar(t: float) -> float:
    return max(0.0, min(1.0, t))


def salida_cubica(t: float) -> float:
    t = limitar(t)
    return 1 - (1 - t) ** 3


def salida_rebote(t: float) -> float:
    """Pasa de 0 a 1 con un pequeño rebasamiento («pop»)."""
    t = limitar(t)
    c1, c3 = 1.70158, 2.70158
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


# ---------- Sprites ----------

def dado_sprite(lado: int, valor: int, resaltado: bool = False) -> Image.Image:
    """Dado como RGBA con margen para el borde dorado (el sprite mide lado + 2·MARGEN)."""
    m = 8
    img = Image.new("RGBA", (lado + 2 * m, lado + 2 * m), (0, 0, 0, 0))
    E.dibujar_dado(ImageDraw.Draw(img), m, m, lado, valor, resaltado=resaltado)
    return img


def hueco_sprite(lado: int) -> Image.Image:
    """Hueco vacío donde caerá un dado."""
    m = 8
    img = Image.new("RGBA", (lado + 2 * m, lado + 2 * m), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((m, m, m + lado, m + lado), radius=lado // 5,
                                          fill=(236, 239, 244, 255), outline=(176, 183, 196, 255), width=3)
    return img


def insignia_sprite(texto: str, color: str) -> Image.Image:
    """Insignia redondeada con texto blanco («+2» en verde, «=» en gris)."""
    w = max(76, int(E.ancho_texto(texto, 50)) + 30)
    h = 60
    img = Image.new("RGBA", (w + 8, h + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((4, 4, 4 + w, 4 + h), radius=30, fill=color, outline=E.FONDO, width=4)
    E.texto_centrado_exacto(d, 4 + w / 2, 4 + h / 2, texto, 50, E.BLANCO)
    return img


def espadas_sprite(tam: int = 260) -> Image.Image:
    """Icono de dos espadas cruzadas (dibujado por código, sin imágenes externas)."""
    k, S = 3, 400
    def espada() -> Image.Image:
        im = Image.new("RGBA", (S * k, S * k), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        def poly(p, fill, w=7):
            d.polygon([(x * k, y * k) for x, y in p], fill=fill, outline=E.FONDO, width=w * k)
        poly([(200, 10), (226, 70), (226, 255), (174, 255), (174, 70)], "#DDE3EE")  # hoja
        d.line([(200 * k, 40 * k), (200 * k, 250 * k)], fill="#A9B4C8", width=6 * k)  # canal
        poly([(120, 255), (280, 255), (280, 285), (120, 285)], E.ORO)  # guarda
        poly([(188, 285), (212, 285), (212, 350), (188, 350)], "#7A4A21")  # empuñadura
        d.ellipse((178 * k, 345 * k, 222 * k, 389 * k), fill=E.ORO, outline=E.FONDO, width=7 * k)
        return im
    e = espada()
    img = Image.new("RGBA", e.size, (0, 0, 0, 0))
    for ang in (45, -45):
        img.alpha_composite(e.rotate(ang, resample=Image.BICUBIC))
    return img.resize((tam, tam), Image.LANCZOS)


# ---------- Pegado con escala y opacidad ----------

def pegar(img: Image.Image, sprite: Image.Image, cx: float, cy: float,
          escala: float = 1.0, opacidad: float = 1.0) -> None:
    """Pega `sprite` centrado en (cx, cy), escalado y con opacidad (0–1)."""
    if escala <= 0.02 or opacidad <= 0:
        return
    if abs(escala - 1) > 1e-3:
        sprite = sprite.resize((max(1, round(sprite.width * escala)), max(1, round(sprite.height * escala))),
                               Image.LANCZOS)
    alfa = sprite.getchannel("A")
    if opacidad < 1:
        alfa = alfa.point(lambda v: int(v * opacidad))
    img.paste(sprite.convert("RGB"), (round(cx - sprite.width / 2), round(cy - sprite.height / 2)), alfa)


def cara_rodando(clave: str, t: float, ritmo: float = 14.0) -> int:
    """Cara que se muestra mientras el dado rueda (cambia `ritmo` veces por segundo, determinista)."""
    return random.Random(f"{clave}:{int(t * ritmo)}").randint(1, 6)


def rebote(t: float, dur: float, alto: float = 14.0) -> float:
    """Desplazamiento vertical (px, hacia arriba negativo) de un dado que rueda y se frena."""
    u = limitar(t / dur)
    return -abs(math.sin(u * 5 * math.pi)) * alto * (1 - u)
