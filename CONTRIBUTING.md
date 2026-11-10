# Cómo contribuir

El canal es un issue con la plantilla **Feedback de experto**. Discussions queda pendiente: lo habilita Carlos cuando lo decida.

## Qué nos sirve

Un hallazgo concreto sobre el caso, la lección, la evaluación, la demo o los límites. Si puedes, incluye el comando que corriste y el archivo que miraste.

Las cinco preguntas del README están en la sección [Para expertos](README.md#para-expertos).

## Qué no envíes

- Datos de clientes, documentos reales, correos, teléfonos o nombres de personas reales.
- Llaves, tokens, contraseñas ni volcados de entorno.
- Material interno de producto que este repo público no contiene: prompts privados, protocolos o datos de clientes.

Si un ejemplo hace falta, invéntalo y márcalo como ficticio, con dominio `.example`.

## Cómo correr las pruebas

```bash
python3 -m unittest discover -s experiments
python3 experiments/eval_b2b.py --writer stub
```

No hace falta red ni API key. No ejecutes `experiments/record_codex_runs.py` sin ser el operador y sin el ok correspondiente: ese script llama a Codex.
