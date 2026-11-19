"""Escenas del vídeo completo y montaje del episodio (paso 4.6).

Un vídeo = intro (fase 1) + 3 × [selección de atacante y defensor (fases 2–3) + duelo y dados (4–5)
+ conquista (6)] (fase 7) + cierre con rankings (fase 8), o, si la serie acaba, la escena especial del
campeón de Galicia en vez del cierre. Todas las escenas son funciones puras del instante y se enlazan
con un pequeño fundido cruzado.

Uso: `python -m src.render.escenas` → `output/muestras/episodio_sin_audio.mp4` (sin sonido).
"""

from __future__ import annotations

import copy
import math
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from PIL import Image, ImageDraw

from src.motor.estado import Episodio, jugar_batalla, partida_terminada
from src.motor.persistencia import jugar_episodio_detallado, nueva_partida, semilla_de_batalla
from src.datos.poblacion import cargar as cargar_poblacion
from src.motor.momentos import cargar_frases, elegir_portada
from src.motor.seleccion import Enfrentamiento, vecinos_enemigos
from src.render import animacion_batalla as AB
from src.render import conquista as CQ
from src.render import dados as D
from src.render import enfrentamiento as M
from src.render import estilo as E
from src.render import portada as PT
from src.render import ranking as R
from src.render.animacion_batalla import escribir_video
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"
FUNDIDO = 0.2          # fundido cruzado entre escenas
VELOCIDAD = 1.2 * 1.08  # el vídeo final va un 20 % más rápido (2026-11-18) y otro 8 % (2026-11-19)
DESENFOQUE = 0.4        # desenfoque de movimiento en los zooms: ± esta fracción del paso entre fotogramas
OBJETIVO = 85.0        # duración buscada del vídeo (el requisito es 80–90 s)
D_INTRO = 1.0
D_CIERRE_MIN, D_CIERRE_MAX = 10.0, 26.0
D_FINAL_SERIE = 9.0


class Escena(Protocol):
    duracion: float

    def fotograma(self, t: float) -> Image.Image: ...


def _suave(u: float) -> float:
    u = D.limitar(u)
    return u * u * (3 - 2 * u)


def _marco(img: Image.Image, y0: int, alto: int) -> None:
    d = ImageDraw.Draw(img)
    d.rectangle((0, y0 - 6, E.ANCHO, y0 - 1), fill=E.ORO)
    d.rectangle((0, y0 + alto, E.ANCHO, y0 + alto + 6), fill=E.ORO)


def _mezclar(a: Image.Image, b: Image.Image, p: float) -> Image.Image:
    return Image.blend(a, b, D.limitar(p))


# Durante el sorteo del atacante el mapa es más alto (Galicia se ve más grande) y el panel queda
# desplazado hacia abajo; al hacer zoom al atacante el mapa encoge y el panel sube, en un solo movimiento.
MAPA_GRANDE = M.MAPA_ALTO + 300  # 740 px; el panel baja 300 px (debajo solo queda la zona vacía de dados)


def componer(panel: Image.Image, banda: Image.Image) -> Image.Image:
    """Fotograma con el mapa `banda` (1080 × alto variable) y el panel de `panel` (maquetación normal)
    desplazado hacia abajo lo que el mapa crece; la línea dorada va siempre justo bajo el mapa."""
    alto = banda.height
    desp = alto - M.MAPA_ALTO
    img = panel.copy()
    if desp > 0:
        franja = panel.crop((0, M.LINEA_Y, E.ANCHO, M.PANEL_FIN - desp))
        img.paste(franja, (0, M.LINEA_Y + desp))
    img.paste(banda, (0, M.MAPA_Y0))
    return img


def ventana_con_alto(v0, v1, u: float, alto: float):
    """Interpola dos ventanas (pueden tener distinta proporción) para una banda de 1080 × `alto` px:
    centro y escala como `_interpolar`; la altura de la ventana sale de la escala, así nunca se deforma."""
    x0, y0, x1, y1 = _interpolar(v0, v1, u)
    cx, cy, w = (x0 + x1) / 2, (y0 + y1) / 2, x1 - x0
    h = w * alto / E.ANCHO
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


# ---------- Fase 1: intro ----------

class EscenaIntro:
    """Título, número de episodio y mapa general de Galicia, visible desde el primer fotograma y en
    tamaño grande. Es idéntico al primer fotograma del sorteo del atacante, así que no hay corte."""

    duracion = D_INTRO
    fundido = 0.0

    def __init__(self, estado: dict, episodio: int, mapa: MapaGalicia) -> None:
        vacio, _ = M.marco_vacio(episodio)
        ventana = mapa.ventana_general(E.ANCHO / MAPA_GRANDE)
        self.img = componer(vacio, mapa.dibujar(estado, ventana, E.ANCHO, MAPA_GRANDE))

    def fotograma(self, t: float) -> Image.Image:
        return self.img.copy()


# ---------- Fases 2 y 3: selección de atacante y defensor ----------

PASOS_ATACANTE = (0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.09, 0.10, 0.12, 0.15, 0.19, 0.24, 0.30, 0.40)  # ≈2,0 s de incertidumbre
PASOS_DEFENSOR = (0.08, 0.08, 0.09, 0.10, 0.11, 0.13, 0.16, 0.20, 0.26)
D_ULTIMO, D_BLOQUEO = 0.35, 0.65  # el elegido se ve en dorado y luego se «bloquea» en rojo
D_ZOOM_SALIDA, D_ZOOM_ENTRADA, D_MORPH = 1.0, 1.3, 1.1
ROTULO_SORTEO = ("SORTEO", E.ORO, E.FONDO)


def _facil(u: float) -> float:
    """Entrada y salida muy suaves (smootherstep): sin tirones al empezar y al parar el zoom."""
    u = D.limitar(u)
    return u * u * u * (u * (6 * u - 15) + 10)


def _interpolar(v0, v1, u: float):
    """Interpola dos ventanas del mismo formato (x0, y0, x1, y1). El tamaño cambia de forma exponencial
    (velocidad de zoom constante a la vista) y el centro se desplaza en proporción al zoom, de modo que
    el destino parece acercarse en línea recta."""
    cx0, cy0, w0, h0 = (v0[0] + v0[2]) / 2, (v0[1] + v0[3]) / 2, v0[2] - v0[0], v0[3] - v0[1]
    cx1, cy1, w1, h1 = (v1[0] + v1[2]) / 2, (v1[1] + v1[3]) / 2, v1[2] - v1[0], v1[3] - v1[1]
    w, h = w0 * (w1 / w0) ** u, h0 * (h1 / h0) ** u
    if abs(w1 - w0) < 1e-6 * w0:
        s = u
    else:
        s = (1 / w - 1 / w0) / (1 / w1 - 1 / w0)
    cx, cy = cx0 + (cx1 - cx0) * s, cy0 + (cy1 - cy0) * s
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def _secuencia(elegido, otros: list, pasos: tuple, rng: random.Random) -> list:
    """Lista de candidatos del sorteo (uno por paso) que termina en `elegido`; nunca repite seguidos."""
    otros = list(otros)
    rng.shuffle(otros)
    if not otros:
        return [elegido]
    sec = [otros[i % len(otros)] for i in range(len(pasos))]
    return sec + [elegido]


class EscenaSeleccion:
    """Un solo plano continuo desde el mapa general hasta la pantalla de enfrentamiento.

    1. (si hay batalla anterior) el mapa se aleja hasta la vista general;
    2. sorteo del atacante: ≈2 s recorriendo dueños (se resalta su territorio y el panel muestra su
       nombre, silueta y vacas) hasta quedar el atacante;
    3. zoom suave hasta el atacante y sus vecinos;
    4. sorteo del defensor entre los concellos vecinos enemigos;
    5. zoom suave hasta los dos bandos mientras entra el defensor en el panel. El último fotograma es
       exactamente el primero de `EscenaBatalla`.
    """

    def __init__(self, estado: dict, f: Enfrentamiento, mapa: MapaGalicia, episodio: int, semilla: str = "",
                 ventana_previa=None, ganador_previo: str | None = None) -> None:
        self.estado, self.f, self.mapa = estado, f, mapa
        self.fundido = FUNDIDO if ventana_previa else 0.0
        prop = E.ANCHO / M.MAPA_ALTO
        self.v0 = mapa.ventana_general(E.ANCHO / MAPA_GRANDE)  # vista general, con el mapa grande
        self.v1 = mapa.ventana_atacante(estado, f.atacante, prop)
        self.v2 = mapa.ventana_enfrentamiento(estado, f.atacante, f.defensor, prop)
        self.vprev, self.ganador_previo = ventana_previa, ganador_previo
        self.vacio, _ = M.marco_vacio(episodio)
        self.completo, _ = M.fotograma_base(estado, f, mapa, episodio)
        self.final_banda = M.banda_enfrentamiento(estado, f, mapa)
        rng = random.Random(f"{semilla}{f.atacante}{f.concello_defensor}")
        # --- sorteo del atacante
        duenos = sorted(d for d in estado["donos"] if d != f.atacante and vecinos_enemigos(estado, d))
        self.sec_a = _secuencia(f.atacante, duenos, PASOS_ATACANTE, rng)
        self.pasos_a = list(PASOS_ATACANTE) + [D_ULTIMO]
        # --- sorteo del defensor
        candidatos = [c for c in vecinos_enemigos(estado, f.atacante) if c != f.concello_defensor]
        self.sec_d = _secuencia(f.concello_defensor, candidatos, PASOS_DEFENSOR, rng)
        self.pasos_d = (list(PASOS_DEFENSOR) if candidatos else []) + [D_ULTIMO]
        if candidatos:
            self.sec_d = self.sec_d[:len(self.pasos_d)]
        # --- línea de tiempo
        self.t_a = (D_ZOOM_SALIDA + 0.3) if ventana_previa else 0.4
        self.t_a_bloqueo = self.t_a + sum(self.pasos_a)
        self.t_z = self.t_a_bloqueo + D_BLOQUEO
        self.t_d = self.t_z + D_ZOOM_ENTRADA + 0.25
        self.t_d_bloqueo = self.t_d + sum(self.pasos_d)
        self.t_m = self.t_d_bloqueo + D_BLOQUEO
        self.duracion = self.t_m + D_MORPH
        self._cache: dict = {}

    # --- piezas con caché
    def _panel_candidato(self, dono: str, bloqueado: bool) -> Image.Image:
        clave = ("panel", dono, bloqueado)
        if clave not in self._cache:
            img = self.vacio.copy()
            rot = M.ROTULOS_BATALLA[0] if bloqueado else ROTULO_SORTEO
            M.dibujar_bando(img, ImageDraw.Draw(img), self.estado, self.mapa, dono, M.CX_A, rot,
                            M.x_pastilla_vacas(self.estado, self.f, dono, -1))
            self._cache[clave] = img
        return self._cache[clave]

    def _banda(self, ventana, contornos: tuple, nombres: tuple, cachear: bool = True,
               alto: int = M.MAPA_ALTO) -> Image.Image:
        """`contornos`: tuplas (clave, tipo, color, grosor); tipo «dono» (territorio) o «concello»."""
        clave = ("banda", tuple(round(v, 1) for v in ventana), contornos, nombres, alto)
        if clave in self._cache:
            return self._cache[clave]
        cont = []
        for ident, tipo, color, grosor in contornos:
            ids = self.estado["donos"][ident]["territorio"] if tipo == "dono" else [ident]
            cont.append((self.mapa.geometria(ids), color, grosor))
        img = self.mapa.dibujar(self.estado, ventana, E.ANCHO, alto, contornos=cont, nombres=list(nombres))
        if cachear:
            self._cache[clave] = img
        return img

    def _paso(self, t: float, t0: float, pasos: list[float]) -> int:
        """Índice del paso del sorteo activo en `t` (el último, si ya terminó)."""
        acum = t0
        for i, dur in enumerate(pasos):
            if t < acum + dur:
                return i
            acum += dur
        return len(pasos) - 1

    def _en_movimiento(self, t: float) -> tuple[float, float] | None:
        """Intervalo (inicio, fin) del zoom activo en `t`, o None si el mapa está quieto."""
        if self.vprev is not None and t < self.t_a:
            return 0.0, D_ZOOM_SALIDA
        if self.t_z <= t < self.t_z + D_ZOOM_ENTRADA:
            return self.t_z, self.t_z + D_ZOOM_ENTRADA
        if self.t_m <= t < self.duracion:
            return self.t_m, self.duracion
        return None

    def fotograma(self, t: float) -> Image.Image:
        """Durante los zooms promedia 3 instantes cercanos (desenfoque de movimiento): a 30 fps el mapa
        se mueve varios píxeles por fotograma y sin él se ve entrecortado. En los extremos de cada zoom
        las muestras se recortan al intervalo, así el primer y último fotograma siguen siendo exactos."""
        mov = self._en_movimiento(t)
        if mov is None:
            return self._fotograma(t)
        paso = DESENFOQUE * VELOCIDAD / E.FPS
        ini, fin = mov
        a, c = max(ini, t - paso), min(fin - 1e-6, t + paso)
        img = self._fotograma(t)
        if c - a < 1e-9:
            return img
        return Image.blend(Image.blend(self._fotograma(a), img, 0.5), self._fotograma(c), 1 / 3)

    def _fotograma(self, t: float) -> Image.Image:
        f, ORO, ROJO = self.f, E.ORO, E.CONFLICTO
        if t >= self.duracion:
            return self.completo.copy()
        # 1) alejarse desde la batalla anterior (el mapa crece a la vez que se aleja)
        if self.vprev is not None and t < self.t_a:
            u = _facil(t / D_ZOOM_SALIDA)
            alto = round(M.MAPA_ALTO + (MAPA_GRANDE - M.MAPA_ALTO) * u)
            ventana = ventana_con_alto(self.vprev, self.v0, u, alto)
            banda = self._banda(ventana, ((self.ganador_previo, "dono", ORO, 6),) if u < 1 else (), (),
                                cachear=False, alto=alto)
            return componer(self.vacio, banda)
        # 2) sorteo del atacante (mapa general grande)
        if t < self.t_z:
            i = self._paso(t, self.t_a, self.pasos_a) if t >= self.t_a else None
            if i is None:
                return componer(self.vacio, self._banda(self.v0, (), (), alto=MAPA_GRANDE))
            bloqueado = t >= self.t_a_bloqueo
            cand = self.sec_a[i]
            color = ROJO if bloqueado else ORO
            clave = ("frame_a", cand, bloqueado)
            if clave not in self._cache:
                banda = self._banda(self.v0, ((cand, "dono", color, 8),), (), alto=MAPA_GRANDE)
                self._cache[clave] = componer(self._panel_candidato(cand, bloqueado), banda)
            return self._cache[clave].copy()
        panel = self._panel_candidato(f.atacante, True)
        # 3) zoom hasta el atacante: el mapa encoge y el panel sube en el mismo movimiento
        if t < self.t_z + D_ZOOM_ENTRADA:
            u = _facil((t - self.t_z) / D_ZOOM_ENTRADA)
            alto = round(MAPA_GRANDE + (M.MAPA_ALTO - MAPA_GRANDE) * u)
            ventana = ventana_con_alto(self.v0, self.v1, u, alto)
            banda = self._banda(ventana, ((f.atacante, "dono", ROJO, 6),), (), cachear=False, alto=alto)
            return componer(panel, banda)
        base_atq = ((f.atacante, "dono", ROJO, 6),)
        # 4) sorteo del defensor (vista del atacante y sus vecinos)
        if t < self.t_m:
            if t < self.t_d:
                return self._compuesto(panel, self._banda(self.v1, base_atq, (f.atacante,)))
            i = self._paso(t, self.t_d, self.pasos_d)
            bloqueado = t >= self.t_d_bloqueo
            cand = self.sec_d[min(i, len(self.sec_d) - 1)]
            cont = base_atq + ((cand, "concello", ROJO if bloqueado else ORO, 7 if not bloqueado else 6),)
            return self._compuesto(panel, self._banda(self.v1, cont, (f.atacante, f.defensor) if bloqueado else (f.atacante,)))
        # 5) zoom hasta los dos bandos; entra el defensor en el panel
        u = _facil((t - self.t_m) / D_MORPH)
        cont = ((f.concello_atacante, "concello", ROJO, 6), (f.concello_defensor, "concello", ROJO, 6))
        banda = self._banda(_interpolar(self.v1, self.v2, u), cont, (f.atacante, f.defensor), cachear=False)
        entra = _facil((t - self.t_m - 0.45) / (D_MORPH - 0.45))
        return self._compuesto(_mezclar(panel, self.completo, entra), banda)

    def _compuesto(self, panel: Image.Image, banda: Image.Image) -> Image.Image:
        return componer(panel, banda)


# ---------- Fases 4–5: duelo, dados y marcador; fase 6: conquista ----------

class EscenaBatalla:
    fundido = 0.0  # empieza exactamente en el último fotograma de la selección

    def __init__(self, estado: dict, ep: Episodio, mapa: MapaGalicia, episodio: int) -> None:
        self.base, _ = M.fotograma_base(estado, ep.enfrentamiento, mapa, episodio)
        self.r = ep.resultado
        self.T = AB.calcular_tiempos(self.r)
        self.duracion = self.T.duracion

    def fotograma(self, t: float) -> Image.Image:
        return AB.fotograma(self.base, self.r, min(t, self.duracion), self.T)


class EscenaConquista:
    duracion = CQ.DURACION
    fundido = FUNDIDO

    def __init__(self, estado_antes: dict, ep: Episodio, estado_despues: dict, mapa: MapaGalicia, episodio: int) -> None:
        self.ctx = CQ.preparar(estado_antes, ep, estado_despues, mapa, episodio)

    def fotograma(self, t: float) -> Image.Image:
        return CQ.fotograma(self.ctx, min(t, self.duracion))


# ---------- Fase 8: cierre con rankings ----------

class EscenaCierre:
    """Mapa general con el estado actual y los dos top 5."""

    fundido = FUNDIDO

    def __init__(self, estado: dict, episodio: int, mapa: MapaGalicia, duracion: float) -> None:
        self.estado, self.duracion = estado, duracion
        base, d = M.cabecera(episodio)
        alto = M.MAPA_ALTO
        ventana = mapa.ventana_general(E.ANCHO / alto)
        base.paste(mapa.dibujar(estado, ventana, E.ANCHO, alto), (0, M.MAPA_Y0))
        d.rectangle((0, M.MAPA_Y0 - 6, E.ANCHO, M.MAPA_Y0 - 1), fill=E.ORO)
        d.rectangle((0, M.LINEA_Y, E.ANCHO, M.LINEA_Y + 6), fill=E.ORO)
        E.pegar_panel(base, M.LINEA_Y + 6, M.PANEL_FIN)
        d.rectangle((0, M.PANEL_FIN, E.ANCHO, M.PANEL_FIN + 4), fill=E.FONDO)
        self.base = base

    def fotograma(self, t: float) -> Image.Image:
        img = self.base.copy()
        R.dibujar_cierre(img, self.estado, t)
        return img


# ---------- Final de la serie ----------

class EscenaFinalSerie:
    """Cuando queda un único dueño: «CAMPIÓN DE GALICIA», con gaita y confeti."""

    duracion = D_FINAL_SERIE
    fundido = FUNDIDO

    def __init__(self, estado: dict, episodio: int, mapa: MapaGalicia) -> None:
        self.estado = estado
        self.dono = next(iter(estado["donos"]))
        base, d = M.cabecera(episodio)
        alto = M.MAPA_ALTO
        base.paste(mapa.dibujar(estado, mapa.ventana_general(E.ANCHO / alto), E.ANCHO, alto), (0, M.MAPA_Y0))
        d.rectangle((0, M.MAPA_Y0 - 6, E.ANCHO, M.MAPA_Y0 - 1), fill=E.ORO)
        d.rectangle((0, M.LINEA_Y, E.ANCHO, M.LINEA_Y + 6), fill=E.ORO)
        E.pegar_panel(base, M.LINEA_Y + 6, M.PANEL_FIN)
        d.rectangle((0, M.PANEL_FIN, E.ANCHO, M.PANEL_FIN + 4), fill=E.FONDO)
        self.base = base
        self.gaita = D.gaita_sprite(300)

    def fotograma(self, t: float) -> Image.Image:
        img = self.base.copy()
        d = ImageDraw.Draw(img)
        dono = self.estado["donos"][self.dono]
        if t > 0.3:
            e = D.salida_rebote((t - 0.3) / 0.5)
            tit = D.texto_sprite("CAMPIÓN DE GALICIA", 76, E.ORO, E.FONDO, 9)
            D.pegar(img, tit, E.ANCHO / 2, 920, escala=e * min(1.0, 900 / tit.width))
        if t > 0.9:
            lineas, tam = E.dividir_nombre(dono["nome"], 84, 900)
            for n, linea in enumerate(lineas):
                E.texto_centrado(d, E.ANCHO / 2, 985 + n * (tam + 4), linea, tam, E.FONDO, borde=7, color_borde=E.BLANCO)
        if t > 1.4:
            for n, txt in enumerate((f"{len(dono['territorio'])} concellos", f"{M.num(dono['vacas'])} {E.ICONO_VACA}",
                                     f"{dono['victorias']} vitorias")):
                D.pegar(img, CQ._pastilla(txt), 200 + 340 * n, 1190, escala=D.salida_rebote((t - 1.4 - 0.15 * n) / 0.35))
        if t > 0.6:
            balanceo = 6 * math.sin(t * 6)
            D.pegar(img, self.gaita.rotate(-balanceo, resample=Image.BICUBIC, expand=True), E.ANCHO / 2, 1360,
                    escala=D.salida_rebote((t - 0.6) / 0.5))
        for k, t0 in enumerate((0.5, 1.8, 3.2, 4.6, 6.0, 7.4)):
            CQ._confeti(img, t - t0, E.ANCHO / 2 + (-300 if k % 2 else 300), 1300, f"fin{k}", n=40, vida=2.2)
        return img


# ---------- Montaje ----------

@dataclass
class Montaje:
    escenas: list
    inicios: list[float]
    duracion: float
    estado_final: dict


def montar(escenas: list, estado_final: dict) -> Montaje:
    """Coloca las escenas una tras otra; cada una solapa con la anterior su `fundido` (0 = corte exacto)."""
    inicios, fin = [], 0.0
    for e in escenas:
        ini = max(0.0, fin - getattr(e, "fundido", 0.0))
        inicios.append(ini)
        fin = ini + e.duracion
    return Montaje(escenas, inicios, fin, estado_final)


def fotograma_de_video(m: Montaje, t: float) -> Image.Image:
    """Fotograma del vídeo en el instante `t`: la escena activa, con fundido cruzado al enlazar."""
    activas = [i for i, (e, ini) in enumerate(zip(m.escenas, m.inicios)) if ini <= t < ini + e.duracion]
    if not activas:
        activas = [len(m.escenas) - 1]
    i = activas[0]
    img = m.escenas[i].fotograma(t - m.inicios[i])
    if len(activas) > 1:
        j = activas[1]
        fundido = m.escenas[j].fundido
        img = _mezclar(img, m.escenas[j].fotograma(t - m.inicios[j]), (t - m.inicios[j]) / fundido)
    return img


def construir_episodio(estado: dict, semilla_serie: str, mapa: MapaGalicia, objetivo: float = OBJETIVO,
                       recientes: list[int] | None = None) -> Montaje:
    """Juega el episodio (3 batallas) y prepara todas sus escenas. Devuelve el montaje y el estado final.
    `recientes`: ids de las frases gancho usadas en los últimos episodios (para no repetirlas)."""
    final, _, pasos = jugar_episodio_detallado(estado, semilla_serie)
    episodio = final["episodio"]
    intro = EscenaIntro(pasos[0][0], episodio, mapa)
    portada = elegir_portada(pasos, cargar_poblacion(), cargar_frases(), recientes or [],
                             random.Random(f"{semilla_serie}:portada:{episodio}"))
    escenas: list = [PT.EscenaPortada(pasos[0][0], portada, mapa, intro.img,
                                      mapa.ventana_general(E.ANCHO / MAPA_GRANDE), MAPA_GRANDE), intro]
    prop = E.ANCHO / M.MAPA_ALTO
    previa = None  # (ventana del enfrentamiento anterior, ganador)
    for n, (previo, ep) in enumerate(pasos):
        despues = pasos[n + 1][0] if n + 1 < len(pasos) else final
        escenas += [EscenaSeleccion(previo, ep.enfrentamiento, mapa, episodio, semilla_serie,
                                    ventana_previa=previa[0] if previa else None,
                                    ganador_previo=previa[1] if previa else None),
                    EscenaBatalla(previo, ep, mapa, episodio),
                    EscenaConquista(previo, ep, despues, mapa, episodio)]
        f = ep.enfrentamiento
        previa = (mapa.ventana_enfrentamiento(previo, f.atacante, f.defensor, prop), ep.ganador)
    if partida_terminada(final):
        escenas.append(EscenaFinalSerie(final, episodio, mapa))
    else:
        resto = montar(escenas, final).duracion
        escenas.append(EscenaCierre(final, episodio, mapa,
                                    min(D_CIERRE_MAX, max(D_CIERRE_MIN, objetivo - resto + FUNDIDO))))
    return montar(escenas, final)


def renderizar(m: Montaje, ruta: Path, fps: int = E.FPS, progreso: bool = False,
               velocidad: float = VELOCIDAD) -> Path:
    """Renderiza el montaje; con `velocidad` > 1 se saltan instantes (el vídeo dura duracion / velocidad)."""
    n = math.ceil(m.duracion / velocidad * fps)

    def gen():
        for i in range(n):
            if progreso and i % 150 == 0:
                print(f"  fotograma {i}/{n}", flush=True)
            yield fotograma_de_video(m, min(i / fps * velocidad, m.duracion - 1e-6))
    return escribir_video(gen(), ruta, fps)


def estado_de_muestra(semilla: str = "muestra", previas: int = 106, episodio: int = 26) -> dict:
    """Estado tras `previas` batallas (episodio actual = `episodio`), listo para jugar el siguiente."""
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    estado = copy.deepcopy(estado)
    estado["batallas_jugadas"], estado["episodio"] = previas, episodio
    return estado


def generar(carpeta: Path = CARPETA) -> Path:
    t0 = time.time()
    m = construir_episodio(estado_de_muestra(), "muestra", MapaGalicia())
    print(f"Montaje listo: {len(m.escenas)} escenas, {m.duracion:.1f} s ({time.time() - t0:.0f} s de preparación)", flush=True)
    carpeta.mkdir(parents=True, exist_ok=True)
    m.escenas[0].fotograma(0.0).save(carpeta / "portada.png")  # miniatura = primer fotograma
    ruta = renderizar(m, carpeta / "episodio_sin_audio.mp4", progreso=True)
    print(f"Render completo en {time.time() - t0:.0f} s", flush=True)
    return ruta


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA))
