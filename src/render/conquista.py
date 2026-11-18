"""Animación de conquista (fase 6 del vídeo, paso 4.5).

Pantalla de enfrentamiento con los rótulos «CAMPIÓN» y «MALOGRADO»: el color del ganador se extiende por
el mapa sobre el territorio del perdedor (concello a concello, desde la frontera), sale una gaita gallega
con un poco de confeti y las pastillas «+N vacas» y «+K concellos» junto al ganador.

`fotograma(ctx, t)` es una función pura del instante, como en `animacion_batalla`.

Uso: `python -m src.render.conquista` → `output/muestras/conquista.mp4` (y un fotograma `conquista.png`).
"""

from __future__ import annotations

import functools
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw

from src.motor.estado import Episodio, jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import territorio
from src.render import dados as D
from src.render import enfrentamiento as M
from src.render import estilo as E
from src.render.animacion_batalla import escribir_video
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"

# Línea de tiempo (segundos)
T_ROTULOS = 0.5      # ATACA/DEFENDE → CAMPIÓN/MALOGRADO
T_EXTENSION = 0.5    # empieza a extenderse el color
D_EXTENSION = 1.8
T_GAITA = 1.0        # aparece la gaita (y el primer chorro de confeti)
T_PASTILLAS = 2.0
T_CONFETI2 = 2.0
DURACION = 4.2
PASOS_MAX = 24       # el mapa se redibuja como mucho 24 veces (grupos de concellos)
X_GAITA, Y_GAITA, ALTO_GAITA = E.ANCHO / 2, D.Y_MEDIO + 22, 232


@dataclass
class Conquista:
    estado_antes: dict
    estado_despues: dict
    f: object
    ganador: str
    perdedor: str
    mapa: MapaGalicia
    base_antes: Image.Image
    base_despues: Image.Image
    ventana: tuple
    orden: list[str]            # concellos del perdedor, de la frontera hacia dentro
    vacas_ganadas: int
    n_concellos: int
    cx_ganador: float
    lado_ganador: int           # -1 = izquierda, +1 = derecha
    banda_final: Image.Image


def _ganador_es_atacante(ep: Episodio) -> bool:
    return ep.ganador == ep.enfrentamiento.atacante


def preparar(estado_antes: dict, ep: Episodio, estado_despues: dict, mapa: MapaGalicia, episodio: int) -> Conquista:
    f = ep.enfrentamiento
    gana_a = _ganador_es_atacante(ep)
    ventana = mapa.ventana_enfrentamiento(estado_antes, f.atacante, f.defensor, E.ANCHO / M.MAPA_ALTO)
    rot_g = ("CAMPIÓN", E.ORO, E.FONDO)
    rot_p = ("MALOGRADO", E.GRIS_EMPATE, E.BLANCO)
    base_antes, _ = M.fotograma_base(estado_antes, f, mapa, episodio)
    base_despues, _ = M.fotograma_base(estado_antes, f, mapa, episodio, rotulos=(rot_g, rot_p) if gana_a else (rot_p, rot_g))
    # orden de extensión: del concello del perdedor más cercano a la frontera hacia dentro
    contacto = mapa.gdf.geometry[f.concello_atacante if gana_a else f.concello_defensor].centroid
    orden = sorted(territorio(estado_antes, ep.perdedor), key=lambda i: (mapa.gdf.geometry[i].centroid.distance(contacto), i))
    contornos = [(mapa.geometria(territorio(estado_despues, ep.ganador)), E.ORO, 6)]
    banda_final = mapa.dibujar(estado_despues, ventana, E.ANCHO, M.MAPA_ALTO, contornos=contornos, nombres=[ep.ganador])
    vacas = estado_antes["donos"][ep.perdedor]["vacas"]
    return Conquista(estado_antes, estado_despues, f, ep.ganador, ep.perdedor, mapa, base_antes, base_despues, ventana,
                     orden, vacas, len(orden), M.CX_A if gana_a else M.CX_D, -1 if gana_a else 1, banda_final)


def _progreso(t: float) -> float:
    return D.salida_cubica((t - T_EXTENSION) / D_EXTENSION) if t > T_EXTENSION else 0.0


def _estado_parcial(ctx: Conquista, n: int) -> dict:
    """Estado con los `n` primeros concellos del perdedor ya del color del ganador."""
    concellos = dict(ctx.estado_antes["concellos"])
    for i in ctx.orden[:n]:
        concellos[i] = {**concellos[i], "dono": ctx.ganador}
    return {**ctx.estado_antes, "concellos": concellos}


def _banda_parcial(ctx: Conquista, n: int) -> Image.Image:
    cache = ctx.__dict__.setdefault("_cache", {})
    if n not in cache:
        f = ctx.f
        conflicto = [(ctx.mapa.geometria([c]), E.CONFLICTO, 6) for c in (f.concello_atacante, f.concello_defensor)]
        cache[n] = ctx.mapa.dibujar(_estado_parcial(ctx, n), ctx.ventana, E.ANCHO, M.MAPA_ALTO, contornos=conflicto)
    return cache[n]


# ---------- Confeti ----------

COLORES_CONFETI = (E.ORO, E.CONFLICTO, E.MAR, E.VERDE_PUNTOS, "#FFFFFF", "#FF8A00")


@functools.lru_cache(maxsize=4)
def _particulas(clave: str, n: int) -> tuple:
    rng = random.Random(clave)
    out = []
    for _ in range(n):
        ang = rng.uniform(math.radians(200), math.radians(340))  # hacia arriba, en abanico
        v = rng.uniform(380, 900)
        out.append((math.cos(ang) * v, math.sin(ang) * v, rng.uniform(0, 6.28), rng.uniform(-9, 9),
                    rng.choice(COLORES_CONFETI), rng.uniform(10, 20), rng.uniform(0.0, 0.12)))
    return tuple(out)


def _confeti(img: Image.Image, t: float, x0: float, y0: float, clave: str, n: int = 46, vida: float = 2.2) -> None:
    """Chorro de confeti que sale de (x0, y0) en el instante 0 y cae con gravedad."""
    if t < 0 or t > vida:
        return
    d = ImageDraw.Draw(img)
    for vx, vy, giro, vgiro, color, tam, retraso in _particulas(clave, n):
        tt = t - retraso
        if tt <= 0:
            continue
        x = x0 + vx * tt * (1 - 0.35 * tt / vida)
        y = y0 + vy * tt + 900 * tt * tt / 2
        a = giro + vgiro * tt
        ancho = abs(math.cos(a * 1.7)) * tam + 3  # «vuelta» del papelito
        c, s = math.cos(a), math.sin(a)
        pts = [(x + c * dx - s * dy, y + s * dx + c * dy)
               for dx, dy in ((-ancho / 2, -tam / 3), (ancho / 2, -tam / 3), (ancho / 2, tam / 3), (-ancho / 2, tam / 3))]
        if 0 <= y < E.ALTO + 40:
            d.polygon(pts, fill=color)


@functools.lru_cache(maxsize=1)
def _sprites() -> tuple[Image.Image, Image.Image]:
    return D.gaita_sprite(ALTO_GAITA), D.destello_sprite(300)


@functools.lru_cache(maxsize=8)
def _pastilla(texto: str) -> Image.Image:
    return E.crear_pastilla(texto, E.T_MIN - 4, 22, semilla=texto)


def _plural(n: int) -> str:
    return f"+{n} concello" if n == 1 else f"+{n} concellos"


def fotograma(ctx: Conquista, t: float) -> Image.Image:
    """Fotograma de la conquista en el instante `t` (segundos), sin estado."""
    img = (ctx.base_antes if t < T_ROTULOS else ctx.base_despues).copy()
    p = _progreso(t)
    if t >= T_EXTENSION:
        if p >= 1.0:
            banda = ctx.banda_final
        else:
            pasos = min(ctx.n_concellos, PASOS_MAX)
            n = math.ceil(ctx.n_concellos * math.floor(p * pasos) / pasos)
            banda = _banda_parcial(ctx, n)
        img.paste(banda, (0, M.MAPA_Y0))
    if t >= T_ROTULOS:  # destello al cambiar los rótulos
        u = D.limitar((t - T_ROTULOS) / 0.3)
        gaita, destello = _sprites()
        D.pegar(img, destello, ctx.cx_ganador, M.Y_ROTULO + 22, escala=0.5 + 0.7 * u, opacidad=(1 - u) * 0.9)
    gaita, _ = _sprites()
    if t >= T_GAITA:
        e = D.salida_rebote((t - T_GAITA) / 0.5)
        balanceo = 7 * math.sin((t - T_GAITA) * 7) * D.limitar((t - T_GAITA) / 0.3) + 12 * ctx.lado_ganador
        sprite = gaita.rotate(-balanceo, resample=Image.BICUBIC, expand=True)
        D.pegar(img, sprite, X_GAITA, Y_GAITA, escala=e)
    if t >= T_PASTILLAS:
        cx = ctx.cx_ganador if ctx.lado_ganador < 0 else ctx.cx_ganador + 125
        for n, (txt, y) in enumerate(((f"+{M.num(ctx.vacas_ganadas)} {E.ICONO_VACA}", Y_GAITA - 50),
                                      (_plural(ctx.n_concellos), Y_GAITA + 50))):
            u = (t - T_PASTILLAS - 0.15 * n) / 0.35
            D.pegar(img, _pastilla(txt), cx, y, escala=D.salida_rebote(u))
    _confeti(img, t - T_GAITA, X_GAITA, Y_GAITA - 40, "a")
    _confeti(img, t - T_CONFETI2, X_GAITA, Y_GAITA - 40, "b", n=30, vida=1.8)
    return img


def numero_de_fotogramas(fps: int = E.FPS) -> int:
    return math.ceil(DURACION * fps)


def renderizar(ctx: Conquista, ruta: Path, fps: int = E.FPS) -> Path:
    return escribir_video((fotograma(ctx, i / fps) for i in range(numero_de_fotogramas(fps))), ruta, fps)


def conquista_de_muestra(semilla: str = "muestra", previas: int = 106, episodio: int = 27, mapa: MapaGalicia | None = None) -> Conquista:
    """Conquista tras `previas` batallas: la siguiente batalla de la serie de muestra."""
    mapa = mapa or MapaGalicia()
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    despues, ep = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, previas + 1)))
    return preparar(estado, ep, despues, mapa, episodio)


def generar(carpeta: Path = CARPETA) -> list[Path]:
    ctx = conquista_de_muestra()
    carpeta.mkdir(parents=True, exist_ok=True)
    fotograma(ctx, 3.2).save(carpeta / "conquista.png")
    return [renderizar(ctx, carpeta / "conquista.mp4"), carpeta / "conquista.png"]


if __name__ == "__main__":
    for ruta in generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA):
        print(ruta)
