# CLAUDE.md — Reglas de trabajo del proyecto «Concello de Batalla»

Este archivo se lee al empezar **cada sesión**.

## Reglas

**a) Al empezar cada sesión**, lee `CLAUDE.md`, `PLAN.md` y `PROGRESO.md` antes de hacer nada.

**b) Un paso cada vez**, en el orden de `PLAN.md`, salvo que el usuario diga lo contrario. No se empieza un paso nuevo con otro `[~]` a medias.

**c) Cada vez que completes un paso:**
- Márcalo como `[x]` en `PLAN.md` (y como `[~]` mientras esté en curso).
- Añade una entrada en `PROGRESO.md` con:
  - Fecha y número/nombre del paso
  - Qué se hizo
  - Cómo se completó (decisiones tomadas, archivos creados o modificados, comandos usados)
  - Problemas encontrados y cómo se resolvieron
  - Qué queda pendiente o qué hay que tener en cuenta para el siguiente paso
- Un paso solo está completado cuando se cumple su criterio «Hecho cuando».

**d) Si cambia el plan** (se añade, quita o modifica un paso), actualiza `PLAN.md` y explica el motivo en `PROGRESO.md`.

**e) No borres entradas antiguas de `PROGRESO.md`.** Es el historial del proyecto. Solo se añaden entradas nuevas, al final.

**f) Si tienes una duda importante, pregunta antes de seguir.** No la inventes. Esto incluye las reglas del juego, las fuentes de datos, las cuentas o los tokens y cualquier decisión difícil de deshacer.

## Reglas adicionales

**g) Secretos:** nunca escribas tokens, contraseñas ni claves en el código ni en el repositorio. Ponlos en `.env` (ignorado por git) o en los secretos del hosting, y documenta los nombres de las variables en `.env.example`.

**h) Publicación:** no publiques nada en público en una red social sin la confirmación explícita del usuario. Las pruebas se hacen en privado o como borrador.

**i) Reproducibilidad:** toda aleatoriedad del juego usa una semilla registrada, para poder repetir cualquier batalla.

**j) Licencias:** todo recurso externo (datos, sonidos, música, tipografías) se registra en `docs/FUENTES.md` con su fuente y su licencia antes de usarlo.

**k) Tests:** la lógica del juego (`src/motor/`) no se da por terminada sin tests que pasen.

**l) Idioma:** documentación y comentarios en castellano.

## Nota sobre continuidad entre sesiones

Cada sesión de Claude Code corre en un contenedor nuevo y vacío: lo único que persiste de una sesión a otra es lo que quede **commiteado y empujado (`git push`) a este repositorio de GitHub**. Antes de dar un paso por completado, haz commit y push de los archivos que lo demuestran — si no, la siguiente sesión no encontrará el trabajo.
