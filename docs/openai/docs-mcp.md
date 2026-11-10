# Docs MCP: alcance y gate

**Comprobado:** 2026-11-09. **Estado del proyecto:** propuesta documentada; conexión no probada.

## OFICIAL

La página [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp) describe un servidor público MCP por HTTP en `https://developers.openai.com/mcp`. Ofrece búsqueda y lectura de documentación para `developers.openai.com`, `platform.openai.com` y `learn.chatgpt.com`; es de solo lectura y no llama a la API de OpenAI por el usuario.

La instrucción de Codex CLI que muestra la página oficial es:

```sh
codex mcp add openaiDeveloperDocs --url https://developers.openai.com/mcp
```

## RECOMENDACIÓN DEL PROYECTO

La instrucción anterior es **propuesta para referencia; documentar, NO ejecutar** en esta misión. Registrar un servidor MCP cambia la configuración de Codex. Issue #3 clasifica conectar/configurar el servidor y correr una prueba de humo como **T2 en HOLD**, aunque el servidor oficial sea público, de solo lectura y no invoque una API de inferencia.

Alternativa disponible mientras tanto: consultar la documentación oficial directamente en el navegador desde una sesión limpia, sin conectar MCP.

## POR_VALIDAR_EN_LT01

No se ejecutó `codex mcp add`, `codex mcp list` ni una consulta al servidor. No se afirma que el nodo tenga acceso de red al endpoint ni que Codex lo haya conectado. Una validación futura requiere una `L4_DECISION` T2 en Issue #3 que autorice servidor, superficie de configuración, operaciones, duración y criterio de rollback; entonces se podrá acordar una prueba de humo independiente.
