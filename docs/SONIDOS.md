# SONIDOS — esquema previo (paso 5.1)

Decisión del usuario (2026-11-19): **no hay música de fondo**; solo efectos, que deben ser «estimulantes»
y satisfactorios. Todo se sincroniza con los eventos de la animación (a velocidad ×1,296). Los efectos se
generan por síntesis (sin licencias de terceros). La cancioncilla de gaita la compone Claude.

Prioridad: **A** imprescindible · **B** deseable · **C** opcional.

| Escena | Evento visual | Sonido | Prior. |
|---|---|---|---|
| Portada (2 s) | aparece la silueta | golpe grave con brillo | A |
| | aparece la frase | «pop» suave | B |
| | la silueta vuela al mapa (0,8 s) | whoosh ascendente | A |
| Intro (1 s) | mapa visible | silencio (o un «ding» breve) | C |
| Sorteo del atacante (≈2 s) | cada cambio de dueño resaltado (14) | tic corto, cada vez más lento y más agudo | A |
| | queda bloqueado (rojo) | «clac» + campanilla | A |
| Zoom al atacante | el mapa se acerca | whoosh | A |
| Sorteo del defensor | cada candidato (≈9) | tic más suave | A |
| | queda bloqueado | «clac» + campanilla | A |
| Zoom a los dos bandos | el mapa se acerca; entra el defensor en el panel | whoosh + «pop» | A |
| Duelo (1,7 s) | entra la navaja / la botella | silbido de metal / deslizar de cristal | A |
| | choque y destello | choque metálico + tintineo de cristal | A |
| | «LIORTA!» | golpe de graves | A |
| Dados | los 6 dados ruedan | traqueteo de dados | A |
| | cada dado se para | golpe seco de madera, escalonado | A |
| | insignia «+N» | «ding» que sube de nota según N (1–5) | A |
| | «=» (empate de tirada) | tic apagado | B |
| | el marcador suma | tic de moneda | B |
| | multiplicador ×1,N | barrido ascendente + acorde brillante (más fuerte con ×1,5) | A |
| | recuadro del ganador | campanilla de victoria corta | A |
| Morte súbita | tarjeta en llamas | alarma grave + crepitar de fuego | A |
| | dado extra | traqueteo + golpe | A |
| Conquista | cambian los rótulos CAMPIÓN/MALOGRADO | destello (whoosh + chispas) | A |
| | entra la gaita | **cancioncilla de gaita** (≈3 s) | A |
| | confeti (2 tandas) | estallidos de papel/«pops» | B |
| | pastillas «+N vacas» y «+K concellos» | campanilla / «cha-ching» | B |
| | el color se extiende (hasta 24 pasos) | «pop» suave por paso, cada vez más agudo | A |
| Alejamiento (ataque suelto) | el mapa se aleja | whoosh descendente | B |
| Fundidos entre escenas | | «swish» muy suave | C |
| Cierre | aparece el panel de rankings | whoosh corto | B |
| | cada fila del ranking (10) | «pop»/tic, la primera de cada lista con campanilla | B |
| Final de la serie | «CAMPIÓN DE GALICIA» | fanfarria grande + gaita | A |
| Vacas (opcional) | pastillas de vacas | mugido (necesita una muestra real; sintetizado suena a juguete) | C |

## Reglas de mezcla
- Mono/estéreo según el efecto; volumen normalizado ≈ −14 LUFS; sin picos (limitador).
- Un efecto nunca tapa a otro: los eventos simultáneos (dado que se para + «+N») se escalonan 30–60 ms.
- Sin música: los silencios entre efectos son intencionados.

## Cancioncilla de gaita (conquista)
Melodía original (no una pieza existente), ≈3 s, en modo mixolidio/dórico con ritmo de muiñeira (6/8), sobre un
bordón continuo. Renderizado con timbre sintetizado; si el usuario aporta muestras de una gaita real, se usan
(registrando su licencia en `docs/FUENTES.md`).
