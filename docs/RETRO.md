# Retrospectiva · RSI Hackathon (9 nov 2026, CDMX)

**Evento:** RSI Hackathon · Kavak × OpenAI × Primero AI.  
**Repo:** [CarlosSoto92/scribe-recovery-openai](https://github.com/CarlosSoto92/scribe-recovery-openai) (MIT, público).  
**Demo:** [GitHub Pages](https://carlossoto92.github.io/scribe-recovery-openai/demo/).  
**Corte de esta nota:** cierre post-hackathon (issues/PRs documentales mergeados; UX restante en roadmap).

## 1. Qué buscábamos

Probar que un agente puede **aprender de una corrección humana** sin reentrenar: Scribe registra la falla/corrección; Recovery solo aplica lecciones `approved`; el siguiente borrador retiene hechos críticos de forma medible (B− vs B+).

## 2. Qué se logró (comprobado)

| Entrega | Evidencia |
| --- | --- |
| Gobierno del squad + protocolo | [PR #1](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/1) |
| Misión 1 · demo CSV V1→Scribe→V2 | [PR #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4) · Issue [#2](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/2) |
| Loop editorial + gate humano (M2a–c) | [PR #9](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/9) |
| Codex writer con lección como skill (N=1) | [PR #11](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/11) |
| Mini web local + P0 UX | [PR #12](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/12) |
| Diff visual B−/B+ (UX-04) | [PR #13](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/13) |
| README público + demo estática Pages | [PR #21](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/21) |
| Referencia OpenAI (`docs/openai/`) | [PR #5](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/5) |
| Playbooks de preflight / Codex | [PR #10](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/10) |
| Visión V0 (arquitectura) | [PR #8](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/8) · [`docs/VISION_V0.md`](VISION_V0.md) |

Suite al cierre documental: **87 tests OK** (`python3 -m unittest discover -s experiments`).

## 3. Qué no se hizo (honesto)

- **DALI real / System Card / prompts internos** — fuera de frontera IP del repo público.
- **Sherlock / fuentes privadas** — no integrados.
- **Publicación automática a LinkedIn** — nunca; la persona publica.
- **Docs MCP conectado** — documentado como POR_VALIDAR; T2 HOLD.
- **UX-05…UX-10** — abiertos como roadmap `post-hackathon` ([#15](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/15)–[#20](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/20)).
- **Estandarizar el playbook multi-repo** — decisión L4 / lab privado; no es estándar de marca interna en este público.

## 4. Qué se rompió / improvisó

- **Colisión de sesiones en Misión 1** (STOP / coordinación) antes del merge de #4.
- **Exportador de la demo Pages** (`experiments/export_static_demo.py`): lo escribió **Hack Ops**, no Codex, porque **LT01 estaba offline** al momento del end-to-end.
- **Pushes y merges** con identidades de laboratorio (**Quark-lab-diimenet**, **antonda2025-lab**) bajo autorización L4; merge final humano/gobernado.
- **Chromium personal de Carlos** no fue operable por el agente (sin extensión/CDP) → validación UX con **Playwright + perfil aislado** (Antigravity).
- **Revisión independiente (Cursor)** encontró fallas reales en la mini web (p. ej. `approval_ref` vacío, CSRF antes de replay) corregidas antes del merge de #12/#13.

## 5. Métricas honestas

- Corrida Codex en vivo del writer: **N=1** por rama (sin inferencia estadística).
- Demos y Pages usan **fixtures sintéticos**; gate de demo = `fixture_simulated`.
- Checker **literal + cita**; una paráfrasis puede fallar (etiqueta: SIN MATCH LITERAL).
- **Nada se publica solo** a redes.

## 6. Aprendizajes operativos

1. Un **escritor / un worktree** por misión; `codex exec` en sandbox de escritura **sin** commit desde el sandbox.
2. Push y merge los hace el operador; la revisión cruzada vale la pena.
3. Repo público = **mecanismo + sintéticos**; lab privado = IP de producto (DALI, clientes, prompts).
4. Documentar reality checks (`docs/playbooks/`) evita repetir colisiones.

## 7. Siguiente

- Roadmap UX [#15](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/15)–[#20](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/20) cuando LT01 esté disponible.
- Superficie privada para DALI/Sherlock si L4 lo decide (no en este repo).
- Medir arranques reales del playbook antes de promoverlo a otro destino.

— Hack Ops · cierre autorizado por Carlos (L4)
