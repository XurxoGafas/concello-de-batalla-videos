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


def tics_sorteo_atacante() -> np.ndarray:
    """05 · Sorteo del atacante: un tic cada vez que se resalta otro dueño (15 en total, con los pasos
    reales de la animación: empiezan rápidos y se frenan). Cada tic es más agudo y más fuerte que el
    anterior (de Mi5 a Mi6 por semitonos); el último, el del elegido, es el más brillante. ≈1,8 s."""
    pasos = [p / VELOCIDAD for p in PASOS_SORTEO_ATACANTE]
    n = len(pasos)
    dur = sum(pasos) + 0.1
    izq, der = np.zeros(int(dur * SR)), np.zeros(int(dur * SR))
    inicio = 0.0
    for i, paso in enumerate(pasos):
        frecuencia = 1318.5 * 2 ** ((12 * i / (n - 1)) / 12)
        tic = _tic(frecuencia, 0.55 + 0.45 * i / (n - 1))
        a = int(inicio * SR)
        reparto = 0.5 + 0.18 * np.sin(i * 2.1)  # los tics bailan un poco entre izquierda y derecha
        izq[a:a + len(tic)] += tic * np.sqrt(1 - reparto)
        der[a:a + len(tic)] += tic * np.sqrt(reparto)
        inicio += paso
    return normalizar(estereo(izq, der), -5.0)


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


EFECTOS = {
    1: ("01_portada_golpe", golpe_portada),
    2: ("02_portada_frase_pop", pop_frase),
    3: ("03_portada_vuelo_whoosh", whoosh_vuelo),
    5: ("05_sorteo_atacante_tics", tics_sorteo_atacante),
    6: ("06_sorteo_bloqueo_clac", clac_campanilla),
    7: ("07_zoom_atacante_whoosh", whoosh_zoom),
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
