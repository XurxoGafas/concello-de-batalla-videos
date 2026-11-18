"""Fondo de hierba viva dibujado por código (paso 4.1).

No usa ninguna imagen ni textura externa: se dibuja con Pillow, así que no hay licencias que
registrar y es idéntico en cualquier máquina (semilla fija → mismas briznas).

`fondo_hierba(fase=...)` admite una fase de viento (0 a 1, cíclica): con `fase` distinta las
puntas de las briznas se desplazan con un balanceo suave, para animar el fondo (fase 4.4+). Con
la misma fase y semilla el resultado es siempre idéntico.
"""

from __future__ import annotations

import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

# Gradiente de verdes (de arriba, lejos y más oscuro, a abajo, cerca y más luminoso)
VERDE_ARRIBA = (20, 92, 38)
VERDE_ABAJO = (74, 176, 58)
VERDE_PUNTA = (190, 238, 96)  # punta clara de cada brizna (da vida y brillo)
VERDE_SOMBRA = (8, 52, 22)  # raíz de cada brizna
SUPERMUESTREO = 2


def _mezcla(a: tuple[int, int, int], b: tuple[int, int, int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(round(x + (y - x) * t)) for x, y in zip(a, b))  # type: ignore[return-value]


def fondo_hierba(ancho: int, alto: int, semilla: int = 7, fase: float = 0.0) -> Image.Image:
    """Imagen RGB `ancho`×`alto` de césped. `fase` (0–1) mueve las puntas con el viento."""
    k = SUPERMUESTREO
    W, H = ancho * k, alto * k
    rng = random.Random(semilla)

    # Base: gradiente vertical
    base = Image.new("RGB", (W, H))
    db = ImageDraw.Draw(base)
    for y in range(H):
        db.line([(0, y), (W, y)], fill=_mezcla(VERDE_ARRIBA, VERDE_ABAJO, y / H))

    # Briznas, de arriba (lejos) hacia abajo (cerca) para que las de delante tapen a las de detrás
    d = ImageDraw.Draw(base)
    paso_y = 9 * k
    y = 40 * k
    fila = 0
    while y < H + 140 * k:
        prof = min(1.0, y / H)  # 0 lejos, 1 cerca
        escala = 0.55 + 1.2 * prof  # las de delante son más grandes
        paso_x = max(7 * k, int(17 * k * (1.1 - 0.35 * prof)))
        x = -paso_x + (fila % 2) * paso_x // 2
        while x < W + paso_x:
            xb = x + rng.uniform(-0.6, 0.6) * paso_x
            hb = rng.uniform(70, 150) * escala * k
            wb = rng.uniform(9, 17) * escala * k
            inclin = rng.uniform(-0.5, 0.5) * wb * 2.2
            fase_i = rng.uniform(0, 2 * math.pi)
            viento = math.sin(2 * math.pi * fase + fase_i) * wb * 0.9 * (hb / (110 * k))
            punta = (xb + inclin + viento, y - hb)
            tono = rng.uniform(-0.22, 0.22)
            c_base = _mezcla(VERDE_ARRIBA, VERDE_ABAJO, prof + tono)
            c_raiz = _mezcla(c_base, VERDE_SOMBRA, 0.7)  # raíz oscura: da profundidad
            c_med = _mezcla(c_base, VERDE_PUNTA, 0.3 + rng.uniform(0, 0.15))
            c_luz = _mezcla(c_med, VERDE_PUNTA, 0.75)
            d.polygon([(xb - wb / 2, y), (xb + wb / 2, y), punta], fill=c_raiz)
            for t, color in ((0.28, c_base), (0.55, c_med), (0.82, c_luz)):
                m = (xb + (punta[0] - xb) * t, y - hb * t)
                semi = wb * (1 - t) / 2
                d.polygon([(m[0] - semi, m[1]), (m[0] + semi, m[1]), punta], fill=color)
            x += paso_x
        y += paso_y
        fila += 1

    img = base.resize((ancho, alto), Image.LANCZOS)

    # Manchas suaves de sol (claras) y de sombra (oscuras), para que no se vea plano
    luz = Image.new("L", (ancho, alto), 0)
    dl = ImageDraw.Draw(luz)
    rng2 = random.Random(semilla + 1)
    for _ in range(9):
        cx, cy = rng2.uniform(0, ancho), rng2.uniform(0, alto)
        rx, ry = rng2.uniform(120, 320), rng2.uniform(80, 220)
        dl.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=rng2.randint(60, 120))
    luz = luz.filter(ImageFilter.GaussianBlur(70))
    sol = Image.new("RGB", (ancho, alto), (210, 245, 110))
    img = Image.composite(Image.blend(img, sol, 0.28), img, luz)

    # Viñeta: oscurece los bordes (y algo más arriba, donde va el título) para dar contraste
    vin = Image.new("L", (ancho, alto), 0)
    dv = ImageDraw.Draw(vin)
    dv.ellipse((-ancho * 0.25, -alto * 0.12, ancho * 1.25, alto * 1.12), fill=255)
    vin = ImageChops.invert(vin.filter(ImageFilter.GaussianBlur(160)))
    sombra = Image.new("RGB", (ancho, alto), (4, 36, 14))
    return Image.composite(Image.blend(img, sombra, 0.55), img, vin)
