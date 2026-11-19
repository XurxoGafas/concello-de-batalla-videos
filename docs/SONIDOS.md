# SONIDOS — esquema previo (paso 5.1)

Decisión del usuario (2026-11-19): **no hay música de fondo**; solo efectos, que deben ser «estimulantes»
y satisfactorios. Todo se sincroniza con los eventos de la animación (a velocidad ×1,296). Los efectos se
generan por síntesis (sin licencias de terceros). La cancioncilla de gaita la compone Claude.

Prioridad: **A** imprescindible · **B** deseable · **C** opcional.

**Estado:** ✅ aprobado por el usuario · ⏳ generado, pendiente de aprobación · (vacío) sin generar. Los cambios se piden por el número («el 05 más lento»). Archivos en `assets/audio/NN_nombre.wav`; código en `src/audio/sintesis.py`.

| Nº | Escena | Evento visual | Sonido | Prior. | Estado |
|---|---|---|---|---|---|
| 01 | Portada (2 s) | aparece la silueta | golpe grave con brillo | A | ✅ |
| 02 |  | aparece la frase | «pop» suave | B | ✅ |
| 03 |  | la silueta vuela al mapa (0,8 s) | whoosh ascendente | A | ✅ |
| 04 | Intro (1 s) | mapa visible | silencio (o un «ding» breve) — por defecto, silencio | C |  |
| 05 | Sorteo del atacante (≈2 s) | cada dueño resaltado (15 tics) | tic de bloque de madera, cada vez más lento, agudo y fuerte. **Montaje: cada tic exactamente cuando se resalta ese dueño** (indicación del usuario) | A | ✅ |
| 06 |  | queda bloqueado (rojo) — también se usa en el sorteo del defensor (9) | «clac» + campanilla | A | ✅ |
| 07 | Zoom al atacante | el mapa se acerca | whoosh suave | A | ✅ |
| 08 | Sorteo del defensor | cada candidato (≈9) | tic más suave y grave que el 05. **Montaje: cada tic cuando se resalta ese concello** | A | ✅ |
| 09 |  | queda bloqueado | usa el 06 (clac + campanilla) | A | ✅ |
| 10 | Zoom a los dos bandos | el mapa se acerca; entra el defensor en el panel | whoosh + «pop». **Montaje: el «pop» coincide con la entrada del defensor en el panel** (indicación del usuario) | A | ✅ |
| 11 | Duelo (1,7 s) | entra la navaja | silbido de metal (termina en el choque) | A | ✅ |
| 12 |  | entra la botella | deslizar de cristal (termina en el choque) | A | ✅ |
| 13 |  | choque y destello | choque metálico + tintineo de cristal (empieza en el choque) | A | ✅ |
| 14 |  | «LIORTA!» | golpe de graves (empieza en el choque, con el temblor) | A | ✅ |
| 15 | Dados | los 6 dados ruedan | traqueteo (uno por tirada, mientras ruedan los dos dados de esa fila) | A | ✅ |
| 16 |  | cada dado se para | golpe seco de madera, escalonado (suena cuando termina el rodar de la fila) | A | ✅ |
| 17 |  | insignia «+N» | «ding» que sube de nota según N (1–5): 5 archivos `17_ding_masN.wav`; suena 0,1 s después de pararse el dado | A | ✅ |
| 18 |  | «=» (empate de tirada) | tic apagado (suena con la insignia «=», 0,1 s después de pararse el dado) | B | ⏳ |
| 19 |  | el marcador suma | tic de moneda (suena cuando el marcador suma, al pararse el dado) | B | ⏳ |
| 20 |  | multiplicador ×1,N | barrido ascendente + acorde brillante, más fuerte cuanto mayor el multiplicador: 5 archivos `20_multiplicador_x1_N.wav`; el acorde coincide con el cambio del marcador a decimales | A | ⏳ |
| 21 |  | recuadro del ganador | campanilla de victoria corta | A |  |
| 22 | Morte súbita | tarjeta en llamas | alarma grave + crepitar de fuego | A |  |
| 23 |  | dado extra | traqueteo + golpe | A |  |
| 24 | Conquista | cambian los rótulos CAMPIÓN/MALOGRADO | destello (whoosh + chispas) | A |  |
| 25 |  | entra la gaita | cancioncilla de gaita (≈3 s) | A |  |
| 26 |  | confeti (2 tandas) | estallidos de papel/«pops» | B |  |
| 27 |  | pastillas «+N vacas» y «+K concellos» | campanilla / «cha-ching» | B |  |
| 28 |  | el color se extiende (hasta 24 pasos) | «pop» suave por paso, cada vez más agudo | A |  |
| 29 | Alejamiento (ataque suelto) | el mapa se aleja | whoosh descendente | B |  |
| 30 | Fundidos entre escenas |  | «swish» muy suave | C |  |
| 31 | Cierre | aparece el panel de rankings | whoosh corto | B |  |
| 32 |  | cada fila del ranking (10) | «pop»/tic; la primera de cada lista con campanilla | B |  |
| 33 | Final de la serie | «CAMPIÓN DE GALICIA» | fanfarria grande + gaita | A |  |
| 34 | Opcional | pastillas de vacas | mugido (necesita una muestra real; sintetizado suena a juguete) | C |  |

## Reglas de mezcla
- Mono/estéreo según el efecto; volumen normalizado ≈ −14 LUFS; sin picos (limitador).
- Un efecto nunca tapa a otro: los eventos simultáneos (dado que se para + «+N») se escalonan 30–60 ms.
- Sin música: los silencios entre efectos son intencionados.

## Cancioncilla de gaita (conquista)
Melodía original (no una pieza existente), ≈3 s, en modo mixolidio/dórico con ritmo de muiñeira (6/8), sobre un
bordón continuo. Renderizado con timbre sintetizado; si el usuario aporta muestras de una gaita real, se usan
(registrando su licencia en `docs/FUENTES.md`).
