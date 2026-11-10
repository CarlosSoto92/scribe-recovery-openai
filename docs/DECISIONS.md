# Decisiones

Registro corto de decisiones reversibles del hackathon.

| # | Fecha | Decisión | Quién | Estado |
|---|-------|----------|-------|--------|
| 1 | 2026-11-09 | Repo público `scribe-recovery-openai` en CarlosSoto92, licencia MIT | Carlos / CTO Sintético | Hecho |
| 2 | 2026-11-09 | Stack sin fijar; estructura mínima `src/`, `experiments/`, `docs/` | Hack Ops | Provisional |
| 3 | 2026-11-09 | Codex trabaja en ramas `feat/*` y abre PR; nadie hace push directo a `main` | Hack Ops | Vigente |
| 4 | 2026-11-09 | Codex es el único que ejecuta; CTO, Antigravity y Hack Ops ordenan su harness (ver docs/SQUAD.md) | Carlos | Vigente |
| 5 | 2026-11-09 | Protocolo ligero: Issue + RELEASE/CLAIM/RETURN/REVIEW; tiers T0/T1/T2 | CTO + Carlos | Vigente |
| 6 | 2026-11-09 | Autoridad de ejecución única: Codex ejecuta; Antigravity diagnostica y recomienda (B1 del CTO) | Carlos | Vigente |
| 7 | 2026-11-09 | T2 por perímetro (proveedor, modelo, presupuesto, periodo) como L4_DECISION (B2 del CTO) | Carlos | Vigente |
| 8 | 2026-11-09 | Secretos solo en 1Password: `op run` con referencias `op://` y SDK con service account de alcance mínimo | Carlos | Vigente |
| 9 | 2026-11-09 | Agentes empleados Builder → Tester → Scribe en secuencia; máximo 1 a la vez en LT01; sin Ollama | CTO + Antigravity | Vigente |
| 10 | 2026-11-09 | Descartado: ampliar la superficie de Antigravity a `harness/` (choca con la decisión 6) | Carlos | Descartada |
| 11 | 2026-11-09 | Pendiente: cómo se proyecta el demo; un túnel público es T2 | Carlos | Abierta |
| 12 | 2026-11-09 | Dos fases: Fase 0 prototipo solo con suscripción de Codex (sin API ni secretos); Fase 1 funcional con API de OpenAI pagada por token + 1Password. 1Password queda en espera hasta Fase 1 | Carlos | Vigente |
| 13 | 2026-11-09 | Frontera producto / nodo: Codex es el único ejecutor de código del MVP; Antigravity opera el entorno LT01 (diagnóstico, instalación, configuración, preflight) dentro de autorizaciones L4, sin producto ni T2 implícito. Reemplaza el alcance de #4, #6 y #10 solo en lo que toca a operar el nodo; esas filas siguen vigentes para el producto | Carlos (vía CTO) | Vigente |
| 14 | 2026-11-09 | Aislamiento/lock de sesiones T1 + revisión cruzada: CLAIM declara SESSION_ID/WORKTREE_PATH/BRANCH/START_PIN/LOCKED_PATHS/OWNER; una escritora por superficie; productor en pausa tras RETURN; Cursor (vía Grok) revisa read-only el SHA exacto sin escribir la rama del productor. Originado en colisión LT-01 Issue #2 / PR #4 (CTO DOC_REQUEST) | Carlos (vía CTO) | Vigente |
