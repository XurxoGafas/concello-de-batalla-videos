"""Pantalla de enfrentamiento (fase 3 del vídeo, paso 4.3).

Muestra el mapa con zoom a los dos bandos (contorno rojo en los concellos en conflicto), y en el
panel inferior las siluetas de los territorios completos con su nombre, el rótulo ATACA / DEFENDE,
el número de vacas de cada bando y, entre ambos, la diferencia en % (todo «pintado de vaca»).

`fotograma_base` dibuja todo lo común con las pantallas de dados (4.4): así los dados y el
marcador aparecen después exactamente en el hueco que deja libre esta pantalla.

Uso: `python -m src.render.enfrentamiento` → `output/muestras/enfrentamiento.png`
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from src.motor.estado import jugar_batalla
from src.motor.multiplicador import diferencia_porcentual
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import Enfrentamiento, elegir_enfrentamiento
from src.render import estilo as E
from src.render.fondo import fondo_foto
from src.render.mapa import MapaGalicia, pintar

CARPETA = E.RAIZ / "output" / "muestras"
SUPERMUESTREO = 2  # las siluetas se dibujan al doble y se reducen, para bordes suaves

# Zonas del fotograma (y en píxeles)
MAPA_Y0, MAPA_ALTO = 395, 510
LINEA_Y = MAPA_Y0 + MAPA_ALTO  # justo bajo el mapa
PANEL_FIN = E.ALTO - E.MARGEN_INF + 10

# Columnas del panel: atacante, defensor y centro
CX_A, CX_D, CX_C = 270, 690, E.ANCHO / 2
Y_ROTULO, Y_SILUETA, ALTO_SILUETA, Y_NOMBRE, Y_VACAS = 938, 975, 125, 1110, 1262


def num(n: int) -> str:
    """Número con punto de millar (1.234)."""
    return f"{n:,}".replace(",", ".")


def caja_silueta(limites: tuple[float, float, float, float], ancho: int, alto: int, k: int):
    """Transformación que encaja un territorio en una caja (ancho×alto) dejando 10 px de aire."""
    minx, miny, maxx, maxy = limites
    esc = min((ancho - 20) * k / (maxx - minx), (alto - 20) * k / (maxy - miny))
    ox = (ancho * k - (maxx - minx) * esc) / 2
    oy = (alto * k - (maxy - miny) * esc) / 2
    return lambda x, y: (ox + (x - minx) * esc, oy + (maxy - y) * esc)


def fotograma_base(estado: dict, f: Enfrentamiento, mapa: MapaGalicia, episodio: int
                   ) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Título, mapa con zoom, líneas doradas, panel, siluetas, nombres, vacas y diferencia."""
    k, W, H = SUPERMUESTREO, E.ANCHO, E.ALTO
    img = fondo_foto(W, H)
    d = ImageDraw.Draw(img)

    E.texto_centrado(d, W / 2, 232, "CONCELLO DE BATALLA", E.T_TITULO, E.ORO, borde=9)
    E.texto_centrado(d, W / 2, 318, f"Ep. {episodio}", E.T_SUBTITULO, E.BLANCO, borde=7)

    # Mapa con zoom: encuadra los territorios completos de los dos bandos
    ventana = mapa.ventana_enfrentamiento(estado, f.atacante, f.defensor, W / MAPA_ALTO)
    conflicto = [(mapa.geometria([c]), E.CONFLICTO, 6) for c in (f.concello_atacante, f.concello_defensor)]
    img.paste(mapa.dibujar(estado, ventana, W, MAPA_ALTO, contornos=conflicto,
                           nombres=[f.atacante, f.defensor]), (0, MAPA_Y0))

    # Líneas doradas y panel (tarjeta navy algo translúcida)
    d.rectangle((0, MAPA_Y0 - 6, W, MAPA_Y0 - 1), fill=E.ORO)
    d.rectangle((0, LINEA_Y, W, LINEA_Y + 6), fill=E.ORO)
    panel = Image.new("RGB", (W, PANEL_FIN - LINEA_Y - 6), E.PANEL)
    img.paste(Image.blend(img.crop((0, LINEA_Y + 6, W, PANEL_FIN)), panel, 0.93), (0, LINEA_Y + 6))
    d.rectangle((0, PANEL_FIN, W, PANEL_FIN + 4), fill=E.FONDO)

    # Rótulo, silueta del territorio completo y nombre del dueño
    for dono, cx, rotulo, color in ((f.atacante, CX_A, "ATACA", E.CONFLICTO),
                                    (f.defensor, CX_D, "DEFENDE", E.BLANCO)):
        E.texto_centrado(d, cx, Y_ROTULO, rotulo, E.T_MIN, color, borde=4)
        geom = mapa.geometria(estado["donos"][dono]["territorio"])
        sil = Image.new("RGBA", (300 * k, ALTO_SILUETA * k), (255, 255, 255, 0))
        pintar(ImageDraw.Draw(sil), geom, caja_silueta(geom.bounds, 300, ALTO_SILUETA, k),
               estado["donos"][dono]["cor"]["colores"][0], E.BLANCO, 3 * k)
        sil = sil.resize((300, ALTO_SILUETA), Image.LANCZOS)
        img.paste(sil.convert("RGB"), (int(cx - 150), Y_SILUETA), sil.getchannel("A"))
        lineas, t = E.dividir_nombre(estado["donos"][dono]["nome"], 52, 410)
        for n, linea in enumerate(lineas):
            E.texto_centrado(d, cx, Y_NOMBRE + n * (t + 2), linea, t, E.BLANCO)
    E.texto_centrado(d, CX_C, Y_SILUETA + ALTO_SILUETA / 2, "VS", 64, E.ORO, borde=3)

    # Fila de vacas: cada bando y, entre ambos, la diferencia en % (todo «pintado de vaca»)
    va, vd = estado["donos"][f.atacante]["vacas"], estado["donos"][f.defensor]["vacas"]
    dif = diferencia_porcentual(va, vd)
    lineas_dif = ["dif. vacas", f"+{num(dif)}%" if dif else "0%"]
    wd, _ = E.tamano_pastilla(lineas_dif, E.T_MIN, 20)
    for vacas, cx_col, lado in ((va, CX_A, -1), (vd, CX_D, 1)):
        txt = f"{num(vacas)} vacas"
        w, _ = E.tamano_pastilla(txt, E.T_MIN, 20)
        # que no invada el hueco central de la pastilla de la diferencia
        cx = min(cx_col, CX_C - wd / 2 - 12 - w / 2) if lado < 0 else max(cx_col, CX_C + wd / 2 + 12 + w / 2)
        E.pastilla_vaca(img, cx, Y_VACAS, txt, E.T_MIN, 20)
    E.pastilla_vaca(img, CX_C, Y_VACAS, lineas_dif, E.T_MIN, 20)
    return img, d


def pantalla_enfrentamiento(estado: dict, f: Enfrentamiento, mapa: MapaGalicia, episodio: int) -> Image.Image:
    """Fotograma completo de la fase 3 (sin dados todavía)."""
    return fotograma_base(estado, f, mapa, episodio)[0]


def generar(ruta: Path, semilla: str = "muestra", previas: int = 106, episodio: int = 27) -> Path:
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    f = elegir_enfrentamiento(estado, random.Random(semilla_de_batalla(semilla, previas + 1)))
    ruta.parent.mkdir(parents=True, exist_ok=True)
    pantalla_enfrentamiento(estado, f, MapaGalicia(), episodio).save(ruta)
    return ruta


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA / "enfrentamiento.png"))
