"""Comprueba que el entorno tiene todo lo necesario para el proyecto.

Uso:
    python scripts/check_env.py

Imprime la versión de Python, de ffmpeg y de cada librería clave.
Si falta algo, lo indica y termina con código de salida 1.
"""

import importlib
import shutil
import subprocess
import sys

LIBRERIAS = [
    "geopandas",
    "shapely",
    "pyproj",
    "PIL",  # Pillow
    "cairo",  # pycairo
    "numpy",
    "pandas",
    "yaml",  # PyYAML
    "pytest",
]


def version_de(modulo: str) -> str:
    mod = importlib.import_module(modulo)
    for atributo in ("__version__", "version"):
        v = getattr(mod, atributo, None)
        if v:
            return str(v)
    return "versión desconocida"


def comprobar_ffmpeg() -> tuple[bool, str]:
    ruta = shutil.which("ffmpeg")
    if not ruta:
        return False, "ffmpeg no está instalado o no está en el PATH"
    resultado = subprocess.run(
        ["ffmpeg", "-version"], capture_output=True, text=True, check=False
    )
    primera_linea = resultado.stdout.splitlines()[0] if resultado.stdout else "?"
    return True, primera_linea


def main() -> int:
    print(f"Python: {sys.version.split()[0]}")

    ok_ffmpeg, info_ffmpeg = comprobar_ffmpeg()
    print(f"ffmpeg: {'OK' if ok_ffmpeg else 'FALTA'} — {info_ffmpeg}")

    faltan = []
    if not ok_ffmpeg:
        faltan.append("ffmpeg")

    for modulo in LIBRERIAS:
        try:
            v = version_de(modulo)
            print(f"{modulo}: OK ({v})")
        except ImportError:
            print(f"{modulo}: FALTA")
            faltan.append(modulo)

    print()
    if faltan:
        print(f"Entorno INCOMPLETO. Falta instalar: {', '.join(faltan)}")
        return 1

    print("Entorno correcto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
