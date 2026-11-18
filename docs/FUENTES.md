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

## Censo de vacas por concello (paso 2.3)

- **Fuente:** Instituto Galego de Estatística (IGE), tabla 62 «Efectivos e explotacións de gando bovino. Información ata o nivel de desagregación municipal» (origen de los datos: IGE-CMR, registro de ganado bovino de la Consellería do Medio Rural), vía la API de datos del IGE: `https://www.ige.gal/igebdt/igeapi/json/datos/62/`
- **Variable usada:** «Número de vacas» (vacas de muxidura + vacas de non muxidura). No se cuentan los «outros bovinos» (terneros, novillas, etc.). Año: **2025**, el último disponible en la tabla.
- **Fecha de descarga:** 2026-11-18.
- **Resultado:** dato para los 313 concellos; total 511.138 vacas, igual al total publicado por el IGE para Galicia. 7 concellos tienen oficialmente 0 vacas (A Arnoia, Barbadás, Larouco, Ribadavia, Rubiá, Toén y A Illa de Arousa) y se tratan como 1 vaca (decisión del usuario), de modo que el total usado en el juego es 511.145. Los códigos de concello del IGE (INE, 5 dígitos) coinciden con los 5 últimos dígitos de los ids del IGN. Las 4 filas sin dato de la tabla corresponden a concellos que ya no existen (Cesuras y Oza dos Ríos, hoy Oza-Cesuras, y Cerdedo y Cotobade, hoy Cerdedo Cotobade): no hay ningún concello vigente sin dato.
- **Cómo reproducirlo:** `python scripts/descargar_vacas.py` → `data/raw/vacas_ige_tabla62.json` (ignorado por git) y `python -m src.datos.vacas` → `data/processed/vacas.json`.
- **Condiciones de uso (API del IGE):** los servicios que usan la API **deben mostrar el aviso**: «Este produto emprega a API de datos do Instituto Galego de Estatística (IGE), pero non está certificado ou aprobado polo IGE», y al presentar los datos no se pueden modificar ni editar los datos, metadatos ni enlaces. El IGE puede limitar peticiones repetidas desde un mismo origen (solo se descarga una vez; no se consulta en cada ejecución del vídeo).
- **Condiciones generales de reutilización (Xunta):** citar la fuente y no desnaturalizar el sentido de la información.
- ⚠️ **Pendiente de confirmar antes de publicar el primer vídeo:** (1) dónde poner el aviso obligatorio del IGE y la cita (descripción de los vídeos y/o pantalla final); (2) que el uso en un canal monetizable encaja con las condiciones del IGE (no se ha localizado el aviso legal propio del IGE; solo las condiciones de la API y el aviso general de la Xunta). Conviene también tener presente que las vacas se acumulan durante la partida (suma de territorios), es un uso derivado del dato original, y que el ajuste 0 → 1 es una regla del juego, no un dato oficial.

## Banderas de los concellos (paso 2.4, en curso)

- **Fuente de la lista:** Wikidata (propiedad P41, «imagen de la bandera»; datos CC0), consulta del 2026-11-18: 317 municipios gallegos (incluye 4 desaparecidos), **142 con imagen de bandera** (110 SVG, 22 PNG, 9 JPG, 1 GIF). Faltan, por tanto, unos 171 concellos sin imagen en Wikidata.
- **Imágenes:** alojadas en Wikimedia Commons. Solo se usan para extraer sus colores (paleta); no se redistribuyen ni se muestran. Pendiente comprobar la licencia de cada imagen si más adelante se quisieran mostrar las banderas en los vídeos. Las banderas municipales son símbolos oficiales aprobados por la Xunta por decreto (DOG).
- **Estado:** la descarga de las imágenes está **bloqueada** por el límite de peticiones de Wikimedia desde esta red (error 429 con espera de 600 s, que no se levanta tras esperar). Se registra en `PROGRESO.md`.

## Tipografía (paso 4.1)

- **Lilita One** (Juan Montoreano). Licencia **SIL Open Font License 1.1** (uso libre, también comercial y dentro de vídeos; no se puede vender la fuente por sí sola). Descargada el 2026-11-18 de `https://github.com/google/fonts/tree/main/ofl/lilitaone` (Google Fonts). Archivos: `assets/fonts/LilitaOne-Regular.ttf` y `assets/fonts/OFL-LilitaOne.txt` (texto de la licencia).
- Cobertura comprobada con un test: ñ Ñ á é í ó ú Á É Í Ó Ú ü Ü ¡ ¿ × « » y cifras. Solo trae un peso (ya es negrita, estilo redondeado de juego, parecido al del vídeo de referencia).

## Imágenes

- **Foto de hierba (fondo de los vídeos)** — `assets/img/hierba.avif` (500×750 px). Título «Campo de hierba verde durante el día», autor **bady abbas** (`https://unsplash.com/es/@bady`), página `https://unsplash.com/es/fotos/campo-de-hierba-verde-durante-el-dia-5HI7Ea3yD-w` (indicada por el usuario el 2026-11-18; datos comprobados en esa página el mismo día). Licencia: **Unsplash License** (`https://unsplash.com/license`): uso gratuito comercial y no comercial, se puede copiar y modificar sin pedir permiso; la atribución **no es obligatoria** (se agradece: «Photo by bady abbas on Unsplash»); no se permite compilar imágenes de Unsplash para montar un servicio similar o competidor (no es nuestro caso). Se usa recortada y ampliada como fondo. Opcional: incluir el crédito en la descripción de los vídeos.
