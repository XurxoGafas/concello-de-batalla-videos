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


def _recortar(im: Image.Image, ancho: int | None = None, alto: int | None = None) -> Image.Image:
    """Recorta al contenido y reescala (conserva la proporción) a `ancho` o `alto` dados."""
    im = im.crop(im.getbbox())
    esc = (ancho / im.width) if ancho else (alto / im.height)
    return im.resize((max(1, round(im.width * esc)), max(1, round(im.height * esc))), Image.LANCZOS)


def navaja_sprite(largo: int = 300, apertura: float = 55) -> Image.Image:
    """Navaja gallega **entreabierta** (se ve que es plegable): el mango de madera clara con su virola
    de acero con anillos queda en horizontal (a la derecha) y la hoja sale del extremo de la virola
    girada `apertura` grados respecto al mango (0 = cerrada, ~180 = abierta del todo).

    La hoja es afilada, con lomo recto, canal y muesca para la uña; el pasador marca el eje.
    `largo` es el ancho aproximado del conjunto."""
    k, W, H = 3, 560, 560
    ox, oy = 150, 300  # posición de la navaja en el lienzo (la hoja gira hacia arriba y a la izquierda)

    def lienzo() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
        return im, ImageDraw.Draw(im)

    def poli(d, pts, fill, w=6):
        d.polygon([((ox + x) * k, (oy + y) * k) for x, y in pts], fill=fill, outline=E.FONDO, width=w * k)

    # --- Hoja (dibujada horizontal, punta a la izquierda; después se gira sobre el pasador) ---
    hoja, d = lienzo()
    # Hoja de cuchillo (no de daga): lomo recto y sin filo (abajo en este dibujo) y filo curvo solo por el
    # lado que se cierra hacia el mango (arriba en este dibujo, que tras girar queda mirando al mango).
    poli(d, [(160, 82), (62, 82), (30, 78), (8, 70), (22, 56), (50, 44), (90, 37), (128, 35), (160, 38)], "#E9EDF3")
    d.line([((ox + 60) * k, (oy + 70) * k), ((ox + 150) * k, (oy + 70) * k)], fill="#A9B4C8", width=4 * k)  # canal
    d.line([((ox + 40) * k, (oy + 52) * k), ((ox + 150) * k, (oy + 43) * k)], fill="#FFFFFF", width=3 * k)  # brillo del filo
    d.ellipse(((ox + 96) * k, (oy + 74) * k, (ox + 118) * k, (oy + 90) * k), fill="#A9B4C8", outline=E.FONDO, width=3 * k)  # muesca de la uña
    pivote = ((ox + 160) * k, (oy + 60) * k)
    hoja = hoja.rotate(-apertura, resample=Image.BICUBIC, center=pivote)  # gira hacia arriba (sentido horario)

    # --- Mango y virola (por delante de la hoja: la hoja «sale» de la virola) ---
    # El mango es de grosor uniforme (el mismo que el extremo ancho de la virola, sin escalón) y la
    # virola se estrecha hacia la hoja, con anillos cada vez más pequeños que acaban en punta.
    mango, d = lienzo()
    CAJA = [(256, 34), (388, 34), (388, 86), (256, 86)]
    poli(d, CAJA, "#D9A24F")  # mango de madera clara, grosor uniforme
    rng = random.Random("navaja")
    for _ in range(26):
        x, y = rng.uniform(266, 378), rng.uniform(40, 80)
        rx, ry = rng.uniform(3, 9), rng.uniform(2, 5)
        d.ellipse(((ox + x - rx) * k, (oy + y - ry) * k, (ox + x + rx) * k, (oy + y + ry) * k),
                  fill=rng.choice(("#B8792B", "#C98F3F", "#A8702A")))
    d.polygon([((ox + x) * k, (oy + y) * k) for x, y in CAJA], outline=E.FONDO, width=6 * k)
    X0, X1, SEMI0, SEMI1 = 150, 258, 17, 26  # virola: de 150 a 258; semialtura 17 → 26 (cónica)
    def semi(x: float) -> float:
        return SEMI0 + (SEMI1 - SEMI0) * (x - X0) / (X1 - X0)
    poli(d, [(X0, 60 - SEMI0), (X1, 60 - SEMI1), (X1, 60 + SEMI1), (X0, 60 + SEMI0)], "#C7CDD8")  # virola cónica
    d.polygon([((ox + x) * k, (oy + y) * k) for x, y in [(X0 + 6, 60 - semi(X0 + 6) + 6), (X1 - 4, 60 - SEMI1 + 6),
                                                        (X1 - 4, 60 - SEMI1 + 13), (X0 + 6, 60 - semi(X0 + 6) + 13)]],
              fill="#E6EAF0")  # brillo siguiendo el cono
    for x in (172, 194, 214, 232, 246):  # anillos: tan altos como la virola en cada punto (acaban en punta)
        d.line([((ox + x) * k, (oy + 60 - semi(x) + 1) * k), ((ox + x) * k, (oy + 60 + semi(x) - 1) * k)],
               fill=E.FONDO, width=3 * k)
    cx, cy = (ox + 160) * k, (oy + 60) * k  # pasador en el eje de giro
    d.ellipse((cx - 9 * k, cy - 9 * k, cx + 9 * k, cy + 9 * k), fill=E.ORO, outline=E.FONDO, width=4 * k)

    hoja.alpha_composite(mango)
    return _recortar(hoja, ancho=largo)


def botella_sprite(alto: int = 280) -> Image.Image:
    """Botella de licor café, vertical: vidrio marrón oscuro, tapón dorado y etiqueta «LIC. CAFÉ»."""
    k, S = 3, 400
    im = Image.new("RGBA", (S * k, S * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    def poli(pts, fill, w=7):
        d.polygon([(x * k, y * k) for x, y in pts], fill=fill, outline=E.FONDO, width=w * k)
    def rect(caja, fill, r=14, w=7):
        x0, y0, x1, y1 = caja
        d.rounded_rectangle((x0 * k, y0 * k, x1 * k, y1 * k), radius=r * k, fill=fill, outline=E.FONDO, width=w * k)
    poli([(150, 196), (172, 150), (181, 112), (219, 112), (228, 150), (250, 196)], "#4A2511")  # hombros
    rect((150, 180, 250, 385), "#4A2511", r=18)  # cuerpo
    rect((181, 70, 219, 120), "#4A2511", r=6)  # cuello
    rect((175, 38, 225, 76), E.ORO, r=8)  # tapón
    d.rounded_rectangle((160 * k, 205 * k, 169 * k, 365 * k), radius=5 * k, fill="#8A5230")  # reflejo
    rect((154, 222, 246, 340), "#F4E9D0", r=10, w=5)  # etiqueta
    d.text((200 * k, 258 * k), "LIC.", font=E.fuente(28 * k), fill=E.FONDO, anchor="mm")
    d.text((200 * k, 299 * k), "CAFÉ", font=E.fuente(34 * k), fill=E.FONDO, anchor="mm")
    return _recortar(im, alto=alto)


ANGULO_NAVAJA, ANGULO_BOTELLA = 42, 24  # grados con los que se cruzan la navaja y la botella (como dos espadas)
# Desplazamientos (px) de cada objeto respecto al centro al cruzarse: la navaja cruza por el cuello de
# la botella y deja a la vista la etiqueta.
DESPL_NAVAJA, DESPL_BOTELLA = (-10, -34), (22, 20)


def destello_sprite(tam: int = 260) -> Image.Image:
    """Estrella de impacto (dorada con centro blanco) para el choque de la navaja y la botella."""
    k = 3
    im = Image.new("RGBA", (tam * k, tam * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = tam * k / 2
    for radio, color in ((c * 0.98, E.ORO), (c * 0.6, E.BLANCO)):
        pts = []
        for i in range(16):
            r = radio if i % 2 == 0 else radio * 0.42
            a = math.pi * i / 8 - math.pi / 2
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        d.polygon(pts, fill=color)
    return im.resize((tam, tam), Image.LANCZOS)


def navaja_botella_sprite(tam: int = 260) -> Image.Image:
    """Icono estático del duelo: navaja y botella ya cruzadas, como dos espadas."""
    nav = navaja_sprite(330).rotate(-ANGULO_NAVAJA, resample=Image.BICUBIC, expand=True)
    bot = botella_sprite(300).rotate(-ANGULO_BOTELLA, resample=Image.BICUBIC, expand=True)
    lado = max(nav.width, bot.width, nav.height, bot.height) + 120
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    for sp, (dx, dy) in ((bot, DESPL_BOTELLA), (nav, DESPL_NAVAJA)):  # la navaja va por delante
        img.alpha_composite(sp, ((lado - sp.width) // 2 + dx, (lado - sp.height) // 2 + dy))
    img = img.crop(img.getbbox())
    lado = max(img.size)
    cuadro = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    cuadro.alpha_composite(img, ((lado - img.width) // 2, (lado - img.height) // 2))
    img = cuadro
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
