# Misión 1 · Fase 0

Demo de consola con Python 3 y su biblioteca estándar. Sin instalaciones,
secretos ni API del producto. Ejecutar desde la raíz del repositorio:

```bash
python3 experiments/demo.py
python3 -m unittest discover -s experiments -p 'test_*.py' -v
```

La demo crea un directorio temporal fuera del repo y lo elimina al terminar.
Para conservar los dos ledgers sintéticos bajo una carpeta nueva en `/tmp`:

```bash
python3 experiments/demo.py --output-dir /tmp
```

Cada corrida conservada recibe un directorio nuevo; no sobrescribe corridas
anteriores. El código de salida de la demo es 0 solo si todas sus comprobaciones
se cumplen, incluyendo la falla esperada del control negativo.

## V1 y V2 por separado

Usar una ruta de ledger nueva y el mismo `run_id` en los dos comandos. El padre
del ledger debe existir. Ejemplo con una ruta que aún no exista:

```bash
python3 src/scribe_recovery.py v1 --input experiments/fixtures/inventory.csv --ledger /tmp/mi-demo-unica.jsonl --run-id demo-1
python3 src/scribe_recovery.py v2 --input experiments/fixtures/inventory.csv --ledger /tmp/mi-demo-unica.jsonl --run-id demo-1
```

V1 sale con 1 (falla controlada `CSV_SCHEMA`); ejecutar V2 después aunque V1
falle. V2 sale con 0 y calcula total 6 para esta fixture. Código 2 indica entrada,
historial o lección inválida y no ejecuta la tarea. Repetir un intento con el
mismo `run_id`, tarea y hash de entrada se rechaza; elegir una corrida nueva.
El código 2 también ocurre por uso incorrecto del CLI (`argparse`) y no siempre imprime JSON.

Para el control negativo, ejecutar V2 con un ledger nuevo: falla con código 1,
sin lección y usando coma. No basta cambiar el número de versión para recuperar.

## Qué demuestra

V1 intenta sumar `cantidad` suponiendo separador coma. El encabezado real usa
punto y coma. El Scribe del producto observa el error y prueba delimitadores en
el **encabezado**, sin volver a ejecutar la tarea; registra la única separación
que produce las columnas `producto` y `cantidad`. V2 lee esa lección del ledger,
la vincula por `run_id`, `task_id` y SHA-256 del contenido, y ejecuta exactamente
un intento adicional usando el separador registrado. La suma se calcula de las
filas; el éxito no está prefabricado. No hay agente conectado a un modelo ni
autoaprendizaje general: es un mecanismo determinista para una tarea sintética.

Cada línea JSONL incluye `run_id`, `task_id`, `input_sha256`, `attempt`,
`timestamp` UTC, `error`, `lesson`, `outcome`, `result` y `evidence`. El evento V1
conserva la causa y el encabezado observado; el evento V2 conserva el delimitador
usado y la referencia al intento del que consumió la lección. V2 no genera una
lección nueva ni repite internamente. Una lección de otra corrida o entrada no
se aplica; una lección de la corrida actual con estructura incompatible se
rechaza. Un JSONL inválido no se repara ni se trunca.

El ledger es **append-only a nivel de aplicación**, no WORM: otro programa o
persona puede editarlo. La demo local es secuencial, sin protección frente a
escritores concurrentes. No usar datos reales ni colocar credenciales en la
entrada. El CLI rechaza usar el archivo de entrada como ledger.

La demo muestra duración medida y cero llamadas/costo de API del producto. El
consumo de suscripción Codex no está disponible y no se estima. El rol Scribe
del desarrollo registra las causas/lecciones del ciclo de implementación por
separado del ledger sintético del **producto**; estos eventos de demo no son
telemetría real de Codex.

## Misión 2 · Loop editorial V0 con gate humano

```bash
python3 experiments/demo_editorial.py
python3 experiments/demo_editorial.py --output-dir /tmp
python3 experiments/demo_editorial.py --json
```

La demo usa solo datos sintéticos y un gate **simulado**, atribuido a
`fixture_simulated`, nunca a Carlos. V1 omite deliberadamente los hechos
`must_keep`; proposed/rejected no cambian el texto. Solo approved con referencia
habilita la regla por scope y nota. B− y B+ corren en procesos nuevos, con la
misma nota y checker: retención = hechos críticos presentes **y citados** / total.
Se espera 0 frente a 1.0, sin afirmar calidad editorial general ni mejora de LLM.
En V0, para `rule_type=required_fact`, el writer determinista **COPIA** desde la
nota los hechos citados por `evidence.fact_ids` de la lección aprobada; no inventa
hechos. La demo destaca el panel B−/B+; `--json` añade los checks crudos.

**Ensayo CLI · fixture simulada**, desde la raíz: tanto el feedback como la
aprobación son ficticios y se atribuyen a `fixture_simulated`.

```bash
EDITORIAL_RUN=$(mktemp -d /tmp/scribe-editorial-live-XXXXXX)
python3 src/scribe_editorial.py draft --note experiments/fixtures/synthetic_note_001.json --lessons "$EDITORIAL_RUN/lessons.jsonl" --session-id live-v1 --out "$EDITORIAL_RUN/draft.json"
python3 src/scribe_editorial.py feedback --draft "$EDITORIAL_RUN/draft.json" --reviewer fixture_simulated --rating 2 --comment "Falta el dato sintético de 4 semanas" --target-facts f1 --feedback-log "$EDITORIAL_RUN/feedback.jsonl"
EDITORIAL_FEEDBACK_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n")[0])["feedback_id"])' "$EDITORIAL_RUN/feedback.jsonl")
python3 src/scribe_editorial.py propose --feedback "$EDITORIAL_FEEDBACK_ID" --feedback-log "$EDITORIAL_RUN/feedback.jsonl" --lessons "$EDITORIAL_RUN/lessons.jsonl"
EDITORIAL_LESSON_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n")[0])["lesson_id"])' "$EDITORIAL_RUN/lessons.jsonl")
python3 src/scribe_editorial.py approve --lesson-id "$EDITORIAL_LESSON_ID" --approval-ref fixture:demo-control --approved-by fixture_simulated --lessons "$EDITORIAL_RUN/lessons.jsonl"
python3 src/scribe_editorial.py compare --note experiments/fixtures/synthetic_note_001.json --lessons "$EDITORIAL_RUN/lessons.jsonl" --session-prefix live-control
# Para retirar la lección (agrega una versión rejected):
python3 src/scribe_editorial.py reject --lesson-id "$EDITORIAL_LESSON_ID" --lessons "$EDITORIAL_RUN/lessons.jsonl"
```

**Loop real de Carlos** · revisión y aprobación humanas sobre la misma nota
sintética, en una corrida nueva. Carlos escribe su propio comentario y rating,
revisa la candidata y ejecuta `approve` solo si la aprueba. Antes de aprobar,
sustituye `<algo>` por el identificador de su decisión L4 real y trazable.

```bash
CARLOS_RUN=$(mktemp -d /tmp/scribe-editorial-carlos-XXXXXX)
python3 src/scribe_editorial.py draft --note experiments/fixtures/synthetic_note_001.json --lessons "$CARLOS_RUN/lessons.jsonl" --session-id carlos-v1 --out "$CARLOS_RUN/draft.json"
read -r -p 'Carlos, escribe tu comentario: ' CARLOS_COMMENT
read -r -p 'Carlos, califica el borrador (1-5): ' CARLOS_RATING
python3 src/scribe_editorial.py feedback --draft "$CARLOS_RUN/draft.json" --reviewer carlos --rating "$CARLOS_RATING" --comment "$CARLOS_COMMENT" --target-facts f1 --feedback-log "$CARLOS_RUN/feedback.jsonl"
CARLOS_FEEDBACK_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n")[0])["feedback_id"])' "$CARLOS_RUN/feedback.jsonl")
python3 src/scribe_editorial.py propose --feedback "$CARLOS_FEEDBACK_ID" --feedback-log "$CARLOS_RUN/feedback.jsonl" --lessons "$CARLOS_RUN/lessons.jsonl"
CARLOS_LESSON_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n")[0])["lesson_id"])' "$CARLOS_RUN/lessons.jsonl")
# Carlos revisa la candidata y sustituye <algo> antes de ejecutar la aprobación:
python3 src/scribe_editorial.py approve --lesson-id "$CARLOS_LESSON_ID" --approved-by carlos --approval-ref 'decision-l4:<algo>' --lessons "$CARLOS_RUN/lessons.jsonl"
python3 src/scribe_editorial.py compare --note experiments/fixtures/synthetic_note_001.json --lessons "$CARLOS_RUN/lessons.jsonl" --session-prefix carlos-control
```

`--correction` es opcional. El CLI registra la declaración y **no verifica
GitHub ni autentica al humano**. Las referencias `fixture:` exigen
`fixture_simulated`. Ninguna aprobación autoriza publicar ni llama servicios.

`draft --out` crea además `<out>.note.json`; `feedback` conserva nota y borrador
en `<feedback-log>.context/`. Mantener estos archivos junto al log permite a
`propose` verificar IDs y hechos sin añadir campos a los schemas. `--feedback`
admite ID o ruta a un feedback JSON ya registrado en ese log; no acepta
feedback sin provenance. Sin `--out`, draft imprime JSON; sin `--feedback-log`,
el intake usa `./feedback.jsonl`. No se sobrescriben salidas existentes.

JSONL UTF-8, separado solo por LF, validado completo antes del append; no se
repara ni trunca. La aprobación agrega una versión y B+ registra `lesson_id@vN`;
la versión vigente rejected impide reutilizar aprobaciones anteriores. Un
snapshot aprobado importado también debe satisfacer el contrato y gate.
Un escritor secuencial, sin garantías transaccionales entre log y auxiliares;
no usar secretos, prompts internos ni datos reales. La etiqueta synthetic no
es un detector de información sensible. Salidas: 0 éxito, 1 chequeo/demo FAIL,
2 entrada/estado inválido con JSON `outcome=invalid`, sin traceback.

M2d: `python3 experiments/demo_codex_writer.py --dry-run` ejecuta el control offline; `python3 experiments/demo_codex_writer.py` usa Codex real (solo operador). Skills, eventos y salidas quedan en `/tmp`; gate fixture simulado, checker literal, N=1 por rama, sin inferencia estadística ni prueba automática de lectura de la skill.

Web V0: `python3 experiments/webapp.py --db /tmp/scribe-web.db` (puerto 8765, `--port` opcional; **127.0.0.1 only**, DB fuera del repo; Ctrl+C para cerrar).
