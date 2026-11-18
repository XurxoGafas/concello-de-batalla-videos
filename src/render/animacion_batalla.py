"""Animación de una batalla completa (fases 4–5 del vídeo, paso 4.4).

`calcular_tiempos(r)` fija la línea de tiempo (segundos) a partir del resultado de la batalla y
`fotograma(base, r, t, tm)` dibuja el fotograma del instante `t` **sin estado** (misma `t`, mismo
fotograma), de modo que cualquier instante se puede repetir o saltar. `base` es la pantalla de
enfrentamiento (`fotograma_base`, 4.3), que se dibuja una sola vez por batalla.

Secuencia: pantalla de enfrentamiento → espadas cruzadas → 3 tiradas (los dados ruedan, se
paran, el ganador de la tirada se resalta y sale su «+N», el marcador sube) → multiplicador
(si lo hay) → muerte súbita (si hay empate) → recuadro dorado en el ganador.

Uso: `python -m src.render.animacion_batalla` → `output/muestras/batalla_sin_audio.mp4`
(y `batalla_muerte_subita.mp4`).
"""

from __future__ import annotations

import math
import random
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from src.motor.batalla import ResultadoBatalla, simular_batalla
from src.motor.estado import jugar_batalla
from src.motor.persistencia import nueva_partida, semilla_de_batalla
from src.motor.seleccion import elegir_enfrentamiento
from src.render import dados as D
from src.render import estilo as E
from src.render import marcador as M
from src.render.enfrentamiento import CARPETA, fotograma_base
from src.render.mapa import MapaGalicia

# Duraciones (segundos)
D_FASE3, D_ESPADAS = 0.8, 1.1
D_RODAR, D_ASENTAR, D_PAUSA = 0.9, 0.4, 0.5
D_MULT = 1.6
D_SD_ENTRADA, D_SD_RESULTADO = 0.5, 1.1
D_FINAL = 1.5


@dataclass
class Tiempos:
    espadas: float = 0.0
    dados: float = 0.0  # empieza la primera tirada y se ven los huecos
    tiradas: list[float] = field(default_factory=list)  # instante en que empieza a rodar cada tirada
    mult: float | None = None
    sd: float | None = None  # empieza la tarjeta de muerte súbita
    rondas_sd: list[float] = field(default_factory=list)  # inicio de cada ronda
    sd_fin: float | None = None
    final: float = 0.0
    duracion: float = 0.0


def calcular_tiempos(r: ResultadoBatalla) -> Tiempos:
    T = Tiempos(espadas=D_FASE3)
    t = T.dados = D_FASE3 + D_ESPADAS
    for _ in r.tiradas:
        T.tiradas.append(t)
        t += D_RODAR + D_ASENTAR + D_PAUSA
    if r.mult_a > 1 or r.mult_b > 1:
        T.mult = t
        t += D_MULT
    if r.muerte_subita:
        T.sd = t
        t += D_SD_ENTRADA
        for _ in r.muerte_subita:
            T.rondas_sd.append(t)
            t += D_RODAR + D_SD_RESULTADO
        T.sd_fin = t
    T.final = t
    T.duracion = t + D_FINAL
    return T


def _marcador_en(r: ResultadoBatalla, T: Tiempos, t: float) -> tuple[str, str, float, float]:
    """Textos del marcador en el instante t y el «pop» de cada total."""
    pa = pb = 0
    pop_a = pop_b = 1.0
    for i, (ti, tir) in enumerate(zip(T.tiradas, r.tiradas)):
        aterriza = ti + D_RODAR
        if t >= aterriza:
            pa += tir.puntos_a
            pb += tir.puntos_b
            u = (t - aterriza) / 0.35
            if u < 1:
                if tir.puntos_a:
                    pop_a = 1 + 0.3 * (1 - u)
                if tir.puntos_b:
                    pop_b = 1 + 0.3 * (1 - u)
    a, b = str(pa), str(pb)
    if T.mult is not None and t >= T.mult + 0.5:
        a, b = M.formato_decimas(r.decimas_a), M.formato_decimas(r.decimas_b)
        u = (t - T.mult - 0.5) / 0.35
        if u < 1:
            pop_a = pop_b = 1 + 0.3 * (1 - u)
    return a, b, pop_a, pop_b


def _columnas(img: Image.Image, r: ResultadoBatalla, T: Tiempos, t: float) -> None:
    for i, (ti, tir) in enumerate(zip(T.tiradas, r.tiradas)):
        y = D.y_fila(i) + D.LADO / 2
        for cx, valor, ganado, fuera, lado in ((D.COL_A, tir.dado_a, tir.puntos_a, -1, "a"),
                                               (D.COL_D, tir.dado_b, tir.puntos_b, 1, "b")):
            if t < ti:
                D.pegar(img, D.hueco_sprite(D.LADO), cx, y)
            elif t < ti + D_RODAR:
                dy = D.rebote(t - ti, D_RODAR)
                D.pegar(img, D.dado_sprite(D.LADO, D.cara_rodando(f"{i}{lado}", t - ti)), cx, y + dy)
            else:
                u = (t - ti - D_RODAR) / D_ASENTAR
                pop = 1 + (0.18 * math.sin(math.pi * D.limitar(u)) if ganado else 0.0)
                D.pegar(img, D.dado_sprite(D.LADO, valor, resaltado=ganado > 0), cx, y, escala=pop)
                txt = f"+{ganado}" if ganado else ("=" if tir.puntos_a == tir.puntos_b else "")
                if txt:
                    sprite = D.insignia_sprite(txt, E.VERDE_PUNTOS if ganado else E.GRIS_EMPATE)
                    bx = cx + fuera * (D.LADO / 2 + 14 + (sprite.width - 8) / 2)
                    D.pegar(img, sprite, bx, y, escala=D.salida_rebote((t - ti - D_RODAR - 0.1) / 0.3))


def _muerte_subita(img: Image.Image, r: ResultadoBatalla, T: Tiempos, t: float) -> None:
    caja = M.tarjeta_muerte_subita(img, (t - T.sd) / D_SD_ENTRADA)
    if t < T.sd + D_SD_ENTRADA:
        return
    ronda = max(i for i, ts in enumerate(T.rondas_sd) if t >= ts)
    ts, rd = T.rondas_sd[ronda], r.muerte_subita[ronda]
    cy = (caja[1] + caja[3]) / 2 + 28
    lado = 110
    for cx, valor, lado_id, otro in ((330, rd.dado_a, "a", rd.dado_b), (E.ANCHO - 330, rd.dado_b, "b", rd.dado_a)):
        if t < ts + D_RODAR:
            dy = D.rebote(t - ts, D_RODAR, 18)
            sprite = D.dado_sprite(lado, D.cara_rodando(f"sd{ronda}{lado_id}", t - ts))
            D.pegar(img, sprite, cx, cy + dy)
        else:
            gana = valor > otro
            D.pegar(img, D.dado_sprite(lado, valor, resaltado=gana), cx, cy,
                    escala=1 + (0.15 * math.sin(math.pi * D.limitar((t - ts - D_RODAR) / 0.4)) if gana else 0))
    E.texto_centrado_exacto(ImageDraw.Draw(img), E.ANCHO / 2, cy, "VS", 56, E.ORO, borde=7, color_borde=E.FONDO)


def fotograma(base: Image.Image, r: ResultadoBatalla, t: float, T: Tiempos | None = None) -> Image.Image:
    """Fotograma de la batalla en el instante `t` (segundos), sin estado."""
    T = T or calcular_tiempos(r)
    img = base.copy()
    if t < T.espadas:
        return img
    if t < T.dados:  # espadas cruzadas
        fade = 1 - D.limitar((t - (T.dados - 0.2)) / 0.2)
        D.pegar(img, D.espadas_sprite(), E.ANCHO / 2, D.Y_MEDIO, escala=D.salida_rebote((t - T.espadas) / 0.5),
                opacidad=fade)
        return img
    _columnas(img, r, T, t)
    a, b, pop_a, pop_b = _marcador_en(r, T, t)
    en_sd = T.sd is not None and T.sd <= t < T.sd_fin
    if not en_sd:
        M.dibujar_totales(img, a, b, pop_a, pop_b)
        if T.mult is not None and t >= T.mult:
            M.dibujar_multiplicador(img, "a" if r.mult_a > 1 else "b", max(r.mult_a, r.mult_b),
                                    (t - T.mult) / 0.6)
    if en_sd:
        _muerte_subita(img, r, T, t)
    elif t >= T.final:
        M.marcar_ganador(img, r.ganador, (t - T.final) / 0.5)
    return img


def numero_de_fotogramas(T: Tiempos, fps: int = E.FPS) -> int:
    return math.ceil(T.duracion * fps)


def escribir_video(fotogramas, ruta: Path, fps: int = E.FPS) -> Path:
    """Codifica los fotogramas (PIL RGB) a MP4 H.264 con ffmpeg, sin audio."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{E.ANCHO}x{E.ALTO}",
           "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(ruta)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    try:
        for f in fotogramas:
            p.stdin.write(f.tobytes())
    finally:
        p.stdin.close()
        if p.wait() != 0:
            raise RuntimeError("ffmpeg falló al codificar el vídeo")
    return ruta


def renderizar(base: Image.Image, r: ResultadoBatalla, ruta: Path, fps: int = E.FPS) -> Path:
    T = calcular_tiempos(r)
    n = numero_de_fotogramas(T, fps)
    return escribir_video((fotograma(base, r, i / fps, T) for i in range(n)), ruta, fps)


def preparar(semilla: str = "muestra", previas: int = 106):
    """Estado tras `previas` batallas y el siguiente enfrentamiento (como en las muestras)."""
    estado = nueva_partida()
    for n in range(1, previas + 1):
        estado, _ = jugar_batalla(estado, random.Random(semilla_de_batalla(semilla, n)))
    f = elegir_enfrentamiento(estado, random.Random(semilla_de_batalla(semilla, previas + 1)))
    return estado, f


def batalla_de_muestra(estado: dict, f, semilla: str, muerte_subita: bool) -> ResultadoBatalla:
    """Una batalla de muestra entre los bandos de `f`: con o sin muerte súbita (busca una semilla)."""
    va, vd = estado["donos"][f.atacante]["vacas"], estado["donos"][f.defensor]["vacas"]
    for k in range(20000):
        r = simular_batalla(va, vd, rng=random.Random(f"{semilla}-{k}"))
        if bool(r.muerte_subita) == muerte_subita:
            return r
    raise RuntimeError("no se encontró una batalla de muestra con esas condiciones")


def generar(carpeta: Path = CARPETA) -> list[Path]:
    estado, f = preparar()
    base, _ = fotograma_base(estado, f, MapaGalicia(), 27)
    rutas = []
    for nombre, sd in (("batalla_sin_audio.mp4", False), ("batalla_muerte_subita.mp4", True)):
        r = batalla_de_muestra(estado, f, "anim", sd)
        rutas.append(renderizar(base, r, carpeta / nombre))
    return rutas


if __name__ == "__main__":
    for ruta in generar(Path(sys.argv[1]) if len(sys.argv) > 1 else CARPETA):
        print(ruta)
