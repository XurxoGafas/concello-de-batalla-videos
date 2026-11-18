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
from src.motor.seleccion import Enfrentamiento, vecinos_enemigos
from src.render import animacion_batalla as AB
from src.render import conquista as CQ
from src.render import dados as D
from src.render import enfrentamiento as M
from src.render import estilo as E
from src.render import ranking as R
from src.render.animacion_batalla import escribir_video
from src.render.mapa import MapaGalicia

CARPETA = E.RAIZ / "output" / "muestras"
FUNDIDO = 0.2          # fundido cruzado entre escenas
OBJETIVO = 85.0        # duración buscada del vídeo (el requisito es 80–90 s)
D_INTRO = 2.0
D_CIERRE_MIN, D_CIERRE_MAX = 10.0, 26.0
D_FINAL_SERIE = 9.0
MAPA_INTRO_ALTO = 840  # el mapa de la intro y del cierre ocupa más que el del enfrentamiento


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


# ---------- Fase 1: intro ----------

class EscenaIntro:
    """Título, número de episodio y el mapa de Galicia, que entra con un fundido."""

    duracion = D_INTRO

    def __init__(self, estado: dict, episodio: int, mapa: MapaGalicia) -> None:
        y0 = 420
        self.vacio, _ = M.cabecera(episodio)
        self.lleno = self.vacio.copy()
        ventana = mapa.ventana_general(E.ANCHO / MAPA_INTRO_ALTO)
        self.lleno.paste(mapa.dibujar(estado, ventana, E.ANCHO, MAPA_INTRO_ALTO), (0, y0))
        _marco(self.lleno, y0, MAPA_INTRO_ALTO)

    def fotograma(self, t: float) -> Image.Image:
        return _mezclar(self.vacio, self.lleno, _suave((t - 0.15) / 0.7))


# ---------- Fases 2 y 3: selección de atacante y defensor ----------

PASOS_SORTEO = (0.08, 0.08, 0.09, 0.10, 0.11, 0.13, 0.16, 0.20, 0.26)  # el último paso (el elegido) se queda más
D_ZOOM, T_PANEL, T_SORTEO = 1.1, 0.8, 2.1
D_BLOQUEO = 1.2


def _interpolar(v0, v1, u: float):
    """Interpola dos ventanas del mismo formato (x0, y0, x1, y1): centro lineal, tamaño exponencial."""
    cx0, cy0, w0, h0 = (v0[0] + v0[2]) / 2, (v0[1] + v0[3]) / 2, v0[2] - v0[0], v0[3] - v0[1]
    cx1, cy1, w1, h1 = (v1[0] + v1[2]) / 2, (v1[1] + v1[3]) / 2, v1[2] - v1[0], v1[3] - v1[1]
    cx, cy = cx0 + (cx1 - cx0) * u, cy0 + (cy1 - cy0) * u
    w, h = w0 * (w1 / w0) ** u, h0 * (h1 / h0) ** u
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


class EscenaSeleccion:
    """El mapa hace zoom hasta el atacante (con su silueta, nombre y vacas) y un sorteo recorre los
    concellos vecinos hasta pararse en el defensor."""

    def __init__(self, estado: dict, f: Enfrentamiento, mapa: MapaGalicia, episodio: int, semilla: str = "") -> None:
        self.estado, self.f, self.mapa = estado, f, mapa
        prop = E.ANCHO / M.MAPA_ALTO
        self.v0 = mapa.ventana_general(prop)
        self.v1 = mapa.ventana_atacante(estado, f.atacante, prop)
        base, d = M.cabecera(episodio)
        d.rectangle((0, M.MAPA_Y0 - 6, E.ANCHO, M.MAPA_Y0 - 1), fill=E.ORO)
        d.rectangle((0, M.LINEA_Y, E.ANCHO, M.LINEA_Y + 6), fill=E.ORO)
        E.pegar_panel(base, M.LINEA_Y + 6, M.PANEL_FIN)
        d.rectangle((0, M.PANEL_FIN, E.ANCHO, M.PANEL_FIN + 4), fill=E.FONDO)
        self.vacio = base
        self.con_ataque = base.copy()
        self._bloque_atacante(self.con_ataque)
        candidatos = vecinos_enemigos(estado, f.atacante)
        rng = random.Random(f"{semilla}{f.atacante}{f.concello_defensor}")
        otros = [c for c in candidatos if c != f.concello_defensor]
        rng.shuffle(otros)
        secuencia: list[str] = []
        if otros:
            n = len(PASOS_SORTEO)
            secuencia = [otros[i % len(otros)] for i in range(n)]
        secuencia.append(f.concello_defensor)
        self.secuencia = secuencia
        self.pasos = (list(PASOS_SORTEO) if otros else []) + [0.5]
        self.t_bloqueo = T_SORTEO + sum(self.pasos[:-1])
        self.duracion = self.t_bloqueo + D_BLOQUEO
        self._cache: dict = {}

    def _bloque_atacante(self, img: Image.Image) -> None:
        f, estado, mapa = self.f, self.estado, self.mapa
        d = ImageDraw.Draw(img)
        E.texto_centrado(d, M.CX_C, M.Y_ROTULO, "ATACA", E.T_MIN, E.CONFLICTO, borde=6, color_borde=E.BLANCO)
        geom = mapa.geometria(estado["donos"][f.atacante]["territorio"])
        k = M.SUPERMUESTREO
        sil = Image.new("RGBA", (300 * k, M.ALTO_SILUETA * k), (255, 255, 255, 0))
        from src.render.mapa import pintar
        pintar(ImageDraw.Draw(sil), geom, M.caja_silueta(geom.bounds, 300, M.ALTO_SILUETA, k),
               estado["donos"][f.atacante]["cor"]["colores"][0], E.FONDO, 3 * k)
        sil = sil.resize((300, M.ALTO_SILUETA), Image.LANCZOS)
        img.paste(sil.convert("RGB"), (int(M.CX_C - 150), M.Y_SILUETA), sil.getchannel("A"))
        lineas, t = E.dividir_nombre(estado["donos"][f.atacante]["nome"], 56, 760)
        for n, linea in enumerate(lineas):
            E.texto_centrado(d, M.CX_C, M.Y_NOMBRE + n * (t + 2), linea, t, E.FONDO, borde=6, color_borde=E.BLANCO)
        E.pastilla_vaca(img, M.CX_C, M.Y_VACAS, f"{M.num(estado['donos'][f.atacante]['vacas'])} vacas", E.T_MIN, 20)

    def _banda(self, ventana, candidato: str | None, bloqueado: bool, nombres_def: bool) -> Image.Image:
        clave = (tuple(round(v, 1) for v in ventana), candidato, bloqueado, nombres_def)
        if clave not in self._cache:
            f, mapa, estado = self.f, self.mapa, self.estado
            cont = [(mapa.geometria(estado["donos"][f.atacante]["territorio"]), E.CONFLICTO, 6)]
            if candidato:
                cont.append((mapa.geometria([candidato]), E.CONFLICTO if bloqueado else E.ORO, 7 if not bloqueado else 6))
            nombres = [f.atacante] + ([f.defensor] if nombres_def else [])
            self._cache[clave] = mapa.dibujar(estado, ventana, E.ANCHO, M.MAPA_ALTO, contornos=cont,
                                              nombres=nombres if ventana == self.v1 else [])
        return self._cache[clave]

    def fotograma(self, t: float) -> Image.Image:
        u = _suave(t / D_ZOOM)
        if t < D_ZOOM:
            u = round(u * 12) / 12  # el zoom se redibuja a ~13 posiciones por segundo
            ventana = self.v0 if u <= 0 else _interpolar(self.v0, self.v1, u)
            banda = self._banda(ventana, None, False, False)
        else:
            candidato, bloqueado = None, False
            if t >= T_SORTEO:
                acum = T_SORTEO
                for cand, dur in zip(self.secuencia, self.pasos):
                    if t < acum + dur:
                        candidato = cand
                        break
                    acum += dur
                else:
                    candidato = self.secuencia[-1]
                bloqueado = t >= self.t_bloqueo
            banda = self._banda(self.v1, candidato, bloqueado, bloqueado)
        base = self.con_ataque if t >= T_PANEL else self.vacio
        img = base.copy()
        if T_PANEL <= t < T_PANEL + 0.25:
            img = _mezclar(self.vacio, self.con_ataque, (t - T_PANEL) / 0.25)
        img.paste(banda, (0, M.MAPA_Y0))
        return img


# ---------- Fases 4–5: duelo, dados y marcador; fase 6: conquista ----------

class EscenaBatalla:
    def __init__(self, estado: dict, ep: Episodio, mapa: MapaGalicia, episodio: int) -> None:
        self.base, _ = M.fotograma_base(estado, ep.enfrentamiento, mapa, episodio)
        self.r = ep.resultado
        self.T = AB.calcular_tiempos(self.r)
        self.duracion = self.T.duracion

    def fotograma(self, t: float) -> Image.Image:
        return AB.fotograma(self.base, self.r, min(t, self.duracion), self.T)


class EscenaConquista:
    duracion = CQ.DURACION

    def __init__(self, estado_antes: dict, ep: Episodio, estado_despues: dict, mapa: MapaGalicia, episodio: int) -> None:
        self.ctx = CQ.preparar(estado_antes, ep, estado_despues, mapa, episodio)

    def fotograma(self, t: float) -> Image.Image:
        return CQ.fotograma(self.ctx, min(t, self.duracion))


# ---------- Fase 8: cierre con rankings ----------

class EscenaCierre:
    """Mapa general con el estado actual y los dos top 5."""

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
            for n, txt in enumerate((f"{len(dono['territorio'])} concellos", f"{M.num(dono['vacas'])} vacas",
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
    inicios, t = [], 0.0
    for e in escenas:
        inicios.append(t)
        t += e.duracion - FUNDIDO
    return Montaje(escenas, inicios, t + FUNDIDO, estado_final)


def fotograma_de_video(m: Montaje, t: float) -> Image.Image:
    """Fotograma del vídeo en el instante `t`: la escena activa, con fundido cruzado al enlazar."""
    activas = [i for i, (e, ini) in enumerate(zip(m.escenas, m.inicios)) if ini <= t < ini + e.duracion]
    if not activas:
        activas = [len(m.escenas) - 1]
    i = activas[0]
    img = m.escenas[i].fotograma(t - m.inicios[i])
    if len(activas) > 1:
        j = activas[1]
        img = _mezclar(img, m.escenas[j].fotograma(t - m.inicios[j]), (t - m.inicios[j]) / FUNDIDO)
    return img


def construir_episodio(estado: dict, semilla_serie: str, mapa: MapaGalicia, objetivo: float = OBJETIVO) -> Montaje:
    """Juega el episodio (3 batallas) y prepara todas sus escenas. Devuelve el montaje y el estado final."""
    final, _, pasos = jugar_episodio_detallado(estado, semilla_serie)
    episodio = final["episodio"]
    escenas: list = [EscenaIntro(pasos[0][0], episodio, mapa)]
    for n, (previo, ep) in enumerate(pasos):
        despues = pasos[n + 1][0] if n + 1 < len(pasos) else final
        escenas += [EscenaSeleccion(previo, ep.enfrentamiento, mapa, episodio, semilla_serie),
                    EscenaBatalla(previo, ep, mapa, episodio),
                    EscenaConquista(previo, ep, despues, mapa, episodio)]
    if partida_terminada(final):
        escenas.append(EscenaFinalSerie(final, episodio, mapa))
    else:
        resto = montar(escenas, final).duracion
        escenas.append(EscenaCierre(final, episodio, mapa, min(D_CIERRE_MAX, max(D_CIERRE_MIN, objetivo - resto + FUNDIDO))))
    return montar(escenas, final)


def renderizar(m: Montaje, ruta: Path, fps: int = E.FPS, progreso: bool = False) -> Path:
    n = math.ceil(m.duracion * fps)

    def gen():
        for i in range(n):
            if progreso and i % 150 == 0:
                print(f"  fotograma {i}/{n}", flush=True)
            yield fotograma_de_video(m, i / fps)
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
    ruta = renderizar(m, carpeta / "episodio_sin_audio.mp4", progreso=True)
    print(f"Render completo en {time.time() - t0:.0f} s", flush=True)
    return ruta


if __name__ == "__main__":
    print(generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA))
