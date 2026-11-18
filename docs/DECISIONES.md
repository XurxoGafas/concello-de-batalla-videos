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

## Cálculo del porcentaje de vacas y el multiplicador

El porcentaje se calcula como `(vacas_mayor − vacas_menor) / vacas_menor`, es decir, el porcentaje **extra** que tiene el bando con más vacas sobre el que tiene menos. Ese porcentaje se redondea a la decena (unidad ≤ 5 → hacia abajo, unidad ≥ 6 → hacia arriba) para obtener el multiplicador, con tope en 50 % (ver tabla completa en `PLAN.md`, paso 3.1).

**Ejemplo confirmado por el usuario:** Arteixo (1500 vacas) ataca a A Coruña (1200 vacas). Diferencia: `(1500 − 1200) / 1200 = 25 %`. Redondeo: unidad 5 → hacia abajo → se queda en 20 % → **multiplicador ×1,2** para Arteixo. A Coruña no multiplica su puntuación.

## Vacas y multiplicador cuando un dueño tiene varios concellos (territorio combinado)

**Confirmado:** las vacas que cuentan para el multiplicador son las del **territorio completo** del dueño, no solo las del concello implicado directamente en la batalla. Las vacas se suman al conquistar: si A Coruña (1200 vacas) le gana a Arteixo (1500 vacas), A Coruña pasa a tener `1200 + 1500 = 2700` vacas en total, y esa cifra es la que se usará en cualquier batalla futura de ese territorio (ataque o defensa), sea con el concello que fue originalmente A Coruña o con cualquier otro concello limítrofe de su territorio combinado.

## Vecindad entre concellos (paso 2.2)

**Confirmado por el usuario (2026-11-18):** dos concellos son vecinos si sus fronteras se tocan, **aunque solo coincidan en una esquina (un único punto)**; no hace falta que compartan una línea. Con los datos del IGN salen 826 parejas por contacto (806 por línea y 20 solo por un punto).

**Isla de A Illa de Arousa:** no toca a ningún concello. Sin una conexión manual no podría atacar ni ser atacada, y la serie no podría terminar con un único dueño. El usuario eligió conectarla a mano; hoy está conectada solo con **Vilanova de Arousa** (el puente de la PO-307 la une con ese concello). *Pendiente de confirmar:* el usuario eligió «Vilanova de Arousa y O Grove» basándose en un dato no verificado que le di (que el puente llegaba a ambos); las fuentes de la Xunta solo mencionan Vilanova. Si quiere añadir O Grove igualmente, basta una línea en `data/vecindades_manuales.json`.

## Fusión de territorio

- El territorio y las vacas del perdedor pasan íntegros al ganador (ver sección anterior).
- El territorio combinado se pinta en el mapa con el color/bandera del ganador y conserva el nombre del concello ganador como «dueño» de esa región.

## Final de la partida (sin reinicio automático)

**Confirmado:** el proyecto es una **serie diaria estilo TikTok**, pensada para generar expectación y engagement a lo largo de muchos episodios (campaña larga y gradual sobre los 313 concellos). La partida termina cuando un único dueño se queda con todo el territorio de Galicia; en ese momento se declara ganador en el vídeo correspondiente. **No hay reinicio automático** — decidir si empieza una temporada nueva es una decisión manual y posterior, fuera del alcance de este plan por ahora.

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
