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

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from src.motor.estado import jugar_batalla
from src.motor.multiplicador import diferencia_porcentual, multiplicadores
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import Enfrentamiento, elegir_enfrentamiento
from src.render import estilo as E
from src.render.fondo import fondo_foto
from src.render.mapa import MapaGalicia, pintar

CARPETA = E.RAIZ / "output" / "muestras"
SUPERMUESTREO = 2  # las siluetas se dibujan al doble y se reducen, para bordes suaves

# Zonas del fotograma (y en píxeles)
MAPA_Y0, MAPA_ALTO = 395, 440
LINEA_Y = MAPA_Y0 + MAPA_ALTO  # justo bajo el mapa
PANEL_FIN = E.ALTO - E.MARGEN_INF + 10

# Columnas del panel: atacante, defensor y centro
CX_A, CX_D, CX_C = 290, 790, E.ANCHO / 2  # simétricas respecto al centro (VS, marcador y dados)
ANCHO_NOMBRE = 300
Y_ROTULO, Y_SILUETA, ALTO_SILUETA, Y_NOMBRE, Y_VACAS = 866, 900, 110, 1035, 1172


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


def cabecera(episodio: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Fondo de hierba con el título de la serie y el número de episodio (común a todas las escenas)."""
    img = fondo_foto(E.ANCHO, E.ALTO)
    d = ImageDraw.Draw(img)
    E.texto_centrado(d, E.ANCHO / 2, 232, "CONCELLO DE BATALLA", E.T_TITULO, E.ORO, borde=9)
    E.texto_centrado(d, E.ANCHO / 2, 318, f"Ep. {episodio}", E.T_SUBTITULO, E.BLANCO, borde=7)
    return img, d


def marco_vacio(episodio: int) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Cabecera, líneas doradas y panel blanco con manchas de vaca; sin mapa ni bandos."""
    img, d = cabecera(episodio)
    W = E.ANCHO
    d.rectangle((0, MAPA_Y0 - 6, W, MAPA_Y0 - 1), fill=E.ORO)
    d.rectangle((0, LINEA_Y, W, LINEA_Y + 6), fill=E.ORO)
    E.pegar_panel(img, LINEA_Y + 6, PANEL_FIN)
    d.rectangle((0, PANEL_FIN, W, PANEL_FIN + 4), fill=E.FONDO)
    return img, d


def texto_diferencia(estado: dict, f: Enfrentamiento) -> list[str]:
    va, vd = estado["donos"][f.atacante]["vacas"], estado["donos"][f.defensor]["vacas"]
    dif = diferencia_porcentual(va, vd)
    bonus = max(multiplicadores(va, vd))
    return [f"diferencia = {'+' + num(dif) if dif else '0'}%", f"bonus = ×{str(bonus).replace('.', ',')}"]


T_CENTRO = 38  # tamaño del texto de la pastilla central (diferencia / bonus)


def x_pastilla_vacas(estado: dict, f: Enfrentamiento, dono: str, lado: int) -> float:
    """Centro de la pastilla de vacas de un bando (lado -1 = izquierda, +1 = derecha): en su columna, pero
    sin invadir el hueco central de la pastilla de la diferencia."""
    wd, _ = E.tamano_pastilla(texto_diferencia(estado, f), T_CENTRO, 18)
    w, _ = E.tamano_pastilla(f"{num(estado['donos'][dono]['vacas'])} {E.ICONO_VACA}", E.T_MIN, 20)
    if lado < 0:
        return min(CX_A, CX_C - wd / 2 - 12 - w / 2)
    return max(CX_D, CX_C + wd / 2 + 12 + w / 2)


def dibujar_bando(img: Image.Image, d: ImageDraw.ImageDraw, estado: dict, mapa: MapaGalicia, dono: str,
                  cx: float, rotulo: tuple[str, str, str], cx_pastilla: float) -> None:
    """Rótulo, silueta del territorio completo, nombre del dueño y pastilla de vacas de un bando."""
    k = SUPERMUESTREO
    texto, color, borde_r = rotulo
    E.texto_centrado(d, cx, Y_ROTULO, texto, E.T_MIN, color, borde=6, color_borde=borde_r)
    geom = mapa.geometria(estado["donos"][dono]["territorio"])
    sil = Image.new("RGBA", (300 * k, ALTO_SILUETA * k), (255, 255, 255, 0))
    caja = caja_silueta(geom.bounds, 300, ALTO_SILUETA, k)
    cor = estado["donos"][dono]["cor"]
    pintar(ImageDraw.Draw(sil), geom, caja, cor["colores"][0], None, 0)
    if cor.get("escudo"):  # territorio blanco con el escudo encima, recortado por su límite
        e = E.escudo(cor["escudo"], round(0.9 * ALTO_SILUETA * k))
        capa = Image.new("RGBA", sil.size, (0, 0, 0, 0))
        capa.alpha_composite(e, (round(300 * k / 2 - e.width / 2), round(ALTO_SILUETA * k / 2 - e.height / 2)))
        capa.putalpha(ImageChops.multiply(capa.getchannel("A"), sil.getchannel("A")))
        sil.alpha_composite(capa)
    pintar(ImageDraw.Draw(sil), geom, caja, None, E.FONDO, 3 * k)  # el límite siempre encima
    sil = sil.resize((300, ALTO_SILUETA), Image.LANCZOS)
    # halo blanco alrededor de la silueta, para que se vea también sobre una mancha negra del panel
    halo = sil.getchannel("A").filter(ImageFilter.MaxFilter(11)).filter(ImageFilter.GaussianBlur(1))
    img.paste(Image.new("RGB", sil.size, E.BLANCO), (int(cx - 150), Y_SILUETA), halo)
    img.paste(sil.convert("RGB"), (int(cx - 150), Y_SILUETA), sil.getchannel("A"))
    lineas, t = E.dividir_nombre(estado["donos"][dono]["nome"], 52, ANCHO_NOMBRE, minimo=30)
    for n, linea in enumerate(lineas):
        E.texto_centrado(d, cx, Y_NOMBRE + n * (t + 2), linea, t, E.FONDO, borde=6, color_borde=E.BLANCO)
    E.pastilla_vaca(img, cx_pastilla, Y_VACAS, f"{num(estado['donos'][dono]['vacas'])} {E.ICONO_VACA}", E.T_MIN, 20)


ROTULOS_BATALLA = (("ATACA", E.CONFLICTO, E.BLANCO), ("DEFENDE", E.AZUL_DEFENSA, E.BLANCO))


def fotograma_base(estado: dict, f: Enfrentamiento, mapa: MapaGalicia, episodio: int,
                   rotulos: tuple[tuple[str, str, str], tuple[str, str, str]] | None = None,
                   disposicion: dict | None = None) -> tuple[Image.Image, ImageDraw.ImageDraw]:
    """Título, mapa con zoom, líneas doradas, panel, siluetas, nombres, vacas y diferencia.

    `rotulos`: (texto, color, color del borde) del atacante y del defensor; por defecto «ATACA» y
    «DEFENDE» (la pantalla de conquista usa «CAMPIÓN» y «MALOGRADO»)."""
    rotulos = rotulos or ROTULOS_BATALLA
    img, d = marco_vacio(episodio)
    img.paste(banda_enfrentamiento(estado, f, mapa, disposicion), (0, MAPA_Y0))
    dibujar_bando(img, d, estado, mapa, f.atacante, CX_A, rotulos[0], x_pastilla_vacas(estado, f, f.atacante, -1))
    dibujar_bando(img, d, estado, mapa, f.defensor, CX_D, rotulos[1], x_pastilla_vacas(estado, f, f.defensor, 1))
    E.texto_centrado(d, CX_C, Y_SILUETA + ALTO_SILUETA / 2, "VS", 64, E.ORO, borde=7, color_borde=E.FONDO)
    E.pastilla_vaca(img, CX_C, Y_VACAS, texto_diferencia(estado, f), T_CENTRO, 18)
    return img, d


def banda_enfrentamiento(estado: dict, f: Enfrentamiento, mapa: MapaGalicia, disposicion: dict | None = None) -> Image.Image:
    """Banda del mapa con zoom a los dos bandos y contorno rojo en los concellos en conflicto."""
    ventana = mapa.ventana_enfrentamiento(estado, f.atacante, f.defensor, E.ANCHO / MAPA_ALTO)
    conflicto = [(mapa.geometria([c]), E.CONFLICTO, 6) for c in (f.concello_atacante, f.concello_defensor)]
    return mapa.dibujar(estado, ventana, E.ANCHO, MAPA_ALTO, contornos=conflicto, nombres=[f.atacante, f.defensor],
                        disposicion=disposicion)


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
