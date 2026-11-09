# AGENTS.md — léelo antes de hacer cualquier cosa

Este repo es el proyecto **Scribe/Recovery** del hackathon (9 nov 2026, CDMX) y también el experimento de cómo opera un squad de agentes de IA.

## La regla central

**Codex es el único que ejecuta.** Codex escribe el código y opera a los agentes empleados que viven en este proyecto.
Los demás asientos (CTO Sintético, Antigravity, Hack Ops) **no escriben código de producto**: ordenan el harness de Codex (entorno, reglas, tareas y revisión) para que Codex rinda.

## Antes de empezar

1. Ubica tu asiento en [`docs/SQUAD.md`](docs/SQUAD.md). Si no estás ahí, detente y pide asiento al CTO Sintético.
2. Lee el protocolo en [`docs/SQUAD_PROTOCOL.md`](docs/SQUAD_PROTOCOL.md).
3. Lee las decisiones vigentes en [`docs/DECISIONS.md`](docs/DECISIONS.md).

## Reglas de la casa

- Una misión = un Issue. El estado vive en GitHub, no en el chat.
- Trabaja en una rama `feat/<tema>` (código) o `docs/<tema>` (documentación) y abre un PR. **Nunca hagas push directo a `main`.** Solo Carlos (L4) hace merge.
- Toca solo la superficie que apartaste en tu `CLAIM`. Si necesitas otra, detente y pídela en el Issue.
- Sin secretos en el repo: usa `.env` local y documenta las variables en `.env.example`.
- Todo lo que toque algo real (llaves de API, deploy, servicios externos, datos de personas) es **T2** y necesita el ok explícito de Carlos en cada acción.
- Si cambias stack o arquitectura, agrega una fila en `docs/DECISIONS.md`.
