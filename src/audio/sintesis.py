"""Síntesis de los efectos de sonido (paso 5.1), con numpy: sin muestras ni licencias de terceros.

Todos los efectos se generan ya a la duración que tendrán en el vídeo final (que va a ×1,296 respecto al
montaje). WAV de 16 bits, 44,1 kHz, estéreo. Los efectos se numeran según `docs/SONIDOS.md`.

Uso: `python -m src.audio.sintesis [número ...]` (sin argumentos, genera todos los definidos).
"""

from __future__ import annotations

import sys
import wave
from pathlib import Path

import numpy as np

SR = 44100
CARPETA = Path(__file__).resolve().parents[2] / "assets" / "audio"
VELOCIDAD = 1.2 * 1.08  # el montaje se reproduce a esta velocidad


# ---------- Utilidades ----------

def t_(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def env_exp(t: np.ndarray, tau: float, ataque: float = 0.002) -> np.ndarray:
    """Ataque lineal muy corto y caída exponencial."""
    e = np.exp(-t / tau)
    if ataque > 0:
        e *= np.minimum(1.0, t / ataque)
    return e


def seno_barrido(t: np.ndarray, f0: float, f1: float, tau_f: float) -> np.ndarray:
    """Seno cuya frecuencia va de f0 a f1 (exponencialmente, con constante tau_f)."""
    f = f1 + (f0 - f1) * np.exp(-t / tau_f)
    fase = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(fase)


def ruido(n: int, semilla: int) -> np.ndarray:
    return np.random.default_rng(semilla).standard_normal(n)


def paso_bajo(x: np.ndarray, corte: float) -> np.ndarray:
    """Paso bajo por FFT (corte brusco suavizado) para ruidos."""
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (f / corte) ** 4)
    return np.fft.irfft(X, len(x))


def filtro_banda_variable(x: np.ndarray, corte: np.ndarray, q: float) -> np.ndarray:
    """Filtro de variable de estado (paso banda) con frecuencia central variable en el tiempo."""
    y = np.zeros_like(x)
    low = band = 0.0
    for i in range(len(x)):
        f = 2 * np.sin(np.pi * min(corte[i], SR / 6) / SR)
        low += f * band
        high = x[i] - low - band / q
        band += f * high
        y[i] = band
    return y


def fundidos(x: np.ndarray, entrada: float = 0.003, salida: float = 0.01) -> np.ndarray:
    """Fundidos de entrada y salida (evitan clics); el tiempo va en el eje 0 (admite mono o estéreo)."""
    x = x.copy()
    n_in, n_out = int(entrada * SR), int(salida * SR)
    forma = (-1,) + (1,) * (x.ndim - 1)
    if n_in:
        x[:n_in] *= np.linspace(0, 1, n_in).reshape(forma)
    if n_out:
        x[-n_out:] *= np.linspace(1, 0, n_out).reshape(forma)
    return x


def normalizar(x: np.ndarray, pico_db: float = -3.0) -> np.ndarray:
    """Escala para que el pico quede a `pico_db` dBFS."""
    return x * (10 ** (pico_db / 20) / max(1e-9, np.max(np.abs(x))))


def estereo(izq: np.ndarray, der: np.ndarray | None = None) -> np.ndarray:
    return np.stack([izq, izq if der is None else der], axis=1)


def guardar(ruta: Path, audio: np.ndarray) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2")
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(audio.shape[1])
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return ruta


def medidas(audio: np.ndarray) -> dict:
    mono = audio.mean(axis=1)
    pico = float(np.max(np.abs(audio)))
    return {"duracion_s": round(len(audio) / SR, 3), "pico_dBFS": round(20 * np.log10(pico), 1),
            "rms_dBFS": round(20 * np.log10(np.sqrt(np.mean(mono ** 2)) + 1e-12), 1)}


# ---------- Efectos ----------

def golpe_portada() -> np.ndarray:
    """01 · Portada: aparece la silueta. Golpe grave (bombo con caída de tono) + soplido de aire grave y un
    brillo agudo que se apaga más despacio. ≈1,3 s."""
    dur = 1.3
    t = t_(dur)
    bombo = seno_barrido(t, 130, 42, 0.07) * env_exp(t, 0.28, 0.002)
    cuerpo = 0.5 * np.sin(2 * np.pi * 55 * t) * env_exp(t, 0.55, 0.01)
    aire = paso_bajo(ruido(len(t), 1), 900) * env_exp(t, 0.09, 0.001) * 1.4
    brillo_l = np.zeros_like(t)
    brillo_r = np.zeros_like(t)
    for k, f in enumerate((1568.0, 2093.0, 2637.0, 3136.0, 4186.0)):  # acorde de Do mayor muy agudo
        env = env_exp(t - 0.02, 0.45 - 0.05 * k, 0.004) * (t >= 0.02) * (0.11 / (1 + 0.25 * k))
        brillo_l += np.sin(2 * np.pi * f * t + k) * env
        brillo_r += np.sin(2 * np.pi * f * 1.002 * t + 2 * k) * env  # ligera diferencia: ensancha
    base = bombo * 1.0 + cuerpo + aire
    izq, der = base + brillo_l, base + brillo_r
    return normalizar(fundidos(estereo(izq, der), 0.001, 0.05), -3.0)


def pop_frase() -> np.ndarray:
    """02 · Portada: aparece la frase. «Pop» de burbuja, corto y suave. ≈0,18 s."""
    dur = 0.18
    t = t_(dur)
    tono = seno_barrido(t, 1100, 420, 0.025) * env_exp(t, 0.035, 0.001)
    clic = paso_bajo(ruido(len(t), 2), 5000) * env_exp(t, 0.004, 0.0005) * 0.35
    x = tono + clic
    return normalizar(fundidos(estereo(x), 0.0005, 0.02), -6.0)


def whoosh_vuelo() -> np.ndarray:
    """03 · Portada: la silueta vuela al mapa (0,8 s de montaje = 0,62 s de vídeo). Whoosh ascendente:
    ruido filtrado cuyo tono sube de grave a agudo, con volumen creciente y caída rápida; se mueve de
    izquierda a derecha."""
    dur = 0.8 / VELOCIDAD
    t = t_(dur)
    u = t / dur
    corte = 250 * (14 ** (u ** 1.3))  # 250 Hz → ≈3,5 kHz
    x = filtro_banda_variable(ruido(len(t), 3), corte, q=2.2)
    env = (u ** 1.6) * np.where(u < 0.86, 1.0, np.clip((1 - u) / 0.14, 0, 1))
    x *= env
    pan = u
    izq, der = x * np.sqrt(1 - pan), x * np.sqrt(pan)
    return normalizar(fundidos(estereo(izq, der), 0.01, 0.015), -4.0)


# Pasos del sorteo del atacante (montaje): los de `escenas.PASOS_ATACANTE` + el último (D_ULTIMO)
PASOS_SORTEO_ATACANTE = (0.07, 0.07, 0.07, 0.07, 0.07, 0.07, 0.09, 0.10, 0.12, 0.15, 0.19, 0.24, 0.30, 0.40, 0.35)


def _tic(frecuencia: float, fuerza: float) -> np.ndarray:
    """Un «tic» de bloque de madera: dos parciales inarmónicos con caída rápida y un clic de aire."""
    t = t_(0.06)
    x = (np.sin(2 * np.pi * frecuencia * t) * env_exp(t, 0.011, 0.0005)
         + 0.45 * np.sin(2 * np.pi * frecuencia * 2.76 * t) * env_exp(t, 0.006, 0.0003)
         + 0.25 * paso_bajo(ruido(len(t), 5), 6000) * env_exp(t, 0.002, 0.0002))
    return x * fuerza


def _secuencia_tics(pasos_montaje: tuple, f_ini: float, semitonos: float, fuerza_ini: float, pico_db: float,
                    semilla_pan: float = 2.1) -> np.ndarray:
    """Un tic al inicio de cada paso del sorteo: cada vez más agudo (`semitonos` en total) y más fuerte."""
    pasos = [p / VELOCIDAD for p in pasos_montaje]
    n = len(pasos)
    dur = sum(pasos) + 0.1
    izq, der = np.zeros(int(dur * SR)), np.zeros(int(dur * SR))
    inicio = 0.0
    for i, paso in enumerate(pasos):
        u = i / (n - 1)
        tic = _tic(f_ini * 2 ** (semitonos * u / 12), fuerza_ini + (1 - fuerza_ini) * u)
        a = int(inicio * SR)
        reparto = 0.5 + 0.18 * np.sin(i * semilla_pan)  # los tics bailan un poco entre izquierda y derecha
        izq[a:a + len(tic)] += tic * np.sqrt(1 - reparto)
        der[a:a + len(tic)] += tic * np.sqrt(reparto)
        inicio += paso
    return normalizar(estereo(izq, der), pico_db)


def tics_sorteo_atacante() -> np.ndarray:
    """05 · Sorteo del atacante: un tic cada vez que se resalta otro dueño (15 en total, con los pasos
    reales de la animación: empiezan rápidos y se frenan). Cada tic es más agudo y más fuerte que el
    anterior (de Mi5 a Mi6 por semitonos); el último, el del elegido, es el más brillante. ≈1,8 s.
    En el montaje, cada tic va en el instante exacto en que se resalta ese dueño."""
    return _secuencia_tics(PASOS_SORTEO_ATACANTE, 1318.5, 12, 0.55, -5.0)


# Pasos del sorteo del defensor (montaje): los de `escenas.PASOS_DEFENSOR` + el último (D_ULTIMO)
PASOS_SORTEO_DEFENSOR = (0.08, 0.08, 0.09, 0.10, 0.11, 0.13, 0.16, 0.20, 0.26, 0.35)


def tics_sorteo_defensor() -> np.ndarray:
    """08 · Sorteo del defensor: un tic por cada concello vecino resaltado (10). Igual que el 05 pero más
    grave y suave (de La5 a Mi6) para distinguirlo; sigue el ritmo real de la animación. ≈1,3 s."""
    return _secuencia_tics(PASOS_SORTEO_DEFENSOR, 880.0, 7, 0.4, -8.0, semilla_pan=1.3)


def clac_campanilla() -> np.ndarray:
    """06 · Bloqueo (sorteo del atacante y del defensor): «clac» seco de cerradura + campanilla corta.
    ≈0,9 s."""
    dur = 0.9
    t = t_(dur)
    clac = (seno_barrido(t, 200, 80, 0.03) * env_exp(t, 0.05, 0.001)
            + 0.9 * paso_bajo(ruido(len(t), 6), 3000) * env_exp(t, 0.012, 0.0005))
    campana = np.zeros_like(t)
    t_c = np.clip(t - 0.035, 0, None)
    for ratio, amp, tau in ((1.0, 1.0, 0.45), (2.0, 0.55, 0.32), (2.76, 0.4, 0.24), (5.4, 0.16, 0.1)):
        campana += amp * np.sin(2 * np.pi * 1174.7 * ratio * t_c) * env_exp(t_c, tau, 0.001) * (t >= 0.035)
    x = clac * 0.9 + campana * 0.55
    return normalizar(fundidos(estereo(x), 0.0005, 0.04), -4.0)


def whoosh_zoom() -> np.ndarray:
    """07 · Zoom del mapa al atacante (1,3 s de montaje = 1,0 s de vídeo). Whoosh suave en campana:
    ruido filtrado que sube de tono poco a poco; más discreto que el del vuelo de la portada. ≈1,0 s."""
    dur = 1.3 / VELOCIDAD
    t = t_(dur)
    u = t / dur
    corte = 320 * (5.5 ** u)  # 320 Hz → ≈1,8 kHz
    x = filtro_banda_variable(ruido(len(t), 7), corte, q=1.6)
    x *= np.sin(np.pi * u) ** 2.2
    pan = 0.5 + 0.2 * np.sin(2 * np.pi * u * 0.5)
    return normalizar(fundidos(estereo(x * np.sqrt(1 - pan), x * np.sqrt(pan)), 0.01, 0.02), -8.0)


def whoosh_morph() -> np.ndarray:
    """10 · Zoom a los dos bandos (1,1 s de montaje = 0,85 s de vídeo): whoosh suave algo más agudo que el 07
    y, cuando el defensor entra en el panel (a los 0,45 s del montaje), un «pop» más grave y redondo que el
    de la frase. ≈0,85 s."""
    dur = 1.1 / VELOCIDAD
    t = t_(dur)
    u = t / dur
    x = filtro_banda_variable(ruido(len(t), 10), 420 * (5.0 ** u), q=1.6)
    x *= np.sin(np.pi * u) ** 2.2
    x = normalizar(x, -9.0)
    t0 = 0.45 / VELOCIDAD
    a = int(t0 * SR)
    tp = t_(0.22)
    pop = (seno_barrido(tp, 760, 260, 0.03) * env_exp(tp, 0.05, 0.001)
           + 0.3 * paso_bajo(ruido(len(tp), 11), 4000) * env_exp(tp, 0.004, 0.0005))
    pop = normalizar(pop, -6.0)
    izq, der = x.copy(), x.copy()
    izq[a:a + len(pop)] += pop
    der[a:a + len(pop)] += pop
    return normalizar(fundidos(estereo(izq, der), 0.01, 0.02), -5.0)


def _parciales(t: np.ndarray, f0: float, ratios, amps, taus, ataque: float = 0.0008) -> np.ndarray:
    """Suma de parciales (con relaciones inarmónicas dan timbre de metal o cristal), cada uno con su caída."""
    x = np.zeros_like(t)
    for k, (r, a, tau) in enumerate(zip(ratios, amps, taus)):
        x += a * np.sin(2 * np.pi * f0 * r * t + k * 0.7) * env_exp(t, tau, ataque)
    return x


D_ENTRADA_DUELO = 0.55 / VELOCIDAD  # la navaja y la botella tardan esto en llegar al choque (vídeo)


def silbido_navaja() -> np.ndarray:
    """11 · Duelo: entra la navaja por la izquierda (0,42 s, justo hasta el choque). Silbido de metal: ruido
    agudo que sube de tono y de volumen, con un timbre metálico que vibra; va de izquierda al centro."""
    dur = D_ENTRADA_DUELO
    t = t_(dur)
    u = t / dur
    aire = filtro_banda_variable(ruido(len(t), 12), 1500 * (3.7 ** (u ** 1.2)), q=3.0) * (u ** 1.5)
    metal = (np.sin(2 * np.pi * 2400 * t) + 0.7 * np.sin(2 * np.pi * 3700 * t + 1)) * (u ** 2) * (
        0.6 + 0.4 * np.sin(2 * np.pi * 38 * t)) * 0.18
    x = normalizar(aire, -9.0) + metal * 0.5
    pan = 0.5 * u  # de la izquierda (0) al centro (0,5)
    return normalizar(fundidos(estereo(x * np.sqrt(1 - pan), x * np.sqrt(pan)), 0.005, 0.004), -7.0)


def deslizar_botella() -> np.ndarray:
    """12 · Duelo: entra la botella por la derecha (0,42 s). Deslizar de cristal: roce grave-medio que
    gana volumen y un tono de cristal suave que vibra; va de la derecha al centro."""
    dur = D_ENTRADA_DUELO
    t = t_(dur)
    u = t / dur
    roce = filtro_banda_variable(ruido(len(t), 13), 480 * (2.0 ** u), q=1.3) * (u ** 1.1)
    cristal = (np.sin(2 * np.pi * 1250 * t + 3 * np.sin(2 * np.pi * 7 * t) * 0.1)
               + 0.6 * np.sin(2 * np.pi * 1870 * t)) * (u ** 1.8) * 0.2
    x = normalizar(roce, -10.0) + cristal * 0.4
    pan = 1 - 0.5 * u  # de la derecha (1) al centro (0,5)
    return normalizar(fundidos(estereo(x * np.sqrt(1 - pan), x * np.sqrt(pan)), 0.005, 0.004), -8.0)


def choque_navaja_botella() -> np.ndarray:
    """13 · Duelo: choque de la navaja con la botella (el destello). Clang metálico + tintineo de cristal
    que se apaga; empieza exactamente en el choque. ≈1,1 s."""
    dur = 1.1
    t = t_(dur)
    clic = paso_bajo(ruido(len(t), 14), 9000) * env_exp(t, 0.003, 0.0003) * 1.1
    clang = _parciales(t, 880, (1, 2.32, 3.18, 4.6, 6.7), (1, 0.7, 0.5, 0.35, 0.2), (0.35, 0.25, 0.2, 0.15, 0.1)) * 0.5
    cristal_l = _parciales(t, 2637, (1, 1.33, 1.78), (0.5, 0.4, 0.3), (0.3, 0.24, 0.18)) * 0.28
    cristal_r = _parciales(t, 2650, (1, 1.34, 1.77), (0.5, 0.4, 0.3), (0.32, 0.22, 0.2)) * 0.28
    izq, der = clic + clang + cristal_l, clic + clang + cristal_r
    return normalizar(fundidos(estereo(izq, der), 0.0003, 0.08), -2.0)


def golpe_liorta() -> np.ndarray:
    """14 · Duelo: aparece «LIORTA!» (con el choque). Golpe de graves con un temblor que se apaga a la vez
    que el temblor de la imagen (≈0,27 s). ≈0,9 s."""
    dur = 0.9
    t = t_(dur)
    thump = seno_barrido(t, 95, 38, 0.06) * env_exp(t, 0.22, 0.002)
    sub = 0.6 * np.sin(2 * np.pi * 48 * t) * env_exp(t, 0.4, 0.01)
    u = np.clip(t / (0.35 / VELOCIDAD), 0, 1)
    temblor = paso_bajo(ruido(len(t), 15), 220) * (1 - u) * (0.6 + 0.4 * np.sin(5 * np.pi * u)) * 2.2
    x = thump + sub + temblor
    return normalizar(fundidos(estereo(x), 0.001, 0.08), -3.0)


def duelo_preview() -> np.ndarray:
    """Vista previa (no es un efecto del esquema): 11 + 12 + 13 + 14 colocados como en la animación, para
    juzgar cómo suenan juntos."""
    from_ = {}
    for n, fn in ((11, silbido_navaja), (12, deslizar_botella), (13, choque_navaja_botella), (14, golpe_liorta)):
        from_[n] = fn()
    dur = D_ENTRADA_DUELO + 1.1
    mezcla = np.zeros((int(dur * SR), 2))
    for n, inicio in ((11, 0.0), (12, 0.0), (13, D_ENTRADA_DUELO), (14, D_ENTRADA_DUELO)):
        a = int(inicio * SR)
        x = from_[n]
        mezcla[a:a + len(x)] += x[: len(mezcla) - a]
    return normalizar(mezcla, -3.0)


D_RODAR_VIDEO = 0.9 / VELOCIDAD  # lo que dura el rodar de los dados en el vídeo (0,69 s)


def _tok(frecuencia: float, fuerza: float, tau: float = 0.007, semilla: int = 0) -> np.ndarray:
    """Un golpecito de dado (plástico/hueso): tono corto + clic de aire."""
    t = t_(0.08)
    x = (np.sin(2 * np.pi * frecuencia * t) * env_exp(t, tau, 0.0004)
         + 0.5 * np.sin(2 * np.pi * frecuencia * 1.9 * t) * env_exp(t, tau * 0.6, 0.0003)
         + 0.5 * paso_bajo(ruido(len(t), 100 + semilla), 7000) * env_exp(t, 0.0025, 0.0002))
    return x * fuerza


def _poner(destino: np.ndarray, x: np.ndarray, inicio: float, pan: float) -> None:
    a = int(inicio * SR)
    n = min(len(x), len(destino) - a)
    if n <= 0:
        return
    destino[a:a + n, 0] += x[:n] * np.sqrt(1 - pan)
    destino[a:a + n, 1] += x[:n] * np.sqrt(pan)


def traqueteo_dados() -> np.ndarray:
    """15 · Dados: rueda cada pareja de dados (0,9 s de montaje = 0,69 s de vídeo; el dado del atacante a la
    izquierda y el del defensor a la derecha). Traqueteo denso de golpecitos aleatorios que se van espaciando
    y tres botes más graves y espaciados justo antes de pararse. Termina donde empieza el 16."""
    dur = D_RODAR_VIDEO
    mezcla = np.zeros((int(dur * SR) + 1, 2))
    for lado, pan in ((0, 0.3), (1, 0.7)):
        rng = np.random.default_rng(40 + lado)
        n = 15
        tiempos = np.sort(0.62 * dur * rng.random(n) ** 0.8)  # más densos al principio
        for k, ti in enumerate(tiempos):
            f = rng.uniform(1900, 3300)
            _poner(mezcla, _tok(f, 0.35 + 0.35 * rng.random(), semilla=k + 20 * lado), ti, pan)
        for k, (fr, fuerza) in enumerate(((0.70, 0.9), (0.84, 0.7), (0.94, 0.5))):  # botes graves que se apagan
            _poner(mezcla, _tok(1100 - 120 * k, fuerza, tau=0.012, semilla=60 + k + 10 * lado), fr * dur, pan)
    return normalizar(fundidos(mezcla, 0.002, 0.01), -6.0)


def dados_se_paran() -> np.ndarray:
    """16 · Dados: cada dado se para (el del atacante y, 35 ms después, el del defensor). Golpe seco y
    grave de madera sobre la mesa con un pequeño eco de resonancia. ≈0,35 s."""
    dur = 0.35
    mezcla = np.zeros((int(dur * SR), 2))
    for lado, (pan, retraso) in enumerate(((0.35, 0.0), (0.65, 0.035))):
        t = t_(0.3)
        golpe = (seno_barrido(t, 330, 170, 0.035) * env_exp(t, 0.05, 0.0008)
                 + 0.4 * np.sin(2 * np.pi * 920 * t) * env_exp(t, 0.025, 0.0005)
                 + 0.6 * paso_bajo(ruido(len(t), 70 + lado), 4500) * env_exp(t, 0.004, 0.0003))
        _poner(mezcla, golpe * (1.0 if lado == 0 else 0.85), retraso, pan)
    return normalizar(fundidos(mezcla, 0.0003, 0.03), -3.0)


NOTAS_DING = {1: 1046.5, 2: 1174.7, 3: 1318.5, 4: 1568.0, 5: 1760.0}  # Do6, Re6, Mi6, Sol6, La6


def ding_puntos(n: int) -> np.ndarray:
    """17 · Insignia «+N» (N = 1…5): «ding» de campana que sube de nota con N (Do, Re, Mi, Sol, La de la
    sexta octava) y es más rico y fuerte cuanto mayor es N. Suena 0,1 s después de pararse el dado. ≈0,6 s."""
    t = t_(0.6)
    f = NOTAS_DING[n]
    x = _parciales(t, f, (1, 2.0, 3.0, 4.2), (1.0, 0.45, 0.25, 0.12), (0.32, 0.22, 0.14, 0.08))
    if n >= 4:  # los puntos altos llevan un brillo extra una octava arriba
        x += 0.25 * (n - 3) * np.sin(2 * np.pi * f * 4 * t) * env_exp(t, 0.12, 0.001)
    x *= 0.7 + 0.075 * n
    return normalizar(fundidos(estereo(x), 0.0005, 0.05), -6.0 + 0.5 * n)


def dings_preview() -> np.ndarray:
    """Vista previa del 17: los cinco «ding» (+1 a +5) seguidos, uno cada 0,5 s."""
    mezcla = np.zeros((int(3.2 * SR), 2))
    for n in range(1, 6):
        _poner(mezcla, ding_puntos(n).mean(axis=1), 0.5 * (n - 1), 0.5)
    return normalizar(mezcla, -3.0)


def tic_empate() -> np.ndarray:
    """18 · Insignia «=» (tirada empatada): tic apagado y grave, como un golpecito sobre algo blando; casi
    sin brillo para que se note que «no pasa nada». ≈0,15 s."""
    t = t_(0.15)
    x = (np.sin(2 * np.pi * 430 * t) * env_exp(t, 0.03, 0.001)
         + 0.4 * paso_bajo(ruido(len(t), 18), 1200) * env_exp(t, 0.012, 0.0008))
    return normalizar(fundidos(estereo(x), 0.0005, 0.02), -12.0)


def tic_moneda() -> np.ndarray:
    """19 · El marcador suma puntos: «tink» de moneda, agudo y brillante, con una cola metálica corta.
    ≈0,35 s."""
    t = t_(0.35)
    x = (_parciales(t, 2349, (1, 2.4, 3.9), (1.0, 0.55, 0.3), (0.11, 0.07, 0.04))
         + 0.5 * paso_bajo(ruido(len(t), 19), 9000) * env_exp(t, 0.002, 0.0002))
    return normalizar(fundidos(estereo(x), 0.0003, 0.04), -8.0)


T_MULT_ACORDE = 0.5 / VELOCIDAD  # el marcador pasa a decimales a los 0,5 s del multiplicador (montaje)


def multiplicador(n: int) -> np.ndarray:
    """20 · Multiplicador ×1,N (N = 1…5): barrido ascendente (ruido que sube + un tono que trepa) que
    termina en un acorde de campanas brillante justo cuando el marcador cambia a decimales. Cuanto mayor es
    el multiplicador, más fuerte el acorde y más destellos y un golpe grave al final (×1,5 es el máximo).
    ≈1,3 s; el acorde cae a los 0,39 s."""
    k = (n - 1) / 4  # 0 (×1,1) … 1 (×1,5)
    dur = T_MULT_ACORDE + 0.95
    t = t_(dur)
    a = int(T_MULT_ACORDE * SR)
    u = np.clip(t / T_MULT_ACORDE, 0, 1)
    subida = (t < T_MULT_ACORDE)
    aire = filtro_banda_variable(ruido(len(t), 20), 400 * (10.0 ** u), q=2.0) * (u ** 1.5) * subida
    fase = 2 * np.pi * np.cumsum(300 * (4.5 ** u)) / SR
    tono = np.sin(fase) * (u ** 2) * subida * 0.35
    x = normalizar(aire, -12.0) + tono * 0.5
    tc = np.clip(t - T_MULT_ACORDE, 0, None)
    on = (t >= T_MULT_ACORDE)
    acorde = np.zeros_like(t)
    for f in (1046.5, 1318.5, 1568.0, 2093.0):  # Do mayor, brillante
        acorde += _parciales(tc, f, (1, 2.0, 3.0), (1.0, 0.4, 0.2), (0.55, 0.3, 0.18)) * on
    x += acorde * (0.18 + 0.2 * k)
    rng = np.random.default_rng(21)
    for _ in range(int(3 + 9 * k)):  # destellos de campanita aguda
        t0 = T_MULT_ACORDE + 0.03 + 0.5 * rng.random()
        f = rng.choice((3136.0, 3951.0, 4186.0, 5274.0))
        d = np.clip(t - t0, 0, None)
        x += 0.05 * (0.5 + k) * np.sin(2 * np.pi * f * d) * env_exp(d, 0.09, 0.001) * (t >= t0)
    if k >= 0.5:  # golpe grave de poder
        x += (0.25 + 0.5 * (k - 0.5)) * seno_barrido(tc, 110, 50, 0.05) * env_exp(tc, 0.18, 0.002) * on
    return normalizar(fundidos(estereo(x), 0.005, 0.08), -5.0 + 2.0 * (k - 1))


def campanilla_ganador() -> np.ndarray:
    """21 · Recuadro dorado del ganador (aparece con rebote en 0,39 s de vídeo): campanilla de victoria, un
    arpegio rapidísimo Sol-Do-Mi-Sol (sexta octava) con un destello agudo al final. ≈0,8 s."""
    t = t_(0.8)
    x = np.zeros_like(t)
    for k, f in enumerate((784.0, 1046.5, 1318.5, 1568.0)):  # Sol5, Do6, Mi6, Sol6
        d = np.clip(t - 0.045 * k, 0, None)
        x += _parciales(d, f, (1, 2.0, 3.0, 4.2), (1.0, 0.4, 0.2, 0.1), (0.4, 0.25, 0.15, 0.08)) * (t >= 0.045 * k) * (0.8 + 0.1 * k)
    d = np.clip(t - 0.2, 0, None)
    x += 0.15 * np.sin(2 * np.pi * 4186 * d) * env_exp(d, 0.2, 0.001) * (t >= 0.2)
    return normalizar(fundidos(estereo(x), 0.0005, 0.08), -5.0)


def crepitar(n: int, semilla: int, densidad: float, fuerza: np.ndarray) -> np.ndarray:
    """Crepitar de fuego: chasquidos sueltos (muchos y flojos, pocos y fuertes) sobre un rumor grave.
    `densidad`: chasquidos por segundo; `fuerza`: envolvente del volumen (misma longitud que `n`)."""
    rng = np.random.default_rng(semilla)
    x = np.zeros(n)
    for _ in range(int(densidad * n / SR)):
        a = int(rng.random() * (n - 400))
        amp = rng.random() ** 3
        tau = rng.uniform(0.0008, 0.003)
        t = t_(0.012)
        x[a:a + len(t)] += paso_bajo(ruido(len(t), int(rng.integers(1, 10 ** 6))), rng.uniform(2500, 7000)) * env_exp(t, tau, 0.0002) * amp * 2.5
    rumor = paso_bajo(ruido(n, semilla + 1), 380) * (0.5 + 0.5 * np.sin(2 * np.pi * 3.1 * np.arange(n) / SR + 1))
    return (x + 0.9 * rumor) * fuerza


def morte_subita() -> np.ndarray:
    """22 · Morte súbita: aparece la tarjeta en llamas (entra en 0,39 s) y se mantiene durante la ronda. Dos
    bocinazos graves de alarma + un soplido de fuego que prende, y después un crepitar que dura toda la ronda
    y se apaga al final. Esta versión cubre UNA ronda (≈1,9 s); en el montaje se alarga según las rondas."""
    dur = (0.5 + 0.9 + 1.1) / VELOCIDAD
    t = t_(dur)
    entrada = 0.5 / VELOCIDAD
    bocina = np.zeros_like(t)
    for ini, f0 in ((0.0, 150.0), (0.21, 118.0)):  # dos pulsos, el segundo más grave
        d = np.clip(t - ini, 0, 0.2)
        onda = sum(np.sin(2 * np.pi * f0 * h * d) / h for h in (1, 3, 5, 7))  # casi cuadrada: sonido de alarma
        pulso = ((t >= ini) & (t < ini + 0.2)) * np.minimum(1, (t - ini) / 0.01) * np.minimum(1, (ini + 0.2 - t) / 0.03)
        bocina += onda * pulso
    u = np.clip(t / entrada, 0, 1)
    soplido = filtro_banda_variable(ruido(len(t), 22), 200 * (12.0 ** u), q=1.4) * (u ** 1.3) * (t < entrada + 0.1)
    fuerza = np.minimum(1, t / entrada) * np.clip((dur - t) / 0.35, 0, 1)
    crepitar_ = crepitar(len(t), 23, 55, fuerza)
    x = 0.3 * bocina + 0.5 * normalizar(soplido, -8.0) + 0.35 * crepitar_
    return normalizar(fundidos(estereo(x), 0.005, 0.1), -4.0)


def dado_extra() -> np.ndarray:
    """23 · Morte súbita: se tira el dado extra de cada bando (rueda 0,69 s y se para). Traqueteo más grave y
    tenso que el de las tiradas normales y, al pararse, un golpe más pesado (madera + graves). ≈1,1 s."""
    rod = D_RODAR_VIDEO
    dur = rod + 0.4
    mezcla = np.zeros((int(dur * SR), 2))
    for lado, pan in ((0, 0.3), (1, 0.7)):
        rng = np.random.default_rng(80 + lado)
        for k, ti in enumerate(np.sort(0.7 * rod * rng.random(14) ** 0.8)):
            _poner(mezcla, _tok(rng.uniform(1300, 2400), 0.35 + 0.35 * rng.random(), tau=0.009, semilla=k + 30 * lado), ti, pan)
        for k, (fr, fuerza) in enumerate(((0.78, 0.9), (0.9, 0.7))):
            _poner(mezcla, _tok(800 - 100 * k, fuerza, tau=0.014, semilla=90 + k + 10 * lado), fr * rod, pan)
        t = t_(0.4)
        golpe = (seno_barrido(t, 260, 120, 0.04) * env_exp(t, 0.07, 0.001)
                 + 0.8 * seno_barrido(t, 90, 45, 0.06) * env_exp(t, 0.18, 0.002)
                 + 0.5 * paso_bajo(ruido(len(t), 95 + lado), 3500) * env_exp(t, 0.005, 0.0003))
        _poner(mezcla, golpe * 1.1, rod + 0.035 * lado, pan)
    return normalizar(fundidos(mezcla, 0.002, 0.06), -3.0)


def destello_rotulos() -> np.ndarray:
    """24 · Cambian los rótulos ATACA/DEFENDE → CAMPIÓN/MALOGRADO: whoosh brillante que sube rápido y se abre
    en chispas agudas (granos de ruido muy cortos). Empieza justo en el cambio de rótulos. ≈0,8 s."""
    dur = 0.8
    t = t_(dur)
    u = np.clip(t / 0.28, 0, 1)
    barrido = filtro_banda_variable(ruido(len(t), 24), 500 * (14.0 ** u), q=2.0) * np.sin(np.pi * np.clip(t / 0.4, 0, 1)) ** 1.5
    barrido *= (t < 0.4)
    rng = np.random.default_rng(25)
    chispas = np.zeros((len(t), 2))
    for k in range(26):
        ti = 0.12 + 0.5 * rng.random() ** 1.3
        f = rng.uniform(3200, 7800)
        d = t_(0.05)
        g = np.sin(2 * np.pi * f * d) * env_exp(d, rng.uniform(0.006, 0.016), 0.0004) * (0.25 + 0.5 * rng.random()) * (1 - ti)
        _poner(chispas, g, ti, rng.random())
    x = estereo(0.9 * normalizar(barrido, -8.0)) + 0.5 * chispas
    return normalizar(fundidos(x, 0.002, 0.08), -5.0)


# Cancioncilla de gaita: Re mixolidio, ritmo de muiñeira (compás 6/8, corcheas). (nota MIDI, corcheas)
GAITA_MELODIA = ((74, 2), (72, 1), (71, 2), (69, 1),
                 (67, 1), (69, 1), (71, 1), (69, 2), (66, 1),
                 (67, 1), (66, 1), (64, 1), (62, 3))
D_CORCHEA_GAITA = 0.145  # segundos de vídeo


def _midi(n: float) -> float:
    return 440.0 * 2 ** ((n - 69) / 12)


def _caramillo(t: np.ndarray, f: float) -> np.ndarray:
    """Timbre de lengüeta (gaita): armónicos impares y pares con caída lenta, algo nasal (resonancias ≈1,2 y 2,6 kHz)."""
    x = sum(np.sin(2 * np.pi * f * h * t + 0.3 * h) / h ** 0.8 for h in range(1, 18) if f * h < 9000)
    return x


def gaita_cancion() -> np.ndarray:
    """25 · Entra la gaita: cancioncilla original de ≈2,6 s (muiñeira en Re mixolidio) sobre un bordón de Re+La.
    Timbre sintetizado de lengüeta; si el usuario aporta muestras de gaita real, se sustituye (docs/FUENTES.md)."""
    n_total = sum(d for _, d in GAITA_MELODIA)
    dur = n_total * D_CORCHEA_GAITA + 0.45
    t = t_(dur)
    melodia = np.zeros_like(t)
    ini = 0.0
    previa = None
    for nota, d in GAITA_MELODIA:
        a = int(ini * SR)
        largo = d * D_CORCHEA_GAITA
        b = int(min(len(t), (ini + largo) * SR))
        seg = t[: b - a]
        env = np.minimum(1, seg / 0.012) * np.minimum(1, np.maximum(0, (largo - seg) / 0.02 + 0.0))
        env = np.where(seg > largo - 0.018, np.clip((largo - seg) / 0.018, 0, 1), env)
        melodia[a:b] += _caramillo(seg, _midi(nota)) * env
        if previa == nota:  # notas repetidas: se separan con un gorgorito (nota de adorno muy corta)
            g = int(0.03 * SR)
            melodia[a:a + g] *= 0.0
            melodia[a:a + g] += _caramillo(t[:g], _midi(nota + 2)) * 0.8
        previa = nota
        ini += largo
    cola = np.clip((dur - t) / 0.4, 0, 1)
    melodia *= cola
    bordon = (_caramillo(t, _midi(38)) + 0.7 * _caramillo(t, _midi(45))) * np.minimum(1, t / 0.05) * cola
    bordon = paso_bajo(bordon, 900)
    mel = filtro_banda_variable(melodia, np.full(len(t), 1500.0), q=0.7) * 0.6 + 0.5 * melodia * 0.4
    x = 0.7 * normalizar(mel, -6.0) + 0.45 * normalizar(bordon, -6.0)
    return normalizar(fundidos(estereo(x), 0.004, 0.1), -5.0)


def confeti() -> np.ndarray:
    """26 · Confeti (se usa en las 2 tandas): «pop» de cañón con un chorro de papelillos (chasquidos ligeros y
    agudos que se espacian al caer). ≈1,1 s."""
    dur = 1.1
    t = t_(dur)
    pop = seno_barrido(t, 320, 90, 0.03) * env_exp(t, 0.035, 0.0005) + 0.8 * paso_bajo(ruido(len(t), 26), 4500) * env_exp(t, 0.012, 0.0004)
    mezcla = np.zeros((len(t), 2))
    _poner(mezcla, pop * 0.9, 0.0, 0.5)
    rng = np.random.default_rng(27)
    for k in range(70):
        ti = 0.02 + 0.95 * rng.random() ** 1.8  # muchos al principio, cada vez menos
        d = t_(0.03)
        g = paso_bajo(ruido(len(d), int(rng.integers(1, 10 ** 6))), rng.uniform(3500, 9000)) * env_exp(d, rng.uniform(0.002, 0.007), 0.0003)
        _poner(mezcla, g * (0.15 + 0.5 * rng.random()) * (1.1 - ti), ti, rng.random())
    return normalizar(fundidos(mezcla, 0.0005, 0.1), -5.0)


def cha_ching() -> np.ndarray:
    """27 · Pastillas «+N vacas» y «+K concellos»: «cha-ching» de caja registradora, dos golpes metálicos
    rápidos (el segundo más agudo) con un brillo final. Suena una vez por pastilla. ≈0,55 s."""
    t = t_(0.55)
    x = np.zeros_like(t)
    for ini, f, amp in ((0.0, 1568.0, 0.8), (0.09, 2093.0, 1.0)):
        d = np.clip(t - ini, 0, None)
        x += amp * _parciales(d, f, (1, 2.76, 5.4, 8.9), (1.0, 0.6, 0.35, 0.2), (0.3, 0.2, 0.1, 0.05)) * (t >= ini)
        x += 0.5 * amp * paso_bajo(ruido(len(t), 27 + int(f)), 8000) * env_exp(d, 0.006, 0.0004) * (t >= ini)
    return normalizar(fundidos(estereo(x), 0.0005, 0.08), -6.0)


def pop_extension(i: int = 0, n: int = 24) -> np.ndarray:
    """28 · Un «pop» suave de la extensión del color (paso i de n): burbuja corta que sube de tono con i
    (de Do5 a Do7 en semitonos continuos) y algo de volumen. ≈0,12 s."""
    t = t_(0.12)
    f = 523.0 * 2 ** (2.0 * i / max(1, n - 1))
    x = seno_barrido(t, f * 0.8, f, 0.02) * env_exp(t, 0.03, 0.001)
    x += 0.25 * np.sin(2 * np.pi * 2 * f * t) * env_exp(t, 0.012, 0.001)
    return normalizar(fundidos(estereo(x), 0.0005, 0.02), -14.0 + 4.0 * i / max(1, n - 1))


def extension_preview() -> np.ndarray:
    """28 (vista previa) · 24 pops repartidos en los 1,8 s de montaje de la extensión (≈1,4 s de vídeo), para oír
    cómo sube la escala. En el montaje se usan tantos pops como pasos tenga la conquista (hasta 24)."""
    dur = 1.8 / VELOCIDAD
    mezcla = np.zeros((int((dur + 0.2) * SR), 2))
    for i in range(24):
        u = i / 23
        _poner(mezcla, pop_extension(i, 24).mean(axis=1), u * dur, 0.5)
    return normalizar(mezcla, -6.0)


def whoosh_alejar() -> np.ndarray:
    """29 · Alejamiento del mapa (ataque suelto, 2,2 s de montaje ≈1,7 s de vídeo): whoosh descendente, ruido que
    pierde brillo poco a poco, con un grave suave al final (el mapa «se asienta»)."""
    dur = 2.2 / VELOCIDAD
    t = t_(dur)
    u = t / dur
    corte = 2200 * (0.12 ** u)
    x = filtro_banda_variable(ruido(len(t), 29), corte, q=1.3) * np.sin(np.pi * np.minimum(1, u * 1.15)) ** 1.8
    x = normalizar(x, -9.0)
    g = seno_barrido(t, 110, 55, 0.5) * env_exp(np.clip(t - dur * 0.55, 0, None), 0.35, 0.05) * (t > dur * 0.55)
    return normalizar(fundidos(estereo(x + 0.35 * g), 0.02, 0.15), -7.0)


EFECTOS = {
    1: ("01_portada_golpe", golpe_portada),
    2: ("02_portada_frase_pop", pop_frase),
    3: ("03_portada_vuelo_whoosh", whoosh_vuelo),
    5: ("05_sorteo_atacante_tics", tics_sorteo_atacante),
    6: ("06_sorteo_bloqueo_clac", clac_campanilla),
    7: ("07_zoom_atacante_whoosh", whoosh_zoom),
    8: ("08_sorteo_defensor_tics", tics_sorteo_defensor),
    10: ("10_zoom_bandos_whoosh_pop", whoosh_morph),
    11: ("11_duelo_navaja_silbido", silbido_navaja),
    12: ("12_duelo_botella_deslizar", deslizar_botella),
    13: ("13_duelo_choque", choque_navaja_botella),
    14: ("14_duelo_liorta_graves", golpe_liorta),
    15: ("15_dados_traqueteo", traqueteo_dados),
    16: ("16_dados_se_paran", dados_se_paran),
    171: ("17_ding_mas1", lambda: ding_puntos(1)),
    172: ("17_ding_mas2", lambda: ding_puntos(2)),
    173: ("17_ding_mas3", lambda: ding_puntos(3)),
    174: ("17_ding_mas4", lambda: ding_puntos(4)),
    175: ("17_ding_mas5", lambda: ding_puntos(5)),
    18: ("18_empate_tic", tic_empate),
    21: ("21_ganador_campanilla", campanilla_ganador),
    22: ("22_morte_subita_tarjeta", morte_subita),
    23: ("23_morte_subita_dado_extra", dado_extra),
    24: ("24_rotulos_destello", destello_rotulos),
    25: ("25_gaita_cancion", gaita_cancion),
    26: ("26_confeti", confeti),
    27: ("27_pastilla_cha_ching", cha_ching),
    28: ("28_extension_pop", pop_extension),
    128: ("28_extension_preview", extension_preview),
    29: ("29_alejamiento_whoosh", whoosh_alejar),
    19: ("19_marcador_moneda", tic_moneda),
    201: ("20_multiplicador_x1_1", lambda: multiplicador(1)),
    202: ("20_multiplicador_x1_2", lambda: multiplicador(2)),
    203: ("20_multiplicador_x1_3", lambda: multiplicador(3)),
    204: ("20_multiplicador_x1_4", lambda: multiplicador(4)),
    205: ("20_multiplicador_x1_5", lambda: multiplicador(5)),
    111: ("preview_11-14_duelo", duelo_preview),  # vista previa conjunta, no es un efecto del esquema
    117: ("preview_17_dings_1-5", dings_preview),  # los cinco dings seguidos, solo para escuchar
}


def generar(numeros: list[int] | None = None, carpeta: Path = CARPETA) -> list[Path]:
    rutas = []
    for n in numeros or sorted(EFECTOS):
        nombre, fn = EFECTOS[n]
        audio = fn()
        ruta = guardar(carpeta / f"{nombre}.wav", audio)
        print(nombre, medidas(audio))
        rutas.append(ruta)
    return rutas


if __name__ == "__main__":
    generar([int(a) for a in sys.argv[1:]] or None)
