# Playbook reutilizable del squad Scribe/Recovery (hackathon)

**Estado:** conocimiento operativo propuesto, pendiente de REVIEW y merge L4. **Origen:** experimento Scribe/Recovery, 9 de noviembre de 2026. **Uso:** futuros proyectos y operadores, sin copiar la gobernanza específica del hackathon.

## Entrada rápida para cualquier agente

1. Leer el `AGENTS.md` **del repositorio de destino** y sus reglas vigentes; nunca suponer que este playbook reemplaza la autoridad del proyecto.
2. Si vas a preparar LT-01, seguir [PREFLIGHT_LT01.md](PREFLIGHT_LT01.md). Para otro nodo, adaptar *comprobaciones*, no copiar rutas ni valores.
3. Si vas a producir cambios, seguir [CODEX_DELIVERY_LOOP.md](CODEX_DELIVERY_LOOP.md): CLAIM → trabajo acotado → RETURN → REVIEW externo → merge humano.
4. Registrar en el Issue un resultado verificable y el SHA exacto. El handoff mínimo es **URL GitHub + acción + retorno esperado**.
5. Detenerse ante una contradicción con L4, seguridad, restricciones T2 o una modificación externa inesperada.

**Jerarquía:** instrucciones L4 vigentes y normas superiores → reglas del repo de destino → evidencia fresca del host/Git → misión/RELEASE → este playbook. No trasladar automáticamente asientos, hashes, permisos, identidades, rutas, costes ni políticas a otro repositorio.

## Mapa de activos

| Archivo | Qué resuelve | Prueba pendiente |
| --- | --- | --- |
| [PREFLIGHT_LT01.md](PREFLIGHT_LT01.md) | Distingue provisioning, arranque de jornada y preflight por misión; comprobaciones seguras y STOP | Ejecutarlo en tres jornadas reales y registrar duración |
| [CODEX_DELIVERY_LOOP.md](CODEX_DELIVERY_LOOP.md) | Sesiones/worktrees exclusivos; codex exec; RETURN/REVIEW; corrección y merge | Repetir una misión sintética en otro repositorio no productivo |
| [Issue #6](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/6) | Decisión sobre dónde estandarizar este método (lab privado / otros repos) | L4 decide promoción a repositorio compartido |
| [Protocolo local](../SQUAD_PROTOCOL.md) | Autoridades T0/T1/T2 del hackathon | No transportar automáticamente a un proyecto nuevo |

## Reality checks: evidencia → aprendizaje → regla

| Evidencia y calificación | Qué observamos / qué NO demuestra | Regla reutilizable |
| --- | --- | --- |
| **OBSERVADO**, 9 nov, relato L4: ~90 min para pasar de llegada a operar agentes | Es *primera preparación total*, no medición de warm start; no se conoce desglose | Medir provisioning separado de arranque recurrente; objetivo provisional warm start <10–15 min, no ahorro proclamado |
| **COMPROBADO**: [Issue #2 STOP](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/2#issuecomment-6749931717), [coordinación](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/2#issuecomment-6750110660) | Dos Codex compartieron checkout/rama; hubo archivos y staging inesperados. No se atribuyó con certeza la autoría | Un único escritor por superficie y checkout; CLAIM con sesión/worktree; STOP y preservar evidencia ante interferencia |
| **COMPROBADO**: [PR #1](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/1) integrado, commit 29be441, merge posterior en main | Las reglas de concurrencia pasaron a documentación versionada | Issue asigna responsabilidad, **no** aísla filesystem ni procesos; usar worktree y dueño explícito |
| **OBSERVADO según RETURN de Hack Ops**: [PR #4 RETURN_DELTA](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6751776707) | Codex CLI 0.167 con `codex exec` y worktree exclusivo; operador externo realizó push fuera del sandbox. No significa que todo host admita los mismos flags | Grok coordina una sesión escritora; verificar ayuda/versionado, permisos reales y cuota; commit/push gobernados sin bypass de seguridad |
| **COMPROBADO en GitHub con ejecución reportada por Cursor/Grok**: [PR #4 REVIEW](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4#issuecomment-6751959019), [merge](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4) | 16→20 tests; las regresiones nuevas fallaron sobre código anterior y pasaron sobre SHA 7c34712; demo V1→Scribe→V2 PASS | Revisor distinto del constructor, checkout limpio, SHA exacto; registrar pruebas ejecutadas vs inspección |
| **COMPROBADO**: [Issue #7](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/7) y [PR #8](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/8) | CSV Phase 0 recupera dentro de mismo run_id; **no** es memoria entre sesiones ni aprendizaje de agente general | Separar evidencia del mecanismo, hipótesis comercial y alcance de futuro producto |
| **POR VALIDAR**: arranque repetible y portabilidad | No hay tres tiempos de warm start ni prueba documentada de otro repo | No convertir este patrón en estándar global antes de una réplica verificable |

## Fronteras que protegen el aprendizaje

- **Squad ≠ producto:** eventos de `codex exec --json` describen el trabajo del constructor; el ledger JSONL de Scribe/Recovery es otro sistema. No mezclar sus evidencias.
- **Una terminal adicional ≠ capacidad paralela:** worktrees aíslan archivos; no RAM, servicios, branches remotas compartidas o autoridad de escritura. Medir recursos.
- **La suscripción Codex ≠ uso ilimitado:** Fase 0 no usa la API del producto, pero la cuota de Codex existe; no inventar coste cero total o volumen de tokens.
- **Publicar un PR ≠ aprobar su contenido:** Grok/Cursor revisan; CTO/L4 evalúan y **L4 fusiona**. Un PASS sobre SHA antiguo no valida un nuevo HEAD.
- **La lección propuesta ≠ lección aprobada:** solo una decisión humana trazable puede activar cambio de skill, `AGENTS.md` o comportamiento en otro agente.
- **Repo público ≠ depósito de IP:** no exponer prompts internos, fuentes privadas, clientes, credenciales ni datos personales.

## Métricas para la próxima réplica

Registrar **fecha, nodo, repo, tipo de arranque, inicio, READY, primer CLAIM, RETURN, REVIEW, merge, número de intervenciones humanas, colisiones/STOP y resultado del smoke**. Reportar intervalos reales (no estimados). Tras tres arranques, comparar mediana de warm start con la meta provisional. Tras una misión en otro repo, decidir si convertir el flujo en una skill y si moverlo a un lab privado designado por L4.

**Próximo paso recomendado:** primero probar este playbook; después, si reduce trabajo, convertir el preflight manual en un script read-only pequeño. No crear orquestador, daemon, panel o nueva infraestructura como requisito.
