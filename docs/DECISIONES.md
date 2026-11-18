# DECISIONES — Concello de Batalla

Decisiones tomadas por el usuario. No se cambian sin su aprobación explícita.

## Estructura de un vídeo (7 fases)

Cada vídeo contiene **3 enfrentamientos** (313 concellos ÷ batallas por vídeo → la partida avanza 3 conquistas por episodio y continúa en el siguiente vídeo). Las fases 2 a 6 se repiten 3 veces dentro de un mismo vídeo (fase 7).

**Fase 1 — Micro intro:**
Una imagen corta (1–2 segundos como máximo) que hace una transición hacia el mapa de Galicia del episodio actual. En el episodio 1, el mapa muestra todos los concellos coloreados según su propia bandera (cada concello es su propio dueño).

**Fase 2 — Selección del atacante:**
Se elige al azar un concello atacante entre los dueños vivos. Se hace zoom en el mapa centrado en ese concello, de forma que se vean los concellos con los que hace frontera. Se muestra en pantalla el número de vacas del atacante, debajo de su nombre.

**Fase 3 — Selección del defensor:**
Se elige al azar un defensor, solo entre los concellos que hacen frontera con el atacante. Una vez elegido, se muestran en pantalla las siluetas de ambos concellos, cada una con su nombre y, debajo del nombre, su número de vacas.

**Fase 4 — Tirada de dados:**
Se tiran 3 dados por cada concello. En cada tirada se compara el resultado de ambos y la diferencia se suma a favor de quien saque más. Ejemplo: concello 1 saca un 6 y concello 2 saca un 1 → +5 puntos para el concello 1. Se repite con el 2º y 3er dado y se obtiene una puntuación total acumulada para cada concello.

**Fase 5 — Multiplicador y empate:**
- El concello (o dueño) que tenga **más vacas** multiplica su puntuación total por el bonus correspondiente (ver tabla de multiplicador en `PLAN.md`, paso 3.1). El otro bando no multiplica.
- Se comparan las puntuaciones ya con el multiplicador aplicado.
- **Si hay empate** (puede ocurrir si las vacas son similares y no hay bonus, o por coincidencia tras aplicar el bonus): se tira un dado adicional por cada concello. Si ese dado desempata (uno saca más que el otro), gana quien saque más. Si vuelve a haber empate, se repite con otro dado adicional, y así hasta desempatar.

**Fase 6 — Resultado y conquista:**
Gana el concello con más puntuación (tras multiplicador y, si hizo falta, desempate). El ganador absorbe del perdedor: su número de vacas y su territorio. El territorio conquistado pasa a mostrarse en el mapa con el nombre y los colores de la bandera del concello ganador, igual que el resto de su territorio.

**Fase 7 — Repetición:**
Las fases 2 a 6 se repiten 3 veces dentro del mismo vídeo (3 batallas por episodio), avanzando siempre sobre el estado resultante de la batalla anterior dentro del mismo vídeo.

**Fase 8 — Cierre con ranking (confirmada el 2026-11-18, a partir del vídeo de referencia):**
Tras la última batalla del vídeo, una pantalla de cierre con:
- El mapa general de Galicia con el estado actual.
- El nombre de la serie + número de episodio (p. ej. «Ep. 27»).
- Dos rankings top 5: **«Máis vitorias»** (concellos con más batallas ganadas a lo largo de toda la serie, acumulado) y **«Máis territorio»** (concellos con más concellos bajo su dominio en ese momento).
- *(Decisión de diseño, no confirmada por el usuario, a revisar si no convence): «territorio» se mide en número de concellos controlados, no en km², porque es más simple de entender en un vídeo corto y más coherente con la unidad del juego (concellos, no superficie).*

## Mecánica de dados y puntuación — resumen técnico

- 3 dados por concello y enfrentamiento.
- Puntuación = suma de las diferencias (dado propio − dado rival) en las tiradas donde el concello saca más; no se restan puntos cuando se pierde una tirada individual, solo se suma la diferencia a favor del que saca más en cada una de las 3 tiradas.
- El multiplicador se aplica **solo** al bando con más vacas, sobre su puntuación total ya sumada (no dado a dado).
- Empate tras multiplicador → dados de muerte súbita (1 dado por bando, se repite hasta desempatar).

## Puntuación con decimales (paso 3.2)

**Confirmado por el usuario (2026-11-18):** tras aplicar el multiplicador, las puntuaciones se comparan **con decimales, sin redondear**. Como los puntos de los dados son enteros y el multiplicador tiene un solo decimal (×1,1 a ×1,5), la puntuación tiene como mucho **un decimal** (p. ej. 7 × 1,3 = 9,1). Se guarda en décimas (enteros) para que la comparación sea exacta. Casi desaparecen los empates; solo se llega a muerte súbita cuando las puntuaciones son exactamente iguales (p. ej. 4 × 1,5 = 6,0 contra 6).

**Reproducibilidad (regla i):** cada batalla usa una semilla. El orden de los sorteos es parte del contrato: por cada una de las 3 tiradas, dado del atacante y luego dado del defensor; después, por cada ronda de muerte súbita, dado del atacante y luego del defensor. Además cada resultado guarda todos sus dados, así que una batalla se puede repetir o dibujar sin volver a sortear aunque cambie la versión de Python.

## Cálculo del porcentaje de vacas y el multiplicador

El porcentaje se calcula como `(vacas_mayor − vacas_menor) / vacas_menor`, es decir, el porcentaje **extra** que tiene el bando con más vacas sobre el que tiene menos. Ese porcentaje se redondea a la decena (unidad ≤ 5 → hacia abajo, unidad ≥ 6 → hacia arriba) para obtener el multiplicador, con tope en 50 % (ver tabla completa en `PLAN.md`, paso 3.1).

**Ejemplo confirmado por el usuario:** Arteixo (1500 vacas) ataca a A Coruña (1200 vacas). Diferencia: `(1500 − 1200) / 1200 = 25 %`. Redondeo: unidad 5 → hacia abajo → se queda en 20 % → **multiplicador ×1,2** para Arteixo. A Coruña no multiplica su puntuación.

**Decimales en el redondeo (decisión de implementación, paso 3.1; revisable):** los ejemplos del usuario solo usan porcentajes enteros. Para un porcentaje con decimales se mira cuánto sobra de la decena: **si sobra más de 5 se sube, si sobra 5 o menos se baja** (35 % → ×1,3; 35,5 % → ×1,4). Con porcentajes enteros coincide exactamente con la regla del usuario.

**Efecto real del multiplicador (calculado enumerando todas las tiradas, con la muerte súbita al 50 %):** el bando favorecido gana el 50 % sin bonus, 54–55 % con ×1,1 o ×1,2, 56 % con ×1,3, 58 % con ×1,4 y **59 % con ×1,5**. Con los datos reales de vacas, el **80 % de las parejas de vecinos** parte ya del tope ×1,5.

## Vacas y multiplicador cuando un dueño tiene varios concellos (territorio combinado)

**Confirmado:** las vacas que cuentan para el multiplicador son las del **territorio completo** del dueño, no solo las del concello implicado directamente en la batalla. Las vacas se suman al conquistar: si A Coruña (1200 vacas) le gana a Arteixo (1500 vacas), A Coruña pasa a tener `1200 + 1500 = 2700` vacas en total, y esa cifra es la que se usará en cualquier batalla futura de ese territorio (ataque o defensa), sea con el concello que fue originalmente A Coruña o con cualquier otro concello limítrofe de su territorio combinado.

## Vecindad entre concellos (paso 2.2)

**Confirmado por el usuario (2026-11-18):** dos concellos son vecinos si sus fronteras se tocan, **aunque solo coincidan en una esquina (un único punto)**; no hace falta que compartan una línea. Con los datos del IGN salen 826 parejas por contacto (806 por línea y 20 solo por un punto).

**Isla de A Illa de Arousa:** no toca a ningún concello. Sin una conexión manual no podría atacar ni ser atacada, y la serie no podría terminar con un único dueño. **Decisión final del usuario (2026-11-18): queda conectada solo con Vilanova de Arousa** (el puente de la PO-307 la une con ese concello). Está en `data/vecindades_manuales.json`. (Antes había elegido añadir también O Grove, pero se basaba en un dato no verificado; las fuentes de la Xunta solo mencionan Vilanova.)

## Fusión de territorio

- El territorio y las vacas del perdedor pasan íntegros al ganador (ver sección anterior).
- El territorio combinado se pinta en el mapa con el color/bandera del ganador y conserva el nombre del concello ganador como «dueño» de esa región.

## Final de la partida (sin reinicio automático)

**Confirmado:** el proyecto es una **serie diaria estilo TikTok**, pensada para generar expectación y engagement a lo largo de muchos episodios (campaña larga y gradual sobre los 313 concellos). La partida termina cuando un único dueño se queda con todo el territorio de Galicia; en ese momento se declara ganador en el vídeo correspondiente. **No hay reinicio automático** — decidir si empieza una temporada nueva es una decisión manual y posterior, fuera del alcance de este plan por ahora.

## Qué cuenta como «vaca» y de qué año (paso 2.3)

**Decisión de implementación (el usuario indicó el IGE como fuente; la elección de variable y año es mía, revisable):** se usa la variable «Número de vacas» del IGE (vacas de muxidura + non muxidura), **no** el total de bovinos (que incluye terneros y novillas). Año **2025** (último disponible). Con esto el total gallego es de 511.138 vacas.

**Resultado del caso «sin dato»:** no hay ningún concello vigente sin dato en la fuente, así que no hubo que preguntar casos sueltos. Siete concellos tienen 0 vacas oficiales y pasan a 1 (A Arnoia, Barbadás, Larouco, Ribadavia, Rubiá, Toén y A Illa de Arousa).

## Color de cada concello = su bandera (paso 2.4)

**Confirmado por el usuario (2026-11-18):** el color de cada concello es el de su bandera. Se guarda una **paleta** de hasta 4 colores con su proporción de superficie (el primero es el principal, para rellenar el territorio con un color liso); así se podrá usar también para rayas o un patrón. Los colores se extraen de la imagen de la bandera.

**Decidido por el usuario (2026-11-18):** de momento todos los concellos llevan un **color genérico distinto del de los demás** (`"fonte": "provisional"` en el estado), y el usuario enviará las banderas para sustituirlos (paso 2.5 de `PLAN.md`). Los concellos de los que no llegue bandera conservarán su color provisional.

## Concellos sin dato de vacas

**Confirmado — dos casos distintos:**
- Si un concello no tiene ningún dato disponible en la fuente (falta el registro): se resolverá caso por caso cuando el usuario revise el conjunto de datos de vacas (paso 2.3 de `PLAN.md`) y señale qué concellos faltan.
- Si un concello tiene oficialmente **0 vacas**: se trata como si tuviera **1 vaca**, para que el cálculo del porcentaje y del multiplicador nunca tenga que dividir por cero.

## Idioma

**Confirmado: gallego.** Todos los textos en pantalla, títulos, descripciones y narración de los vídeos van en gallego. (La documentación interna del proyecto — `PLAN.md`, `CLAUDE.md`, `PROGRESO.md`, este archivo — sigue en castellano, por ser documentación de trabajo, no contenido del vídeo.)

## Duración y frecuencia

**Confirmado:** vídeo diario, serie que avanza de forma gradual (no se resuelve en pocos días). Duración objetivo de cada episodio: **entre 1:20 y 1:30 (80–90 segundos)** aproximadamente, con las 3 batallas dentro.

*Nota técnica a tener en cuenta en el paso 6.2 (validación técnica) y 7.1 (YouTube):* YouTube Shorts admite duraciones de hasta 3 minutos a fecha de hoy, pero conviene comprobar en el momento de implementar el límite vigente; Instagram Reels y TikTok no deberían tener problema con 80–90 s. Si al implementar se comprueba que algún límite oficial ha cambiado y choca con 80–90 s, se avisará antes de seguir.

## Cadencia por vídeo

- **3 batallas por vídeo, publicación diaria.** Con 313 concellos, la partida es una campaña larga que avanza vídeo a vídeo hasta quedar un único dueño.

## Stack técnico (paso 0.2)

**Python 3.11+**, con:
- `geopandas` / `shapely` para la geometría de los concellos y las adyacencias.
- `Pillow` (o `pycairo`) para dibujar cada fotograma (mapa, siluetas, dados, marcador).
- `ffmpeg` (vía `ffmpeg-python` o llamada directa) para montar el vídeo final y mezclar el audio.
- Tests con `pytest`.

Se descarta Remotion/React por ser más pesado de ejecutar en un entorno gratuito y no aportar nada que no cubra el stack de Python para este caso.

## Hosting y programación (paso 0.3)

**Repositorio en GitHub + GitHub Actions con cron.**

- **Repositorio:** el plan original preveía un repositorio privado (2.000 minutos de Actions/mes, de sobra para un vídeo diario). El repositorio real creado por el usuario (`XurxoGafas/concello-de-batalla-videos`) es público; con repo público GitHub Actions da minutos ilimitados, así que sigue encajando — solo cambia que el código es visible por cualquiera. Si se prefiriera ocultar el código o los datos de la partida, se podría pasar a privado más adelante.
- **Dónde se ejecuta:** GitHub Actions, no una VM propia, porque no exige mantenimiento de servidor. Alternativa si algún día no bastara: una VM Always Free de Oracle Cloud.
- **Persistencia del estado:** el estado de la partida (`estado_actual.json`, `historial.jsonl`) se guarda haciendo commit al propio repositorio en cada ejecución, así no hace falta una base de datos ni un disco externo.
- **Secretos:** los tokens de YouTube, Instagram y TikTok se guardan como "Secrets" de GitHub (cifrados, nunca visibles en el código).

## Vídeo de referencia (analizado el 2026-11-18)

El usuario adjuntó un vídeo de ejemplo del formato en el que se basa este proyecto (76 s, 720×1280, varias batallas de países encadenadas). Del análisis fotograma a fotograma se confirma el estilo visual general (fondo azul marino oscuro, dorado para títulos y multiplicador, tipografía redondeada en negrita, línea dorada separando el mapa del panel inferior) y se extraen dos elementos nuevos para el plan:

- Icono de **espadas cruzadas** entre ambos bandos antes de la tirada de dados (fase 4/5).
- Pantalla de conquista con las etiquetas **«LOSER» / «WINNER»** (en gallego: «PERDEDOR» / «GAÑADOR») y un icono de espada apuntando hacia el ganador (fase 6).
- La **pantalla de ranking de cierre** (fase 8, añadida arriba).

**Importante — el multiplicador del vídeo de referencia NO se usa como modelo:** en el vídeo, ambos bandos muestran y aplican su propio multiplicador (p. ej. ×1,1 y ×1,2 a la vez, según la población absoluta de cada uno). El usuario confirmó explícitamente que esto no aplica aquí y que se mantiene la regla ya decidida: **solo multiplica el bando con más vacas**, sobre la diferencia relativa de vacas respecto al otro (ver sección «Cálculo del porcentaje de vacas»).

## Datos nuevos a persistir por la fase 8 (ranking)

Para poder mostrar el ranking de «máis vitorias» hace falta llevar la cuenta, por dueño, del número de batallas ganadas acumuladas a lo largo de toda la serie (no solo del episodio actual). Esto afecta al paso 3.5 (persistencia) y 2.4 (estado inicial) de `PLAN.md`: el estado debe guardar un contador de victorias por dueño además del territorio y las vacas.

## Todo resuelto

No quedan dudas abiertas de las planteadas inicialmente en `PLAN.md`. La definición de «territorio» para el ranking (número de concellos, no km²) es una decisión de diseño no confirmada explícitamente por el usuario — revisar si no convence. Cualquier duda nueva que surja durante la implementación se añadirá aquí y se preguntará antes de decidir por cuenta propia (regla f de `CLAUDE.md`).

## Conquista y contador de victorias (paso 3.4)

- El ganador absorbe todo el territorio y todas las vacas del perdedor; el dueño perdedor se elimina. El color efectivo de un concello es el de su dueño actual (el concello conserva su propia bandera en el estado, por si hiciera falta).
- **Victorias acumuladas (decisión del usuario, 2026-11-18):** el ganador suma 1 por la batalla ganada y **no hereda** las victorias del perdedor; estas desaparecen con el dueño eliminado. Ejemplo: si O Porriño gana a Ordes, que tenía 10 victorias, O Porriño solo suma 1. El contador de cada dueño es, por tanto, el número de batallas que ha ganado él mismo (sustituye a la interpretación anterior, en la que se heredaban).

## Semillas y persistencia de la partida (paso 3.5)

**Decisión de diseño mía (revisable; afecta a la reproducibilidad y al secreto de los resultados):**

- Hay una **semilla de serie secreta**, que no se guarda en el repositorio: se lee de la variable de entorno `SEMILLA_SERIE` (en GitHub, un *Secret*; en local, `.env`). Motivo: el repositorio es público; si la semilla estuviera dentro, cualquiera podría simular los resultados de los próximos días antes de que se publiquen los vídeos.
- Cada batalla usa su propia semilla, derivada con SHA-256 de `semilla_serie:número_de_batalla` (número global y consecutivo). Esa semilla derivada **sí se guarda** en `data/partida/historial.jsonl` junto con todos los dados, así que cualquier batalla pasada se puede repetir o redibujar, pero no se pueden deducir las futuras.
- No hace falta guardar el estado del generador aleatorio entre ejecuciones: 5 batallas en 5 procesos dan exactamente lo mismo que en 1.
- **Consecuencia importante:** la semilla de serie debe mantenerse igual durante toda la serie y **no se puede recuperar si se pierde** (las batallas ya jugadas están en el historial, pero las siguientes cambiarían). Hay que guardarla en un sitio seguro además de en GitHub Secrets.
- Archivos: `data/partida/estado_actual.json` (estado + `episodio` + `batallas_jugadas`) y `data/partida/historial.jsonl` (una línea por batalla). El estado se guarda de forma atómica y con formato estable (diffs pequeños en cada commit diario). Estado e historial se suben en el mismo commit al final de cada ejecución.
