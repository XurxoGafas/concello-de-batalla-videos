# FUENTES — Datos y recursos externos

Cada recurso externo se registra aquí con su fuente, fecha y licencia **antes de usarlo** (regla j de `CLAUDE.md`).

## Límites de los concellos de Galicia (paso 2.1)

- **Fuente:** Instituto Geográfico Nacional (IGN), «Unidades administrativas» (Divisiones Administrativas de España), servicio OGC API-Features: `https://api-features.ign.es/collections/administrativeunit`
- **Filtro aplicado:** `codnut2=ES11` (Galicia) y `nationallevelname=Municipio`.
- **Fecha de descarga:** 2026-11-18.
- **Resultado:** 313 concellos (A Coruña 93, Lugo 67, Ourense 92, Pontevedra 61), geometría `MultiPolygon`, sistema de coordenadas EPSG:4326. Todos con id (`nationalcode`) y nombre únicos, geometrías válidas.
- **Licencia:** CC BY 4.0 (metadatos del servicio: «CC-BY 4.0 ign.es»). Exige citar el origen. Fórmula de cita provisional: «CC-BY 4.0 ign.es». ⚠️ **Pendiente de confirmar antes de publicar el primer vídeo:** la fórmula exacta de cita que exige el IGN para productos derivados (el mapa dibujado es un derivado), para ponerla en la descripción de los vídeos.
- **Cómo reproducirlo:** `python scripts/descargar_concellos.py` → `data/raw/concellos.geojson` (carpeta ignorada por git; se regenera con el script).
- **Notas:**
  - El nombre de la fusión Cerdedo + Cotobade (Decreto 134/2016) figura en el IGN como «Cerdedo Cotobade» (sin guion). Revisar cómo se muestra en los vídeos.
  - Los nombres del IGN no llevan formas bilingües con «/».
  - Fuente alternativa descartada: servicio «Límites administrativos de Galicia» de la Xunta (IET). Se actualiza con los límites del IGN de 02/2026, pero su licencia no está clara (una ficha de datos.gob.es indica CC BY-SA 4.0, mientras que las condiciones del IET hablan de licencia «compatible con CC-BY 4.0»). La cláusula «compartir igual» podría obligar a publicar los datos derivados con esa misma licencia, y el repositorio es público; por eso se prefirió el IGN, con licencia inequívoca.
