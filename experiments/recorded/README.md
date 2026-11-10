# Corridas grabadas de Codex

Esta carpeta guarda, cuando el operador las haga, las salidas de `codex exec` y su `MANIFEST.json`.

**En este commit no hay corridas.** El marcador del modelo real queda en `pendiente: corridas de Codex por grabar`. No se inventan textos ni cifras.

## Quién graba

Solo el operador, en su máquina, con la suscripción de Codex (Fase 0, sin API key) y con el ok de Carlos. El script es `experiments/record_codex_runs.py`. No forma parte de los tests ni de CI.

```bash
# No llama a Codex. Muestra el plan.
python3 experiments/record_codex_runs.py --dry-run --controls

# Grabación real, una corrida a la vez, sin pisar carpetas.
python3 experiments/record_codex_runs.py --reps 1 --controls --operator "nombre-del-operador"
```

`--reps 2` repite B− y B+. C3 (lección de otro tipo) se graba una vez por tipo. El valor por defecto es 1 repetición.

## Qué se guarda

- `codex-<fecha UTC>/MANIFEST.json`: versión de Codex, comando saneado, hash del prompt, hash de la nota, hash de la skill inyectada, sandbox, fecha UTC y operador.
- `<tipo>-case-NN__<condición>__rK.txt`: solo el texto final del documento.

No se guardan eventos JSON crudos ni rutas de la cuenta del operador. El script sustituye el home por `~`.

## Cómo se puntúa

```bash
python3 experiments/eval_b2b.py --replay experiments/recorded/codex-<fecha>
```

Eso corre offline, con los mismos checkers. Si un hash no coincide, sale con código 2 y no publica un marcador.

`MANIFEST.example.json` solo enseña la forma del archivo. No es una corrida y el replay lo rechaza.
