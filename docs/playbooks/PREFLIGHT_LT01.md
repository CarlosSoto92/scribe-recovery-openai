# Preflight LT-01 — arranque verificable del squad

**Tipo:** guía manual T0, **solo lectura**. **No ejecuta instalaciones, login, limpieza Git, kills, pulls, deploy ni cambios de secretos.** Adaptar a otro nodo antes de reutilizar. **Owner operativo:** Grok/Hack Ops, con Antigravity como observador y operador del host autorizado.

## Tres cosas que no debemos confundir

| Etapa | Cuándo | Salida |
| --- | --- | --- |
| **Provisioning** | Primera instalación o tras cambios relevantes | Binarios, acceso, permisos y rutas instaladas y probadas por operador autorizado; no usar esta duración para medir warm start |
| **Warm preflight** | Una vez por jornada, con nodo ya configurado | `READY / DEGRADED / STOP`, hora, versión, auth sin secretos, RAM, estado de procesos y Git |
| **Preflight por misión** | Justo antes del CLAIM y de cada escritura | `SESSION_ID / ISSUE / WORKTREE_PATH / BRANCH / START_PIN / LOCKED_PATHS / OWNER` verificables |

**Baseline observado:** L4 necesitó alrededor de **90 minutos** de preparación hasta operar con agentes el 9 de noviembre de 2026; incluye setup inicial y coordinación. **Meta provisional:** warm preflight inferior a **10–15 min** y preflight por misión inferior a **2–3 min** en entorno previamente dispuesto. **No se ha medido la mejora.**

## Paso A. Comprobaciones locales sin mutación

Ejecutar desde el checkout indicado por la misión. Los resultados son **locales**; no pegar logs completos con rutas privadas, argumentos o datos sensibles en GitHub.

~~~bash
# Herramientas: solo lectura, no instalación ni ejecución del agente
date -Is
command -v git
command -v gh
command -v codex
command -v python3
git --version
gh --version
codex --version
python3 --version
codex exec --help

# Recursos: instantánea; NO garantía futura
free -h
df -h .

# Git y aislamiento
pwd
git rev-parse --show-toplevel
git rev-parse HEAD
git branch --show-current
git status --short
git worktree list --porcelain
git remote

# Procesos codex. Solo PID/estado/nombre, no argumentos o prompts
ps -C codex -o pid=,ppid=,stat=,comm=
~~~

Para autentificación, el operador puede comprobar `gh auth status` en pantalla local sin volcar tokens, cookies o credenciales al Issue. Si el comando no funciona, registrar **AUTH_POR_VALIDAR**; no usar `gh auth token` ni copiar archivos de configuración. `git remote` solo lista nombres; validar la identidad y el host esperado de manera controlada, sin publicar URLs con credenciales embebidas.

**Nota:** `git fetch` puede cambiar metadatos Git, por lo que **no** forma parte del diagnóstico T0 totalmente read-only. Si Grok necesita actualizar refs, hacerlo como paso operativo T1 autorizado y después fijar `START_PIN` y rama. No ejecutar comandos de limpieza ni cambiar de rama durante el preflight.

## Paso B. Evaluar exclusividad del escritor

1. Comprobar que el directorio y rama coincidan con el CLAIM esperado, y que la superficie de escritura esté libre.
2. Inspeccionar `git status --short`; un checkout no limpio **no se borra ni se restaura automáticamente**. Identificar dueño de cada cambio.
3. Revisar worktrees y procesos; dos terminales en el mismo checkout **no** son escritores independientes. Un worktree exclusivo no reserva una rama remota por sí mismo.
4. Confirmar capacidad real de RAM/CPU para la misión; en el experimento LT-01 se ha mantenido **una sesión escritora activa**. No arrancar dos constructores por tener dos terminales.
5. Si el CLI está en sandbox `workspace-write`, verificar sus límites reales. En worktrees, operaciones de commit pueden necesitar rutas del directorio Git compartido; **no conceder automáticamente `--add-dir` a `.git` o `.git/worktrees`**. Grok puede realizar commit/push desde entorno autorizado y auditado, o pedir alternativa explícita.
6. Si hay un proceso desconocido, discrepancia de rama, cambios externos o ruta inesperada: **STOP** y preservar evidencia. Un PID o `git status` limpio por sí solo no acredita propiedad.

## Paso C. Dictamen del warm preflight

| Resultado | Cuándo | Acción |
| --- | --- | --- |
| **READY** | Runtime, autenticación necesaria, repo, SHA y writer único verificados; recursos suficientes | Grok puede despachar misión T1 previamente autorizada y publicar CLAIM completo |
| **DEGRADED** | Falta función no necesaria para la tarea (p. ej. documentación MCP opcional), sin riesgo en escrituras | Ejecutar solo el perímetro seguro; documentar qué no fue validado |
| **STOP** | Autoridad o dueño incierto; worktree contaminado; secreto; falta de auth esencial; RAM insuficiente; T2 no aprobado | No ejecutar Codex escritor; escalar a L4/CTO por Issue con evidencia sanitizada |

**Plantilla de registro (no inventar valores):**

~~~text
PREFLIGHT · fecha/hora y zona:
NODO / REPO:
PROVISIONING (nuevo / existente):
DURACIÓN hasta READY:
VERSIONES (Codex/Git/Python):
MAIN_REMOTO / START_PIN:
WORKTREES / PROCESOS (resumen sanitizado):
RAM disponible observada:
AUTH (identidad y estado, nunca token):
RESULTADO: READY | DEGRADED | STOP
CAUSAS / RESPONSABLE / SIGUIENTE ACCIÓN:
~~~

## Paso D. Cierre de jornada y repetición

- Tras RETURN, el productor queda **pausado** hasta REVIEW. No reubicar una sesión bloqueada sin una nueva orden de Grok.
- Antes de declarar misión lista, comparar `EXACT_HEAD`, tests, demo y REVIEWED_HEAD. L4 decide merge.
- Tras merge, smoke sobre `main` actualizado: misma suite o prueba de aceptación en checkout limpio y SHA registrado.
- Cerrar únicamente procesos identificados como propios y cuyo fin esté aprobado; nunca matar por coincidencia superficial de PID.
- Registrar tiempos separados: `llegada → READY`, `READY → CLAIM`, `CLAIM → RETURN`, `RETURN → REVIEW`. Repetir en tres arranques antes de publicar mejora de tiempo.

## STOP conocidos y evidencia de procedencia

- [Colisión de dos terminales, Issue #2](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/2#issuecomment-6749931717): cambios externos y staging inesperado → STOP.
- [Nuevo STOP por ownership, PR #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6750965186): una sesión anterior quedó en rama distinta y detectó proceso adicional → no tomó propiedad.
- [Recuperación: RETURN con codex exec y worktree](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6751776707): Grok documentó escritor único y push fuera del sandbox; evidencia operativa del caso, **no receta válida universal**.

**Límite:** este documento es un checklist humano verificable, no un script probado. Crear el kit automatizado solo si la primera ejecución manual muestra un ahorro real y mantiene control local y de credenciales.
