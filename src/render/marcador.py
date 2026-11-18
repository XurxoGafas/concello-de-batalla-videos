"""Marcador de la batalla (paso 4.4): totales, multiplicador, muerte súbita y ganador.

Todo se dibuja encima del fotograma base (`fotograma_base`, paso 4.3), en la zona de dados.
Las funciones no guardan estado: reciben el instante y dibujan lo que toca.
"""

from __future__ import annotations

from PIL import Image, ImageDraw

from src.render import dados as D
from src.render import estilo as E

X_A, X_D = E.ANCHO / 2 - 105, E.ANCHO / 2 + 105  # columnas de los totales
Y_TOTAL = D.Y_MEDIO - 25
Y_MULT = D.Y_MEDIO + 60


def formato_decimas(decimas: int) -> str:
    """91 → «9,1»."""
    return f"{decimas // 10},{decimas % 10}"


def dibujar_totales(img: Image.Image, a: str, b: str, pop_a: float = 1.0, pop_b: float = 1.0) -> None:
    """Marcador «a - b»; `pop_*` (≥1) agranda momentáneamente el total que acaba de cambiar."""
    d = ImageDraw.Draw(img)
    for cx, txt, pop in ((X_A, a, pop_a), (X_D, b, pop_b)):
        base = 84 if len(txt) > 2 else 100  # los decimales («9,1») son más anchos
        E.texto_centrado_exacto(d, cx, Y_TOTAL, txt, int(base * pop), E.FONDO, borde=8, color_borde=E.BLANCO)
    E.texto_centrado_exacto(d, E.ANCHO / 2, Y_TOTAL, "-", 80, E.FONDO, borde=8, color_borde=E.BLANCO)


def dibujar_multiplicador(img: Image.Image, lado: str, mult: float, u: float) -> None:
    """Pastilla de vaca «×1,5» bajo el total del bando con más vacas; `u` (0–1) es su aparición
    (rebote) y un halo dorado la resalta."""
    cx = X_A if lado == "a" else X_D
    pastilla = E.crear_pastilla(f"×{str(mult).replace('.', ',')}", 46, 26)
    s = D.salida_rebote(u)
    if u < 1.0:  # halo dorado que se apaga
        halo = Image.new("RGBA", (pastilla.width + 40, pastilla.height + 40), (0, 0, 0, 0))
        ImageDraw.Draw(halo).rounded_rectangle((0, 0, halo.width - 1, halo.height - 1), radius=40,
                                               fill=(*_rgb(E.ORO), 255))
        D.pegar(img, halo, cx, Y_MULT, escala=s * 1.0, opacidad=0.8 * (1 - u))
    D.pegar(img, pastilla, cx, Y_MULT, escala=s)


def _rgb(hexa: str) -> tuple[int, int, int]:
    return tuple(int(hexa[i:i + 2], 16) for i in (1, 3, 5))  # type: ignore[return-value]


def marcar_ganador(img: Image.Image, lado: str, u: float) -> None:
    """Recuadro dorado alrededor del total del ganador (aparece con rebote)."""
    cx = X_A if lado == "a" else X_D
    w, h = 150, 120
    s = D.salida_rebote(u)
    caja = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    ImageDraw.Draw(caja).rounded_rectangle((6, 6, 6 + w, 6 + h), radius=30, outline=E.ORO, width=9)
    D.pegar(img, caja, cx, Y_TOTAL, escala=s)


def tarjeta_muerte_subita(img: Image.Image, u: float) -> tuple[float, float, float, float]:
    """Tarjeta blanca que cubre la zona de dados con el título «MORTE SÚBITA».

    `u` (0–1) es la entrada (sube desde abajo). Devuelve la caja (x0, y0, x1, y1) para colocar
    dentro los dados de desempate."""
    x0, x1 = 40, E.ANCHO - 40
    y0, y1 = D.Y0 - 6, D.Y0 + D.ALTO_ZONA + 4
    desp = (1 - D.salida_cubica(u)) * 60
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0 + desp, x1, y1 + desp), radius=36, fill=E.BLANCO, outline=E.FONDO, width=6)
    E.texto_centrado_exacto(d, E.ANCHO / 2, y0 + 36 + desp, "MORTE SÚBITA", 58, E.CONFLICTO, borde=6,
                            color_borde=E.BLANCO)
    return x0, y0 + desp, x1, y1 + desp
