"""Serie de episodios (partida real): genera el siguiente episodio, lo guarda y avanza la partida.

Por cada episodio se guarda, en el repositorio (`data/partida/`):
  · `estado_actual.json`            estado de la partida tras el episodio (de aquí sale el siguiente)
  · `historial.jsonl`               las batallas (con su semilla, para repetirlas)
  · `portadas.jsonl`                frase de portada usada (para no repetirla en ~10 episodios)
  · `episodios/estado_NNN.json`     estado de la partida tras el episodio NNN (permite volver a dibujarlo)
  · `docs/EPISODIOS.md`             resumen legible: batallas, vacas, clasificaciones
El vídeo va a `output/episodios/` (no se sube a git).

Uso:
    python -m src.render.serie                       # siguiente episodio (semilla en SEMILLA_SERIE, de .env)
    python -m src.render.serie 2                     # 2 episodios seguidos
    python -m src.render.serie --registrar --semilla ep1-0   # solo registra el siguiente episodio (el vídeo ya existe)
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import time
from pathlib import Path

from src.audio.mezcla import medir_lufs, poner_audio
from src.motor import momentos
from src.motor.persistencia import (RUTA_ESTADO, RUTA_HISTORIAL, VARIABLE_SEMILLA, anadir_al_historial, cargar_estado,
                                    guardar_estado, jugar_episodio, nueva_partida)
from src.render import estilo as E
from src.render import ranking as R
from src.render.escenas import Montaje, construir_episodio, renderizar
from src.render.mapa import MapaGalicia

CARPETA_VIDEOS = E.RAIZ / "output" / "episodios"
CARPETA_ESTADOS = RUTA_ESTADO.parent / "episodios"
RUTA_RESUMEN = E.RAIZ / "docs" / "EPISODIOS.md"


def cargar_env(ruta: Path = E.RAIZ / ".env") -> None:
    """Lee `.env` (CLAVE=valor) sin pisar las variables que ya estén definidas."""
    if ruta.exists():
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            if "=" in linea and not linea.lstrip().startswith("#"):
                k, v = linea.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def resumen_md(estado_antes: dict, estado: dict, registros: list[dict], portada: momentos.Portada) -> str:
    """Texto de `docs/EPISODIOS.md` para un episodio: batallas, vacas, portada y clasificaciones."""
    n = estado["episodio"]
    nombre = lambda i: estado_antes["donos"][i]["nome"]  # los dueños conquistados ya no están en `estado`
    lineas = [f"\n## Episodio {n}\n", f"Portada: «{portada.texto.replace(momentos.MARCA_A, '').replace(momentos.MARCA_B, '')}» "
              f"(frase {portada.frase_id}, protagonista {portada.nombre}).\n"]
    for r in registros:
        res = r["resultado"]
        lineas.append(f"- Batalla {r['batalla']}: **{nombre(r['atacante'])}** ({r['vacas_atacante']} 🐄) ataca a "
                      f"**{nombre(r['defensor'])}** ({r['vacas_defensor']} 🐄) → gana **{nombre(r['ganador'])}**; "
                      f"semilla `{r['semilla']}`.")
    vit, vac = R.clasificaciones(estado)
    lineas.append("\nClasificación tras el episodio:\n")
    lineas.append("- Vitorias: " + ", ".join(f"{nombre(i)} ({v})" for i, v in vit))
    lineas.append("- Vacas: " + ", ".join(f"{nombre(i)} ({v})" for i, v in vac))
    lineas.append(f"- Dueños que quedan: {len(estado['donos'])}.")
    return "\n".join(lineas) + "\n"


def registrar(estado: dict, semilla: str, montaje: Montaje, *, ruta_estado: Path = RUTA_ESTADO,
              ruta_historial: Path = RUTA_HISTORIAL, carpeta_estados: Path = CARPETA_ESTADOS,
              ruta_resumen: Path = RUTA_RESUMEN, ruta_portadas: Path = momentos.HISTORIAL) -> dict:
    """Guarda el resultado del episodio (estado, historial, frase de portada, copia numerada y resumen).
    Devuelve el estado nuevo. Se llama solo cuando el vídeo ya está hecho."""
    final, registros = jugar_episodio(estado, semilla)
    if final != montaje.estado_final:
        raise RuntimeError("El montaje no corresponde a este estado y semilla: no se guarda nada")
    portada = montaje.escenas[0].portada
    texto = resumen_md(estado, final, registros, portada)  # antes de escribir nada: si falla, no se guarda un episodio a medias
    anadir_al_historial(registros, ruta_historial)
    momentos.anadir_al_historial(final["episodio"], portada, ruta_portadas)
    guardar_estado(final, ruta_estado)
    guardar_estado(final, carpeta_estados / f"estado_{final['episodio']:03d}.json")
    ruta_resumen.parent.mkdir(parents=True, exist_ok=True)
    cabecera = ("# Episodios de la serie\n\nResumen de cada episodio publicado (se añade solo; el detalle de cada batalla "
                "está en `data/partida/historial.jsonl`).\n")
    previo = ruta_resumen.read_text(encoding="utf-8") if ruta_resumen.exists() else cabecera
    ruta_resumen.write_text(previo + texto, encoding="utf-8")
    return final


def generar_siguiente(semilla: str, solo_registrar: bool = False, mapa: MapaGalicia | None = None) -> dict:
    """Genera (vídeo con sonido) y registra el siguiente episodio de la partida."""
    t0 = time.time()
    mapa = mapa or MapaGalicia()
    estado = cargar_estado(RUTA_ESTADO) if RUTA_ESTADO.exists() else nueva_partida()
    n = estado["episodio"] + 1
    m = construir_episodio(estado, semilla, mapa, recientes=momentos.leer_recientes())
    print(f"Episodio {n}: montaje {m.duracion:.1f} s, {len(m.escenas)} escenas ({time.time() - t0:.0f} s)", flush=True)
    if not solo_registrar:
        CARPETA_VIDEOS.mkdir(parents=True, exist_ok=True)
        base = CARPETA_VIDEOS / f"episodio_{n:03d}"
        m.escenas[0].fotograma(0.0).save(base.with_name(base.name + "_portada.png"))
        sin = renderizar(m, base.with_name(base.name + "_sin_audio.mp4"), progreso=True)
        con = poner_audio(m, sin, base.with_suffix(".mp4"))
        sin.unlink()
        print(con, medir_lufs(con), f"({time.time() - t0:.0f} s)", flush=True)
    final = registrar(estado, semilla, m)
    print(f"Episodio {n} guardado en data/partida/ y docs/EPISODIOS.md", flush=True)
    return final


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cuantos", nargs="?", type=int, default=1, help="episodios seguidos a generar")
    ap.add_argument("--semilla", help=f"semilla de la serie (si no, la variable {VARIABLE_SEMILLA} o .env)")
    ap.add_argument("--registrar", action="store_true", help="solo registrar el episodio, sin renderizar el vídeo")
    a = ap.parse_args()
    cargar_env()
    semilla = a.semilla or os.environ.get(VARIABLE_SEMILLA, "").strip()
    if not semilla:
        raise SystemExit(f"Falta la semilla de la serie ({VARIABLE_SEMILLA} en .env o --semilla)")
    mapa = MapaGalicia()
    for _ in range(a.cuantos):
        generar_siguiente(semilla, a.registrar, mapa)


if __name__ == "__main__":
    main()
