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
- Sin secretos en el repo. Las llaves y contraseñas viven en **1Password** (ver sección de secretos abajo).
- **Autoridad de ejecución única:** Codex ejecuta. Antigravity, CTO y Hack Ops diagnostican, recomiendan y revisan; cualquier excepción la autoriza Carlos (L4) por escrito en el Issue.
- **T2 por perímetro:** Carlos autoriza un perímetro (proveedor, modelo, presupuesto y periodo) como `L4_DECISION` en el Issue. Dentro de ese perímetro, las llamadas a la API no requieren aprobación individual. Fuera de él (otro proveedor, deploy, exponer algo a internet, datos reales) se pide ok acción por acción.
- Si cambias stack o arquitectura, agrega una fila en `docs/DECISIONS.md`.

## Fases del proyecto

- **Fase 0, prototipo (ahora):** se construye **solo con la suscripción de Codex** de Carlos (los créditos del hackathon). El prototipo no llama a la API de OpenAI con llave propia ni necesita secretos. Si una tarea parece requerir la API, se detiene y se pide en el Issue.
- **Fase 1, funcional (después):** el producto llama directo a la API de OpenAI y paga por token. Requiere la `L4_DECISION` de perímetro T2 (proveedor, modelo, presupuesto, periodo) y la llave inyectada con 1Password (sección siguiente).
- El paso de Fase 0 a Fase 1 lo decide Carlos (L4). Mientras tanto, la configuración de 1Password queda lista pero en espera.

## Secretos: 1Password (Fase 1)

- Ninguna llave, token ni contraseña se escribe en el repo, en `.env` versionado, en logs ni en comentarios de Issues/PRs.
- Las variables se declaran en `.env.example` como **referencias** `op://<vault>/<item>/<campo>`, nunca como valores.
- Para correr algo que necesita llaves: `op run --env-file=.env.example -- <comando>`. 1Password inyecta los valores solo en ese proceso.
- Código que necesite leer secretos en tiempo de ejecución usa el **SDK de 1Password** con una service account de alcance mínimo (solo el vault del hackathon), no la cuenta personal de Carlos.
- Crear o ampliar una service account o un vault es T2: lo autoriza Carlos.

## Condiciones del nodo LT01

- **Ruta canónica:** `/home/anton-lab/Work/scribe-recovery-openai` (con W mayúscula).
- **Memoria:** 7.1 GB totales y ~2.6 GB disponibles. La RAM es el cuello de botella.
- **Paralelismo:** máximo **1 agente empleado a la vez**. Builder → Tester → Scribe corren en secuencia, nunca en paralelo.
- **Prohibido:** `ollama run` y modelos locales (consumen 2–4 GB). Los modelos se consumen en la nube (Fase 0 vía suscripción de Codex; Fase 1 vía API).
- **Servidores de prueba** (Next.js, FastAPI, etc.): se cierran al terminar cada prueba. No dejes demonios corriendo.
- **Builds de Node:** `NODE_OPTIONS="--max-old-space-size=2048"`.
- Docker está apagado; encenderlo solo si la misión lo pide.

## Agentes empleados de Codex

Codex opera tres roles, **en secuencia** y sin infraestructura multiagente pesada:

1. **Builder:** implementa la misión.
2. **Tester:** corre y escribe pruebas; reporta fallas.
3. **Scribe:** registra errores, causas y lecciones del ciclo (es el corazón del producto).

Una misión = un resultado demostrable. No abras Issues para microtareas.
