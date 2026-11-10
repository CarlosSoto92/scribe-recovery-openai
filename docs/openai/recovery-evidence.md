# Scribe/Recovery: pruebas y evidencia

**Comprobado:** 2026-11-09. Esta guía separa la orientación oficial sobre evaluación de la evidencia de la demo local.

## OFICIAL

La guía OpenAI [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals) recomienda empezar por trazas para depurar el comportamiento de un flujo y pasar a datasets y ejecuciones de evaluación repetibles cuando los criterios de calidad estén claros. Es una orientación para flujos con agentes; no prescribe la arquitectura de Scribe/Recovery.

La página de [Working with evals](https://developers.openai.com/api/docs/guides/evals) indica que Evals quedó en modo de solo lectura para usuarios existentes el **2026-10-31** y tiene apagado programado para el **2026-11-30**. Consultada el 2026-11-09, la página recomienda probar Datasets si se empieza con evaluaciones o se necesita un entorno iterativo nuevo. Revalidar el calendario antes de depender de ese producto.

## RECOMENDACIÓN DEL PROYECTO

Para la Fase 0, mantener la prueba determinista local y sintética:

1. Fijar entrada y condición de fallo de V1.
2. Guardar la causa observada y la lección estructurada.
3. Verificar que V2 lee esa lección y realiza un único reintento.
4. Mantener un control negativo sin lección que no recupere.
5. Comprobar resultado, intentos y evidencia del ledger; no llamar a una API ni usar datos reales.

Las trazas y evaluaciones de productos OpenAI no sustituyen el ledger del proyecto. Incorporarlas al producto requeriría una decisión y autorización separadas; esta guía no habilita llamadas de API.

## VALIDADO_EN_LT01 · evidencia reportada

El `RETURN` de Issue #2 en [PR #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4), con `EXACT_HEAD=e0ab38f7c8ff1742d6810f655cecd561ecb529ea`, reporta:

- `python3 -m unittest discover -s experiments -p 'test_*.py' -v` — 16 pruebas correctas.
- `python3 experiments/demo.py` — seis comprobaciones correctas: V1 falla de forma controlada, V2 recupera el total 6 y el control negativo falla.
- `python3 -m py_compile src/scribe_recovery.py experiments/demo.py experiments/test_recovery_regressions.py` — correcto.

Esta es evidencia del productor registrada en el RETURN, no revisión independiente ni aprobación de merge. PR #4 sigue pendiente de revisión/merge según el estado observado al redactar esta guía; no se reejecutaron pruebas en esta misión documental.
