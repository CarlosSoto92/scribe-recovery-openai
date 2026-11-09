# Codex CLI: ejecuciones y evidencia

**Comprobado:** 2026-11-09. **Alcance:** `codex exec` no interactivo y su salida estructurada.

## OFICIAL

La guía oficial de [Codex non-interactive mode](https://developers.openai.com/codex/non-interactive-mode) describe `codex exec --json` como salida JSON Lines (`JSONL`) a `stdout`. Entre los eventos están `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*` y `error`. Los elementos pueden representar mensajes, ejecución de comandos, cambios de archivos, llamadas a herramientas MCP, búsquedas web y actualizaciones del plan. La opción `-o` / `--output-last-message` guarda el mensaje final; la documentación indica que también sigue apareciendo en `stdout`.

Ejemplo oficial de forma, **solo referencia; no ejecutado en esta misión**:

```sh
codex exec --json "summarize the repo structure" | jq
```

La referencia cubre el flujo de eventos emitido por Codex CLI. No lo confundas con el ledger de eventos que Scribe guarda para el producto.

## RECOMENDACIÓN DEL PROYECTO

Para investigar una ejecución, conserva el JSONL de Codex junto a un identificador de corrida, el commit revisado, el comando utilizado y el resultado. Separa esa evidencia del ledger funcional de Scribe. Usa fixtures sintéticos y excluye credenciales, datos personales y contenido sensible. Antes de automatizar, comprueba en la versión local del CLI los nombres y campos de eventos que realmente aparecen.

## VALIDACIÓN

- **POR_VALIDAR_EN_LT01:** esta misión no ejecutó `codex exec --json`; no se ha comprobado la disponibilidad del comando ni el esquema de eventos de la instalación local.
- **VALIDADO_EN_LT01 (solo demo Scribe/Recovery):** el `RETURN` de Issue #2 en [PR #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4), `EXACT_HEAD=e0ab38f7c8ff1742d6810f655cecd561ecb529ea`, registra 16 pruebas y seis comprobaciones de demo correctas. Eso valida el experimento en ese SHA, no la captura JSONL de Codex.
