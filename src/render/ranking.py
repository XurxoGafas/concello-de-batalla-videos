"""Pantalla de cierre con los dos rankings top 5 (fase 8 del vídeo, paso 4.6).

«Máis vitorias» (batallas ganadas por cada dueño en toda la serie) y «Máis vacas» (vacas que suma el
territorio de cada dueño ahora; decisión del usuario, 2026-11-18, en vez de «Máis territorio»). Los
empates se desempatan siempre igual (la otra magnitud y, al final, el nombre), para que el vídeo sea
reproducible.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from src.render import dados as D
from src.render import enfrentamiento as M
from src.render import estilo as E

TOP = 5
CX_IZQ, CX_DER = 285, 795
ANCHO_FILA, ALTO_FILA = 470, 84
Y_TITULOS, Y_FILAS, PASO_FILA = 884, 1000, 100


def clasificaciones(estado: dict, top: int = TOP) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    """([(id, victorias)…], [(id, vacas)…]). En «vitorias» solo entran los dueños con alguna."""
    donos = estado["donos"]
    vit = sorted(((i, d["victorias"]) for i, d in donos.items() if d["victorias"] > 0),
                 key=lambda x: (-x[1], -donos[x[0]]["vacas"], donos[x[0]]["nome"]))
    vac = sorted(((i, d["vacas"]) for i, d in donos.items()),
                 key=lambda x: (-x[1], -donos[x[0]]["victorias"], donos[x[0]]["nome"]))
    return vit[:top], vac[:top]


def _fila(nombre: str, valor: int, puesto: int, color: str) -> Image.Image:
    """Tarjeta RGBA de una fila: insignia con el puesto, nombre del dueño y valor."""
    k = 2
    w, h = ANCHO_FILA, ALTO_FILA
    im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    relleno = "#FFF1C2" if puesto == 1 else E.BLANCO
    d.rounded_rectangle((2 * k, 2 * k, (w - 2) * k, (h - 2) * k), radius=28 * k, fill=relleno, outline=E.FONDO, width=4 * k)
    r = 28 * k
    cx, cy = 40 * k, h * k // 2
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color, outline=E.FONDO, width=4 * k)
    im = im.resize((w, h), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    E.texto_centrado_exacto(d, 40, h / 2, str(puesto), 38, E.BLANCO, borde=4, color_borde=E.FONDO)
    txt_valor = M.num(valor)
    tv = 40
    ancho_v = E.ancho_texto(txt_valor, tv)
    tam = E.ajustar_tamano(nombre, 38, w - 70 - ancho_v - 50, minimo=24)
    E.texto_con_borde(d, (78, h / 2 + 1), nombre, E.fuente(tam), E.FONDO, "lm", 0, E.FONDO)
    E.texto_con_borde(d, (w - 24, h / 2 + 1), txt_valor, E.fuente(tv), E.FONDO, "rm", 0, E.FONDO)
    return im


def dibujar_cierre(img: Image.Image, estado: dict, t: float, t0: float = 0.6, paso: float = 0.28) -> None:
    """Dibuja sobre `img` (que ya lleva cabecera, mapa y panel) los títulos y las filas que toquen en `t`.

    Las filas aparecen de la 5ª a la 1ª, cada una con un pequeño «pop»."""
    d = ImageDraw.Draw(img)
    vit, ter = clasificaciones(estado)
    for cx, titulo, sub in ((CX_IZQ, "MÁIS VITORIAS", "batallas gañadas"), (CX_DER, "MÁIS VACAS", "vacas do territorio")):
        E.texto_centrado(d, cx, Y_TITULOS - 34, titulo, 46, E.FONDO, borde=6, color_borde=E.BLANCO)
        E.texto_centrado(d, cx, Y_TITULOS + 22, sub, 30, E.FONDO, borde=5, color_borde=E.BLANCO)
    colores = {1: E.ORO, 2: "#8E9BB0", 3: "#B9773B"}
    for cx, lista in ((CX_IZQ, vit), (CX_DER, ter)):
        n = len(lista)
        for idx, (dono, valor) in enumerate(lista):
            puesto = idx + 1
            llegada = t0 + (n - puesto) * paso  # primero sale la última
            u = (t - llegada) / 0.3
            if u <= 0:
                continue
            fila = _fila(estado["donos"][dono]["nome"], valor, puesto, colores.get(puesto, E.AZUL_DEFENSA))
            D.pegar(img, fila, cx, Y_FILAS + idx * PASO_FILA, escala=D.salida_rebote(u))
