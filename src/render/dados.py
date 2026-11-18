"""Dados y utilidades de animación (paso 4.4).

Sprites RGBA (dado, insignia «+N», navaja y botella de licor café), funciones de suavizado y la geometría de
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


def navaja_botella_sprite(tam: int = 260) -> Image.Image:
    """Icono del duelo: navaja de bolsillo gallega (mango de madera, hoja abierta) cruzada con una
    botella de licor café. Dibujado por código, sin imágenes externas."""
    k, S, P = 3, 400, 520  # supermuestreo, lienzo de cada objeto y lienzo final (con holgura al girar)

    def lienzo() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        im = Image.new("RGBA", (S * k, S * k), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def poli(d, pts, fill, w=7):
        d.polygon([(x * k, y * k) for x, y in pts], fill=fill, outline=E.FONDO, width=w * k)

    def rect(d, caja, fill, r=14, w=7):
        x0, y0, x1, y1 = caja
        d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), radius=r * k, fill=fill, outline=E.FONDO, width=w * k)

    # --- Navaja: hoja plateada con lomo curvo, virola de latón y mango de madera con vetas y remaches ---
    nav, d = lienzo()
    poli(d, [(176, 195), (226, 195), (230, 140), (221, 80), (196, 14), (186, 70), (178, 130)], "#DDE3EE")
    d.line([(196 * k, 40 * k), (200 * k, 190 * k)], fill="#A9B4C8", width=5 * k)  # filo / canal
    poli(d, [(172, 214), (230, 214), (238, 372), (164, 372)], "#9A5B2B")  # mango de madera
    for x0, x1 in ((182, 186), (200, 206), (218, 221)):  # vetas
        d.line([(x0 * k, 226 * k), (x1 * k, 360 * k)], fill="#C58A52", width=4 * k)
    rect(d, (166, 190, 236, 220), E.ORO, r=8)  # virola de latón
    for cy in (240, 346):  # remaches
        d.ellipse((194 * k, (cy - 7) * k, 208 * k, (cy + 7) * k), fill=E.ORO, outline=E.FONDO, width=4 * k)

    # --- Botella de licor café: vidrio marrón oscuro, tapón dorado y etiqueta crema con «CAFÉ» ---
    bot, d = lienzo()
    poli(d, [(150, 196), (172, 150), (181, 112), (219, 112), (228, 150), (250, 196)], "#4A2511")  # hombros
    rect(d, (150, 180, 250, 385), "#4A2511", r=18)  # cuerpo
    rect(d, (181, 70, 219, 120), "#4A2511", r=6)  # cuello
    rect(d, (175, 38, 225, 76), E.ORO, r=8)  # tapón
    d.rounded_rectangle((161 * k, 205 * k, 171 * k, 365 * k), radius=5 * k, fill="#8A5230")  # reflejo
    rect(d, (160, 235, 240, 330), "#F4E9D0", r=10, w=5)  # etiqueta
    f = E.fuente(34 * k)
    d.text((200 * k, 283 * k), "CAFÉ", font=f, fill=E.FONDO, anchor="mm")

    def girar(im: Image.Image, grados: float, dx: float) -> Image.Image:
        lienzo_p = Image.new("RGBA", (P * k, P * k), (0, 0, 0, 0))
        lienzo_p.alpha_composite(im, (((P - S) // 2 + int(dx)) * k, ((P - S) // 2) * k))
        return lienzo_p.rotate(grados, resample=Image.BICUBIC, center=((P // 2 + dx) * k, P // 2 * k))

    icono = girar(nav, -22, -78)  # la navaja se inclina hacia la derecha…
    icono.alpha_composite(girar(bot, 16, 78))  # …y la botella hacia la izquierda: se cruzan arriba
    caja = icono.getbbox()
    icono = icono.crop(caja)
    lado = max(icono.size)
    cuadro = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    cuadro.alpha_composite(icono, ((lado - icono.width) // 2, (lado - icono.height) // 2))
    return cuadro.resize((tam, tam), Image.LANCZOS)


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
