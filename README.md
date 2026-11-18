# Concello de Batalla

Generador automático de vídeos verticales (9:16) en los que los concellos de Galicia se invaden entre sí a golpe de dados, multiplicados según el número de vacas de cada bando. Cada vídeo encadena 3 batallas y se publica a diario en YouTube Shorts, Instagram Reels y TikTok. El plan completo está en `PLAN.md`, las reglas del juego en `docs/DECISIONES.md`, y el historial de avance en `PROGRESO.md`.

## Estado del proyecto

En desarrollo. Ver `PLAN.md` para el detalle fase a fase y `PROGRESO.md` para el historial de cada paso completado.

## Instalación (en progreso)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/check_env.py
```

`check_env.py` comprueba que Python, ffmpeg y las librerías clave (geopandas, shapely, Pillow, etc.) están disponibles.
