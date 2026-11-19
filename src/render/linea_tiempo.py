"""Línea de tiempo del sonido (paso 5.2): en qué instante del montaje suena cada efecto del esquema
`docs/SONIDOS.md`. Se calcula a partir de los tiempos que ya usan las escenas, sin renderizar nada.

Los instantes están en **segundos de montaje** (antes de acelerar ×1,296); `src/audio/mezcla.py` los
pasa a tiempo de vídeo. Cada evento lleva el número del esquema (`"05"`, `"17"`…) y, si hace falta, parámetros.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.render import animacion_batalla as AB
from src.render import conquista as CQ
from src.render import escenas as ES
from src.render import portada as PT
from src.render import ranking as R
from src.render.dados import salida_cubica

T_FRASE_PORTADA = 0.25  # el «pop» de la frase suena un instante después del golpe de la silueta


@dataclass(frozen=True)
class Evento:
    t: float          # segundos de montaje
    num: str          # número del esquema: "01" … "33"
    ganancia: float = 1.0
    params: tuple = field(default_factory=tuple)  # parámetros del efecto (p. ej. N del «+N»)

    def __lt__(self, otro: "Evento") -> bool:
        return (self.t, self.num) < (otro.t, otro.num)


def tiempos_pops_extension(n_concellos: int) -> list[float]:
    """Instantes (desde el inicio de la conquista) en que el mapa se redibuja durante la extensión del color:
    uno por paso, hasta `PASOS_MAX`. Inversa de la curva `salida_cubica` que usa `conquista.fotograma`."""
    pasos = min(n_concellos, CQ.PASOS_MAX)
    return [CQ.T_EXTENSION + CQ.D_EXTENSION * (1 - (1 - k / pasos) ** (1 / 3)) for k in range(1, pasos + 1)]


def _portada(e, ini: float) -> list[Evento]:
    return [Evento(ini, "01"), Evento(ini + T_FRASE_PORTADA, "02"), Evento(ini + PT.D_FIJA, "03")]


def _seleccion(e: ES.EscenaSeleccion, ini: float) -> list[Evento]:
    return [Evento(ini + e.t_a, "05", params=tuple(e.pasos_a)),
            Evento(ini + e.t_a_bloqueo, "06"),
            Evento(ini + e.t_z, "07"),
            Evento(ini + e.t_d, "08", params=tuple(e.pasos_d)),
            Evento(ini + e.t_d_bloqueo, "06"),
            Evento(ini + e.t_m, "10")]


def _batalla(e: ES.EscenaBatalla, ini: float) -> list[Evento]:
    T, r = e.T, e.r
    ev = [Evento(ini + T.espadas, "11"), Evento(ini + T.espadas, "12"),
          Evento(ini + T.espadas + AB.D_ENTRADA, "13"), Evento(ini + T.espadas + AB.D_ENTRADA, "14")]
    for ti, tir in zip(T.tiradas, r.tiradas):
        cae = ti + AB.D_RODAR
        ev += [Evento(ini + ti, "15"), Evento(ini + cae, "16")]
        puntos = max(tir.puntos_a, tir.puntos_b)
        if puntos:
            ev += [Evento(ini + cae, "19"), Evento(ini + cae + 0.1, "17", params=(min(5, puntos),))]
        else:
            ev.append(Evento(ini + cae + 0.1, "18"))
    if T.mult is not None:
        n = round((max(r.mult_a, r.mult_b) - 1) * 10)
        ev.append(Evento(ini + T.mult, "20", params=(min(5, max(1, n)),)))
    if T.sd is not None:
        ev.append(Evento(ini + T.sd, "22", params=(len(T.rondas_sd),)))
        ev += [Evento(ini + ts, "23") for ts in T.rondas_sd]
    ev.append(Evento(ini + T.final, "21"))
    return ev


def _conquista(e: ES.EscenaConquista, ini: float) -> list[Evento]:
    n = e.ctx.n_concellos
    pasos = min(n, CQ.PASOS_MAX)
    ev = [Evento(ini + CQ.T_ROTULOS, "24"), Evento(ini + CQ.T_GAITA, "25"),
          Evento(ini + CQ.T_GAITA, "26"), Evento(ini + CQ.T_CONFETI2, "26"),
          Evento(ini + CQ.T_PASTILLAS, "27"), Evento(ini + CQ.T_PASTILLAS + 0.15, "27", 0.9)]
    ev += [Evento(ini + t, "28", params=(k, pasos)) for k, t in enumerate(tiempos_pops_extension(n))]
    return ev


def _cierre(e: ES.EscenaCierre, ini: float, t0: float = 0.6, paso: float = 0.28) -> list[Evento]:
    """31 al aparecer el panel; un «pop» (32) por cada tanda de filas (de la 5.ª a la 1.ª, las dos listas a la vez);
    la tanda de la fila 1 lleva campanilla."""
    vit, ter = R.clasificaciones(e.estado)
    llegadas: dict[float, bool] = {}
    for lista in (vit, ter):
        n = len(lista)
        for puesto in range(1, n + 1):
            t = round(t0 + (n - puesto) * paso, 4)
            llegadas[t] = llegadas.get(t, False) or puesto == 1
    return [Evento(ini, "31")] + [Evento(ini + t, "32", params=(primera,)) for t, primera in sorted(llegadas.items())]


def eventos(m: ES.Montaje) -> list[Evento]:
    """Todos los eventos de sonido del montaje, ordenados por instante."""
    ev: list[Evento] = []
    for i, (e, ini) in enumerate(zip(m.escenas, m.inicios)):
        if i > 0 and getattr(e, "fundido", 0.0) > 0:
            ev.append(Evento(ini, "30"))
        if isinstance(e, PT.EscenaPortada):
            ev += _portada(e, ini)
        elif isinstance(e, ES.EscenaSeleccion):
            ev += _seleccion(e, ini)
        elif isinstance(e, ES.EscenaBatalla):
            ev += _batalla(e, ini)
        elif isinstance(e, ES.EscenaConquista):
            ev += _conquista(e, ini)
        elif isinstance(e, ES.EscenaAlejamiento):
            ev.append(Evento(ini, "29"))
        elif isinstance(e, ES.EscenaCierre):
            ev += _cierre(e, ini)
        elif isinstance(e, ES.EscenaFinalSerie):
            ev.append(Evento(ini + 0.3, "33"))
        # EscenaIntro (04): silencio
    return sorted(ev)
