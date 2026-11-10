# Cómo opera el squad

Vista rápida de quién hace qué y cómo fluye una misión. Las reglas completas están en [`AGENTS.md`](../AGENTS.md), [`SQUAD.md`](SQUAD.md) y [`SQUAD_PROTOCOL.md`](SQUAD_PROTOCOL.md). GitHub es la fuente de verdad.

## 1. Asientos y fronteras

```mermaid
flowchart TB
    L4["Carlos · L4<br/>decide, firma T2, único merge"]
    CTO["CTO Sintético · ChatGPT nube<br/>dirección técnica, RELEASE y REVIEW"]
    HO["Hack Ops · Grok Bot<br/>docs, Issues, revisión, bitácora, demo<br/>coordina Cursor · GitHub: antonda2025-lab"]
    CR["Cursor · revisor externo<br/>read-only · SHA exacto"]
    AG["Antigravity · LT01<br/>opera el entorno del nodo<br/>sin producto ni T2 implícito"]
    CX["Codex · LT01<br/>T1 productor · único ejecutor MVP<br/>GitHub: cuenta de laboratorio del nodo"]
    subgraph EMP["Agentes empleados · uno a la vez"]
        B["Builder"] --> T["Tester"] --> S["Scribe"]
    end
    GH[("GitHub · SSOT<br/>Issues, PRs, DECISIONS.md")]

    L4 -->|"prioridad, L4_DECISION, merge"| GH
    CTO -->|"RELEASE / REVIEW"| GH
    HO -->|"Issues, docs/, REVIEW técnico"| GH
    HO -->|"opera"| CR
    CR -.->|"auditoría read-only"| GH
    CX -->|"CLAIM, PR, RETURN"| GH
    AG -.->|"preflight y evidencia del nodo"| GH
    AG -.->|"prepara el entorno"| CX
    CX --> EMP
```

| Asiento | Puede tocar | No puede |
|---|---|---|
| Carlos (L4) | Todo; merge a `main`; gates T2 | — |
| CTO Sintético | `RELEASE`, `REVIEW`, `docs/` vía PR | Código de producto, merge |
| Hack Ops | `docs/`, plantillas, Issues, revisión; lectura de LT01; opera Cursor | Código de producto, cambios en LT01 sin ok, merge, escritura en rama del productor |
| Antigravity | Entorno LT01 dentro de autorizaciones L4 | Producto, merge, secretos/API/túneles sin gate T2 |
| Codex | `src/`, `experiments/`, ramas `feat/*` (T1 productor) | `main` directo, secretos, T2 sin gate; no auto-revisa |
| Cursor | Checkout aislado read-only del SHA del productor | Escritura en rama Codex, secretos, merge |

## 2. Ciclo de una misión

```mermaid
sequenceDiagram
    participant L4 as Carlos L4
    participant HO as Hack Ops
    participant CR as Cursor
    participant CTO as CTO Sintético
    participant CX as Codex
    HO->>HO: Abre Issue de misión (plantilla)
    CTO->>HO: RELEASE en el Issue: objetivo, superficie, tier
    CX->>CTO: CLAIM: SESSION_ID + worktree + LOCKED_PATHS
    CX->>CX: Builder → Tester → Scribe en rama feat/*
    CX->>HO: PR + RETURN con EXACT_HEAD
    Note over CX: Productor en pausa hasta REVIEW
    HO->>CR: Opera auditoría read-only del SHA
    CR-->>HO: Hallazgos + pruebas
    HO->>CX: REVIEW técnico (firma Grok)
    CTO->>CX: REVIEW independiente: PASS o CORRECCIÓN
    CX-->>CTO: Corrige en el mismo PR y devuelve EXACT_HEAD
    L4->>L4: Merge a main (solo Carlos)
```

Reglas clave: un Issue por resultado demostrable; el último evento válido del asiento autorizado, dentro de su alcance, define el estado; nada desplaza decisiones L4, seguridad ni gates T2; si algo cae fuera de tu superficie, STOP y se pide en el Issue.

## 3. Fases del proyecto

```mermaid
flowchart LR
    F0["Fase 0 · Prototipo<br/>solo suscripción de Codex<br/>sin API ni secretos · T1"] -->|"Carlos decide · L4_DECISION T2"| F1["Fase 1 · Funcional<br/>API de OpenAI pagada por token<br/>llave vía 1Password op run"]
```
