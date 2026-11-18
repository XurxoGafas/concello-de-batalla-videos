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

    La hoja es de un solo filo (lomo recto y filo curvo), con canal; el pasador marca el eje.
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
    d.line([((ox + 68) * k, (oy + 53) * k), ((ox + 134) * k, (oy + 46) * k)], fill="#FFFFFF", width=3 * k)  # brillo, termina antes del perfil
    pivote = ((ox + 160) * k, (oy + 60) * k)
    hoja = hoja.rotate(-apertura, resample=Image.BICUBIC, center=pivote)  # gira hacia arriba (sentido horario)

    # --- Mango y virola (por delante de la hoja: la hoja «sale» de la virola) ---
    # El mango es de grosor uniforme (el mismo que el extremo ancho de la virola, sin escalón) y la
    # virola se estrecha hacia la hoja, con anillos cada vez más pequeños que acaban en punta.
    mango, d = lienzo()
    CAJA = [(212, 34), (327, 34), (327, 86), (212, 86)]  # mango+virola = 1,1 × la hoja (152 → 167 desde el pasador)
    poli(d, CAJA, "#D9A24F")  # mango de madera clara, grosor uniforme
    rng = random.Random("navaja")
    for _ in range(20):
        x, y = rng.uniform(222, 317), rng.uniform(40, 80)
        rx, ry = rng.uniform(3, 9), rng.uniform(2, 5)
        d.ellipse(((ox + x - rx) * k, (oy + y - ry) * k, (ox + x + rx) * k, (oy + y + ry) * k),
                  fill=rng.choice(("#B8792B", "#C98F3F", "#A8702A")))
    d.polygon([((ox + x) * k, (oy + y) * k) for x, y in CAJA], outline=E.FONDO, width=6 * k)
    X0, X1, SEMI0, SEMI1 = 150, 214, 17, 26  # virola: de 150 a 214; semialtura 17 → 26 (cónica)
    def semi(x: float) -> float:
        return SEMI0 + (SEMI1 - SEMI0) * (x - X0) / (X1 - X0)
    poli(d, [(X0, 60 - SEMI0), (X1, 60 - SEMI1), (X1, 60 + SEMI1), (X0, 60 + SEMI0)], "#C7CDD8")  # virola cónica
    d.polygon([((ox + x) * k, (oy + y) * k) for x, y in [(X0 + 6, 60 - semi(X0 + 6) + 6), (X1 - 4, 60 - SEMI1 + 6),
                                                        (X1 - 4, 60 - SEMI1 + 13), (X0 + 6, 60 - semi(X0 + 6) + 13)]],
              fill="#E6EAF0")  # brillo siguiendo el cono
    for x in (170, 183, 195, 205, 211):  # anillos: tan altos como la virola en cada punto (acaban en punta)
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


# Pose final del choque (grados, positivo = antihorario; px respecto al centro de la zona). La navaja va
# **abierta y recta**, apoyada hacia la derecha, y golpea con el filo (su lado curvo) el hombro de la
# botella, que se inclina hacia ella.
ANGULO_NAVAJA, ANGULO_BOTELLA = -122, 14
DESPL_NAVAJA, DESPL_BOTELLA = (-62, -24), (58, -24)


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


def gaita_sprite(alto: int = 260) -> Image.Image:
    """Gaita gallega dibujada por código: fol (bolsa) rojo con cinta dorada, soprete a la izquierda,
    punteiro (con agujeros y campana) hacia abajo, y roncón y ronqueta hacia arriba a la derecha."""
    k, W, H = 3, 520, 520
    im = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def pt(x, y):
        return (x * k, y * k)

    def tubo(p0, p1, w0, w1, color, anillos=(), cola=None):
        """Tubo cónico de p0 a p1 con grosor w0→w1, anillos dorados en las fracciones dadas."""
        w0, w1 = w0 * 1.5, w1 * 1.5
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        n = math.hypot(dx, dy)
        nx, ny = -dy / n, dx / n
        pts = [(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2), (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
               (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2), (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)]
        d.polygon([pt(*q) for q in pts], fill=color, outline=E.FONDO, width=6 * k)
        for f in anillos:
            c = (p0[0] + dx * f, p0[1] + dy * f)
            w = w0 + (w1 - w0) * f
            d.line([pt(c[0] + nx * (w / 2 + 2), c[1] + ny * (w / 2 + 2)), pt(c[0] - nx * (w / 2 + 2), c[1] - ny * (w / 2 + 2))],
                   fill=E.ORO, width=7 * k)
            d.line([pt(c[0] + nx * (w / 2 + 2), c[1] + ny * (w / 2 + 2)), pt(c[0] - nx * (w / 2 + 2), c[1] - ny * (w / 2 + 2))],
                   fill=E.FONDO, width=1 * k)
        if cola:  # remate dorado en el extremo p1
            r = w1 / 2 + 4
            d.ellipse((*pt(p1[0] - r, p1[1] - r), *pt(p1[0] + r, p1[1] + r)), fill=E.ORO, outline=E.FONDO, width=5 * k)
        return nx, ny

    MADERA, CLARA = "#7A4A22", "#D9A24F"
    # Roncón (largo) y ronqueta (corto): hacia arriba y a la derecha, por detrás del fol
    tubo((270, 250), (440, 30), 26, 17, MADERA, anillos=(0.3, 0.62), cola=True)
    tubo((320, 270), (490, 120), 22, 15, MADERA, anillos=(0.35, 0.7), cola=True)
    # Soprete (por donde se sopla): hacia arriba y a la izquierda
    tubo((140, 250), (50, 130), 22, 14, MADERA, anillos=(0.5,), cola=True)
    # Punteiro: hacia abajo y a la izquierda, con agujeros y campana
    p0, p1 = (200, 360), (110, 490)
    nx, ny = tubo(p0, p1, 24, 40, CLARA, anillos=(0.12, 0.9))
    for f in (0.28, 0.42, 0.56, 0.70):
        c = (p0[0] + (p1[0] - p0[0]) * f, p0[1] + (p1[1] - p0[1]) * f)
        d.ellipse((*pt(c[0] - 5, c[1] - 5), *pt(c[0] + 5, c[1] + 5)), fill=E.FONDO)
    # Fol: bolsa roja con cinta dorada
    d.ellipse((*pt(100, 215), *pt(360, 385)), fill="#C62F3A", outline=E.FONDO, width=7 * k)
    d.ellipse((*pt(125, 232), *pt(335, 368)), outline=E.ORO, width=6 * k)
    d.arc((*pt(115, 225), *pt(345, 375)), 200, 250, fill="#FF8C94", width=7 * k)  # brillo
    for x in (170, 215, 260, 300):  # franjas de la cinta
        d.line([pt(x, 262), pt(x - 8, 340)], fill="#F5B82E", width=4 * k)
    # Collarines dorados en las uniones
    for cx, cy in ((255, 245), (305, 262), (148, 248), (190, 355)):
        d.ellipse((*pt(cx - 14, cy - 10), *pt(cx + 14, cy + 10)), fill=E.ORO, outline=E.FONDO, width=5 * k)
    return _recortar(im, alto=alto)


def texto_sprite(texto: str, tam: int, color: str, color_borde: str = E.FONDO, borde: int = 9) -> Image.Image:
    """Texto con trazo grueso como imagen RGBA (para animarlo: escalarlo, hacerlo aparecer…)."""
    f = E.fuente(tam)
    x0, y0, x1, y1 = ImageDraw.Draw(Image.new("L", (1, 1))).textbbox((0, 0), texto, font=f, anchor="ls", stroke_width=borde)
    im = Image.new("RGBA", (x1 - x0 + 8, y1 - y0 + 8), (0, 0, 0, 0))
    E.texto_con_borde(ImageDraw.Draw(im), (4 - x0, 4 - y0), texto, f, color, "ls", borde, color_borde)
    return im


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
