# Codex Delivery Loop — guía operativa transferible

**Versión candidata:** 2026-11-09. **No sustituye** al `AGENTS.md`, las políticas L4 ni al `RELEASE` del repo de destino. **Roles en el experimento:** Grok/Hack Ops dirige Codex; CTO fija alcance y revisa técnicamente; Cursor audita; Carlos/L4 decide merge y riesgos sensibles.

## Resultado visible que buscamos

Una intención del usuario se transforma en **un PR pequeño, probado, revisado por un tercero, con SHA reproducible y sin colisión de escritores**. Si el proceso pesa más que el cambio, reducir pasos; no dividir un resultado en micro-Issues.

### Misión mínima, una sola vez

~~~text
OBJETIVO COMERCIAL / USUARIO:
ARTEFACTO VISIBLE:
ENTRADAS Y ACTIVOS A REUTILIZAR:
REPO / RAMA BASE:
LOCKED_PATHS (solo lo permitido):
RESTRICCIONES / TIER:
PRUEBA DE ACEPTACIÓN (positiva + negativa):
PRESUPUESTO DE EJECUCIÓN / STOP:
DESTINO DE DEMO O STAGING:
~~~

## Ciclo con autoridad separada

1. **RELEASE (CTO, en Issue):** objetivo y restricciones, tier, superficie, prueba, revisor, stop. L4 gobierna decisiones sensibles. Un RELEASE no reserva checkout ni concede varios CLAIM.
2. **Despacho operativo (Grok):** preparar worktree y rama exclusivos; ejecutar [preflight](PREFLIGHT_LT01.md), asignar **un solo escritor** y un objetivo verificable. Ninguna orden paralela desde CTO a terminales Codex.
3. **CLAIM (Grok/Codex, en Issue):** registrar valores reales, no un «pending» permanente:
   
   ~~~text
   CLAIM
   ISSUE:
   SESSION_ID:
   WORKTREE_PATH:
   BRANCH:
   START_PIN:
   LOCKED_PATHS:
   OWNER (operador y escritor):
   TIER / TEST / STOP:
   ~~~
   
   Si el ID del thread solo se conoce tras `thread.started`, publicar complemento `CLAIM_UPDATE` con el ID real **antes de continuar escrituras significativas**. Si el proceso trabaja en otro worktree/branch, **STOP**.
4. **Construcción (Codex):** trabajar exclusivamente en el lock, reutilizar pruebas existentes, escribir casos de regresión para fallos reales, no inventar éxito. En LT-01 Grok reportó `codex exec --json` con CLI 0.167 y autenticación existente. La ejecución es **secuencial** mientras la RAM lo exija.
5. **Commit/push (operador designado):** no dar privilegios amplios al sandbox para sortear límites de Git. En el caso PR #4, Codex produjo el cambio y Grok hizo push fast-forward fuera del sandbox controlado. Verificar autoría, `git status --short` y diff. **Nunca force push ni main directo** sin decisión nueva L4.
6. **RETURN:** PR, `EXACT_HEAD`, archivos, comandos realmente ejecutados, resultados, fallos, riesgos y lecciones. Productor en pausa.
7. **REVIEW independiente:** Cursor por Grok desde checkout limpio y **read-only de la rama del productor**, SHA exacto, pruebas reproducidas + severidad y utilidad de producto. Un subagente del mismo constructor no equivale a un revisor independiente.
8. **Disposición y merge:** CTO determina PASS/CORRECCIÓN. Si corregir, **mismo PR**, nuevo SHA y re-review incremental; solo L4 fusiona. **PASS antiguo ≠ PASS del HEAD nuevo**.
9. **Smoke post-merge:** verificar `main` nuevo y la demo/test desde estado limpio. Registrar commit integrado, no inferir éxito del exit code aislado.

### Handoff entre agentes

~~~text
Grok: [URL de Issue/PR] · acción exacta + superficie + gate ·
retorno esperado: PR/EXACT_HEAD/tests o STOP con evidencia.
~~~

Cualquier agente que no tenga OWNER o LOCKED_PATHS claros entra **T0 read-only** y pregunta en el Issue, no asume la misión.

## Casos reales y correcciones del método

| Caso | Dato del experimento | Decisión reutilizable |
| --- | --- | --- |
| Doble terminal compartiendo checkout | [Issue #2 STOP](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/2#issuecomment-6749931717) | Una sola sesión escritora por superficie; checkout no se comparte |
| Sesión A se encontró con rama docs y segundo proceso | [PR #4 STOP](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6750965186) | No recuperar por `reset --hard`, `clean` o cambio de rama mientras no se identifique ownership |
| Recuperación con Grok + codex exec | [RETURN_DELTA #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6751776707) | Separar operación Git externa al sandbox, controlar una rama y un worktree |
| Revisión independiente útil | [REVIEW Cursor #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6751959019) | Nuevos tests deben FALLAR sobre el código viejo y PASAR en el nuevo cuando sea aplicable |
| 16 vs «21» tests | [REVIEW inicial](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6750694423) | No sumar métodos y `subTest` ni reconstruir un contador por memoria; verificar suite en commit |
| Producto Scribe/Recovery | [Issue #7](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/7) | No confundir ledger de demostración con eventos de Codex ni afirmar que una corrida equivale a aprendizaje general |

## Codex CLI: aprender de un caso, no fijar dogmas

**Reportado y observado en LT-01, CLI 0.167:** `codex exec` no interactivo; `--json` produce eventos estructurados; el operador puede hacer push desde un contexto autorizado fuera del sandbox. **Por revalidar en cada host/versión:** flags, permisos, salida, cuota y comportamiento de `resume`, `fork`, MCP y skills.

- Hack Ops reportó que el flag `--full-auto` no estaba disponible en la versión utilizada; se empleó `--sandbox workspace-write`. **No generalizar a otras versiones:** consultar `codex exec --help`.
- En un worktree, la metadata Git puede residir en una ruta común fuera del sandbox. Ante fallo de commit, NO conceder automáticamente `--add-dir` sobre `.git` o `.git/worktrees`; preferir gestión de Git por el operador con rutas y permisos auditados.
- Para reanudar sesión, Hack Ops observó sensibilidad al orden de flags alrededor de `resume`. Antes de estandarizar, repetir experimento de bajo riesgo con la ayuda de la versión actual.
- `--json` no crea por sí mismo «memoria». Capturar eventos mínimos y saneados en almacenamiento local controlado; **no** subir el stream completo a GitHub sin revisión. Distinguir id de sesión/hilo de id de producto.
- El funcionamiento con autenticación de la suscripción no autoriza acceso a API de producto o gastos T2; tampoco implica créditos ilimitados.

## Plantillas de salida

~~~text
RETURN
ISSUE / PR:
EXACT_HEAD:
SESSION_ID / BRANCH / WORKTREE:
CAMBIO_VISIBLE:
ARCHIVOS:
TESTS_EJECUTADOS (comando + resultado):
DEMO (entrada / salida / estado):
RIESGOS / LIMITES / COSTE O DURACIÓN:
STOP O HANDOFF:
~~~

~~~text
REVIEW_INDEPENDIENTE
REVIEWED_HEAD:
REVISOR / ENTORNO:
PRUEBAS EJECUTADAS vs SOLO INSPECCIONADAS:
RESULT=PASS | CORRECCIÓN | INCONCLUSO:
HALLAZGOS (severidad + reproducción + cambio mínimo):
UTILIDAD PARA USUARIO Y CLAIMS:
REVIEW DELTA REQUERIDO:
~~~

## Métrica de aprendizaje y portabilidad

No contar «agentes activos», prompts o commits como productividad. Medir por misión: minutos desde RELEASE→primer CLAIM→RETURN→REVIEW→merge; número de aclaraciones e intervenciones L4; defectos útiles detectados; STOP, cambios fuera de lock y retrocesos. **Probar una misión T1 sintética en otro repo no productivo** antes de promover esto a estándar global/skill.

**STOP obligatorio:** escritor ambiguo, scope o permisos inciertos, token/PII, datos/IP privados en repo público, alteración de producción, credenciales, uso de API/T2 sin autorización, automatización de envíos o publicación, comandos destructivos, o pruebas no repetibles. El humano gobierna; el agente ejecuta; la evidencia permite decidir.
