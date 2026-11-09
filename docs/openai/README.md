# Referencia OpenAI para Scribe/Recovery

Mapa breve de fuentes oficiales para Codex y el experimento Scribe/Recovery. La selección y las recomendaciones de esta carpeta son editoriales del proyecto; la documentación enlazada pertenece a OpenAI.

**Revisión de fuentes:** 2026-11-09. **Idioma:** guía del proyecto en español; las fuentes oficiales pueden estar en inglés.

## Empieza aquí

| Necesidad | Fuente oficial | Guía local |
|---|---|---|
| Ejecutar Codex desde CLI y entender su flujo de eventos | [Codex: non-interactive mode](https://developers.openai.com/codex/non-interactive-mode) | [Codex CLI, ejecuciones y evidencia](codex-runtime.md) |
| Buscar y leer documentación OpenAI desde una herramienta MCP | [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp) | [Docs MCP: alcance y gate](docs-mcp.md) |
| Depurar y evaluar flujos de agentes | [Evaluate agent workflows](https://developers.openai.com/api/docs/guides/agent-evals) | [Scribe/Recovery: pruebas y evidencia](recovery-evidence.md) |
| Consultar la documentación general de la API | [OpenAI API docs](https://developers.openai.com/api/docs/) | [Scribe/Recovery: pruebas y evidencia](recovery-evidence.md) |
| Revisar el estado del producto Evals anterior | [Working with evals](https://developers.openai.com/api/docs/guides/evals) | [Scribe/Recovery: pruebas y evidencia](recovery-evidence.md) |

La ruta `/codex/non-interactive-mode` redirige a `learn.chatgpt.com`, dominio oficial de OpenAI. El endpoint `https://developers.openai.com/mcp` es la URL del servidor MCP, no una página para abrir en un navegador.

## Cómo leer las etiquetas

- **OFICIAL:** afirmación o comando expresamente descrito en una fuente oficial enlazada.
- **RECOMENDACIÓN DEL PROYECTO:** selección o práctica propuesta para este repo; no atribuirla a OpenAI.
- **VALIDADO_EN_LT01:** resultado local respaldado por un comando, SHA o `RETURN` identificable.
- **POR_VALIDAR_EN_LT01:** todavía no se ejecutó aquí o requiere un permiso pendiente.

Cada afirmación técnica lleva su fuente o identifica su evidencia de proyecto. Los resultados locales no demuestran una capacidad general del modelo.

## Vigencia y mantenimiento

Las fechas indican cuándo se consultó cada página, no una garantía de que su contenido siga igual. Antes de reutilizar una instrucción:

1. Abre la fuente oficial enlazada y comprueba que la página y el comando siguen vigentes.
2. Para cambios de producto, revisa también el [changelog](https://developers.openai.com/api/docs/changelog) y la página oficial de [deprecaciones](https://developers.openai.com/api/docs/deprecations).
3. Actualiza la fecha de comprobación de la guía afectada; resume el cambio y enlaza la fuente. No copies páginas enteras.
4. Verifica enlaces externos e internos, y busca comandos que puedan cambiar configuración, llamar APIs o exponer datos antes de proponer ejecutarlos.

**Cambio sensible vigente al 2026-11-09:** la página oficial de [Evals](https://developers.openai.com/api/docs/guides/evals) indica que el contenido existente quedó en modo de solo lectura el 2026-10-31 y que el apagado está programado para el 2026-11-30. Revalidar ese calendario antes de usar Evals.

## Límites de esta referencia

- La recomendación inicial cubre solo Codex CLI, Docs MCP y evaluación/evidencia de recuperación; no es un catálogo exhaustivo de OpenAI.
- PR #1 sigue abierto en el `START_PIN` de Issue #3. Por ello, los enlaces desde `README.md` y `AGENTS.md` están **DEFERRED** hasta que ese PR se fusione y se comprueben el HEAD fresco y los conflictos.
- Docs MCP está documentado como propuesta. Su configuración, conexión y prueba de humo siguen en **HOLD T2** según Issue #3; esta carpeta no autoriza ni afirma que se haya conectado.
