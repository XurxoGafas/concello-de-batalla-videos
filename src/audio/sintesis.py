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
    111: ("preview_11-14_duelo", duelo_preview),  # vista previa conjunta, no es un efecto del esquema
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
