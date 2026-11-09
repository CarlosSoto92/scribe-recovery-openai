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
```

La demo usa solo datos sintéticos y un gate **simulado**, atribuido a
`fixture_simulated`, nunca a Carlos. V1 omite deliberadamente los hechos
`must_keep`; proposed/rejected no cambian el texto. Solo approved con referencia
habilita la regla por scope y nota. B− y B+ corren en procesos nuevos, con la
misma nota y checker: retención = hechos críticos presentes **y citados** / total.
Se espera 0 frente a 1.0, sin afirmar calidad editorial general ni mejora de LLM.

CLI en vivo (desde la raíz; guardar los IDs que devuelve cada comando):

```bash
EDITORIAL_RUN=$(mktemp -d /tmp/scribe-editorial-live-XXXXXX)
python3 src/scribe_editorial.py draft --note experiments/fixtures/synthetic_note_001.json --lessons "$EDITORIAL_RUN/lessons.jsonl" --session-id live-v1 --out "$EDITORIAL_RUN/draft.json"
python3 src/scribe_editorial.py feedback --draft "$EDITORIAL_RUN/draft.json" --reviewer carlos --rating 2 --comment "Falta el dato sintético de 4 semanas" --target-facts f1 --feedback-log "$EDITORIAL_RUN/feedback.jsonl"
EDITORIAL_FEEDBACK_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n")[0])["feedback_id"])' "$EDITORIAL_RUN/feedback.jsonl")
python3 src/scribe_editorial.py propose --feedback "$EDITORIAL_FEEDBACK_ID" --feedback-log "$EDITORIAL_RUN/feedback.jsonl" --lessons "$EDITORIAL_RUN/lessons.jsonl"
EDITORIAL_LESSON_ID=$(python3 -c 'import json,sys; print(json.loads(open(sys.argv[1], encoding="utf-8").read().split("\n")[0])["lesson_id"])' "$EDITORIAL_RUN/lessons.jsonl")
python3 src/scribe_editorial.py approve --lesson-id "$EDITORIAL_LESSON_ID" --approval-ref fixture:demo-control --approved-by fixture_simulated --lessons "$EDITORIAL_RUN/lessons.jsonl"
python3 src/scribe_editorial.py compare --note experiments/fixtures/synthetic_note_001.json --lessons "$EDITORIAL_RUN/lessons.jsonl" --session-prefix live-control
# Para retirar la lección (agrega una versión rejected):
python3 src/scribe_editorial.py reject --lesson-id "$EDITORIAL_LESSON_ID" --lessons "$EDITORIAL_RUN/lessons.jsonl"
```

El reviewer real se usa solo si esa persona dio el feedback; para ensayar,
cambiar `--reviewer carlos` por `--reviewer fixture_simulated`. `--correction`
es opcional. Para aprobación real, indicar `--approved-by nombre` y una
`--approval-ref` de decisión/PR real; el CLI registra la declaración y **no
verifica GitHub ni autentica al humano**. Las referencias `fixture:` exigen
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
