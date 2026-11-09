# Protocolo del squad (versión ligera para hackathon)

## 1. Una misión = un Issue

Cada **resultado demostrable** vive en un Issue creado con la plantilla **Misión** (nada de Issues para microtareas). Para retomar trabajo, lee el Issue de abajo hacia arriba: el último evento válido emitido por el asiento autorizado, dentro de su alcance, determina el estado; nunca desplaza decisiones L4, prohibiciones de seguridad ni autorizaciones T2.

## 2. Cuatro eventos

Cada evento es un comentario en el Issue que empieza con su nombre.

| Evento | Quién | Contenido mínimo |
|---|---|---|
| `RELEASE` | CTO Sintético | Objetivo, criterio de terminado, superficie (carpetas o archivos), tier, revisor |
| `CLAIM` | Codex | Rama, commit de `main` del que parte, superficie que aparta |
| `RETURN` | Codex | PR, commit exacto (`EXACT_HEAD`), qué hizo, cómo probarlo, qué falta |
| `REVIEW` | Revisor (Hack Ops u otro asignado) | Commit revisado, `PASS` o `CORRECCIÓN` con hallazgos (bloqueante o no) |

Después de `REVIEW: PASS`, el CTO da el visto bueno y **Carlos hace merge**. Una corrección se resuelve en el **mismo PR**.

```mermaid
sequenceDiagram
    participant CTO as CTO Sintético
    participant CX as Codex
    participant R as Revisor
    participant L4 as Carlos
    CTO->>CX: RELEASE (Issue)
    CX->>CTO: CLAIM
    CX->>R: RETURN (PR + EXACT_HEAD)
    R->>CTO: REVIEW
    alt CORRECCIÓN
        CTO->>CX: corrige en el mismo PR
    end
    CTO->>L4: listo para merge
    L4->>L4: merge o hold
```

## 3. Superficies (quién aparta qué)

- Un dueño por superficie. Se aparta en el `CLAIM`.
- Por defecto: `src/` y `experiments/` son de Codex (único ejecutor de código del MVP); `docs/` es de Hack Ops y del CTO. Antigravity no aparta superficie del repo: opera el entorno LT01 dentro de autorizaciones L4, sin tocar el producto.
- ¿Necesitas algo fuera de tu superficie? **Detente** y pídelo en el Issue; no lo toques.
- Leer y revisar no aparta nada y puede hacerse en paralelo.

## 4. Niveles de riesgo

| Tier | Qué cubre | Quién autoriza |
|---|---|---|
| **T0** | Leer, investigar, evaluar | Nadie; libre |
| **T1** | Código o docs en este repo por PR | La misión + merge de Carlos |
| **T2 en perímetro** | Llamadas a la API dentro de un perímetro autorizado (proveedor, modelo, presupuesto, periodo) | Carlos, **una vez**, como `L4_DECISION` en el Issue |
| **T2 fuera de perímetro** | Deploy, exponer algo a internet (p. ej. túneles), otro proveedor, datos reales, crear service accounts o vaults | **Carlos, acción por acción** |

Un PASS en T1 **no** autoriza nada de T2.

## 5. La revisión independiente

- La hace alguien distinto del productor, en una sesión limpia, sobre el commit exacto.
- Un subagente del mismo productor **no cuenta** como revisión independiente.
- Se mide por los defectos útiles que encuentra, no por cuántos PASS da.

## 6. Cuándo detenerse (STOP)

Detente, reporta en el Issue y espera decisión si:

- Vas a tocar algo fuera de tu superficie.
- Aparece un secreto o una credencial expuesta, o un valor de secreto fuera de 1Password.
- La acción es T2 y no tiene el ok de Carlos.
- No está claro quién tiene la autoridad.

## 7. RETURN mínimo

```text
RETURN
PR:
EXACT_HEAD:
QUÉ HICE:
CÓMO PROBARLO:
QUÉ FALTA / RIESGOS:
```

## 8. Perímetro T2 (plantilla de `L4_DECISION`)

```text
L4_DECISION · PERÍMETRO T2
PROVEEDOR:      (p. ej. OpenAI)
MODELOS:        (p. ej. los que fije el RELEASE)
PRESUPUESTO:    (tope en USD)
PERIODO:        (p. ej. 2026-11-09 12:00–17:00 CDMX)
SECRETO:        op://<vault>/<item>/<campo> (1Password)
FUERA DE ALCANCE: deploy, túneles, otros proveedores, datos reales
```
