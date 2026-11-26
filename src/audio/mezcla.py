"""Mezcla del audio del vídeo (paso 5.2): coloca cada efecto del esquema (`docs/SONIDOS.md`) en su instante
según `src/render/linea_tiempo.py`, normaliza el volumen (≈ −14 LUFS) y une el audio al vídeo.

Los efectos ya están sintetizados a duración de vídeo (montaje ÷ 1,296), así que solo se desplazan.
Uso:
    python -m src.audio.mezcla ataque        # ataque corto del episodio 1 → output/muestras/ataque_episodio1_con_audio.mp4
    python -m src.audio.mezcla episodio100   # episodio 100 de muestra
"""

from __future__ import annotations

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

from src.audio import sintesis as S
from src.render import estilo as E
from src.render.escenas import VELOCIDAD, Montaje
from src.render.linea_tiempo import Evento, eventos

LUFS_OBJETIVO = -14.0
PICO_VERDADERO = -1.5


def _cargar(clave: int) -> np.ndarray:
    """Efecto aprobado (WAV de `assets/audio`); si no existe todavía, se sintetiza."""
    nombre, fn = S.EFECTOS[clave]
    ruta = S.CARPETA / f"{nombre}.wav"
    if not ruta.exists():
        S.guardar(ruta, fn())
    with wave.open(str(ruta), "rb") as w:
        datos = np.frombuffer(w.readframes(w.getnframes()), dtype="<i2").astype(np.float64) / 32767
        return datos.reshape(-1, w.getnchannels())


def efecto(ev: Evento) -> np.ndarray:
    """Audio estéreo de un evento (con los parámetros del esquema)."""
    n = ev.num
    if n == "05":  # tics con los pasos reales de la animación
        return S._secuencia_tics(tuple(ev.params), 1318.5, 12, 0.55, -5.0)
    if n == "08":
        return S._secuencia_tics(tuple(ev.params), 880.0, 7, 0.4, -8.0, semilla_pan=1.3)
    if n == "17":
        return _cargar(170 + ev.params[0])
    if n == "20":
        return _cargar(200 + ev.params[0])
    if n == "22":
        return _cargar(22) if ev.params[0] == 1 else S.morte_subita(ev.params[0])
    if n == "28":
        return S.pop_extension(*ev.params)
    if n == "32":
        return _cargar(321 if ev.params[0] else 32)
    if n == "06":
        return _cargar(6)
    return _cargar(int(n))


def mezclar(m: Montaje, velocidad: float = VELOCIDAD) -> np.ndarray:
    """Pista estéreo (44,1 kHz) de todo el vídeo, sin normalizar."""
    n = int(np.ceil(m.duracion / velocidad * S.SR)) + S.SR
    pista = np.zeros((n, 2))
    for ev in eventos(m):
        x = efecto(ev) * ev.ganancia
        a = int(round(ev.t / velocidad * S.SR))
        pista[a:a + len(x)] += x[: n - a]
    return pista[: int(np.ceil(m.duracion / velocidad * S.SR))]


def _ffmpeg(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["ffmpeg", "-hide_banner", "-y", *args], capture_output=True, text=True, check=True)


def normalizar_lufs(wav_in: Path, wav_out: Path) -> dict:
    """Normaliza a −14 LUFS (loudnorm en dos pasadas, lineal) con tope de pico verdadero de −1,5 dB."""
    base = f"loudnorm=I={LUFS_OBJETIVO}:TP={PICO_VERDADERO}:LRA=11"
    r = _ffmpeg("-i", str(wav_in), "-af", base + ":print_format=json", "-f", "null", "-")
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    med = (f":measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
           f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    # limitador final: loudnorm lineal no siempre respeta el pico (el ep. 9 salió a +2,2 dBTP)
    limite = 10 ** ((PICO_VERDADERO - 0.5) / 20)
    _ffmpeg("-i", str(wav_in), "-af", base + med + f",alimiter=limit={limite:.4f}:level=false", "-ar", str(S.SR), "-c:a", "pcm_s16le", str(wav_out))
    return {"entrada_LUFS": float(js["input_i"]), "pico_entrada_dBTP": float(js["input_tp"])}


def unir(video: Path, wav: Path, salida: Path) -> Path:
    """Copia el vídeo tal cual y le añade el audio (AAC 192 kb/s)."""
    _ffmpeg("-i", str(video), "-i", str(wav), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-t", f"{duracion_video(video):.3f}", "-movflags", "+faststart", str(salida))
    return salida


def duracion_video(ruta: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(ruta)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def medir_lufs(ruta: Path) -> dict:
    r = _ffmpeg("-i", str(ruta), "-af", "loudnorm=print_format=json", "-f", "null", "-")
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    return {"LUFS": float(js["input_i"]), "pico_dBTP": float(js["input_tp"])}


def poner_audio(m: Montaje, video: Path, salida: Path) -> Path:
    """Mezcla el audio del montaje, lo normaliza y lo une al `video` (ya renderizado, sin sonido)."""
    pista = mezclar(m)
    sin_normalizar, normal = salida.with_suffix(".mezcla.wav"), salida.with_suffix(".wav")
    S.guardar(sin_normalizar, pista / max(1.0, float(np.max(np.abs(pista)))))
    normalizar_lufs(sin_normalizar, normal)
    sin_normalizar.unlink()
    return unir(video, normal, salida)


def _montaje(que: str) -> tuple[Montaje, Path]:
    from src.render.mapa import MapaGalicia
    carpeta = E.RAIZ / "output" / "muestras"
    mapa = MapaGalicia()
    if que == "ataque":
        from src.render.ataque_episodio1 import elegir_semilla
        from src.render.escenas import construir_ataque
        from src.render.mapa_episodio1 import estado_episodio1
        estado = estado_episodio1(mapa)
        ordes = next(i for i, c in estado["concellos"].items() if c["nome"] == "Ordes")
        return construir_ataque(estado, elegir_semilla(estado, ordes), mapa), carpeta / "ataque_episodio1.mp4"
    if que == "episodio100":
        from src.render import episodio100 as E100
        from src.render.escenas import construir_episodio, estado_de_muestra
        estado = estado_de_muestra(E100.SEMILLA, previas=(E100.EPISODIO - 1) * E100.BATALLAS_POR_EPISODIO,
                                   episodio=E100.EPISODIO - 1)
        return construir_episodio(estado, E100.SEMILLA, mapa), carpeta / "episodio100_sin_audio.mp4"
    raise SystemExit("Uso: python -m src.audio.mezcla ataque|episodio100")


if __name__ == "__main__":
    m, video = _montaje(sys.argv[1] if len(sys.argv) > 1 else "ataque")
    esperado = m.duracion / VELOCIDAD
    print(f"Montaje {m.duracion:.1f} s → vídeo esperado {esperado:.1f} s; archivo {duracion_video(video):.1f} s", flush=True)
    salida = video.with_name(video.stem.replace("_sin_audio", "") + "_con_audio.mp4")
    print(poner_audio(m, video, salida))
    print(medir_lufs(salida))
