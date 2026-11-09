# Scribe del desarrollo · Misión 1

Esta nota registra el ciclo de implementación. Es distinta del ledger JSONL
con datos sintéticos que genera el producto; no es telemetría real de Codex.

## Evidencia del ciclo

- Builder comprobó la secuencia: V1 terminó con código 1 y `CSV_SCHEMA`,
  Scribe dedujo `;` del encabezado, V2 terminó con código 0 y total 6, y el
  control sin lección terminó con código 1.
- Tester reportó primero 15 pruebas correctas. Una regresión adicional mostró
  que una lección editada con separador permitido `,` y encabezado observado
  `producto;cantidad` llegaba a ejecutar la tarea en lugar de rechazarla.
- Causa: la validación comprobaba el tipo y la lista de separadores permitidos,
  pero no que el separador de la lección reprodujera las columnas observadas.
- Corrección: comprobar el encabezado con el separador registrado antes de
  ejecutar la tarea; rechazar la incompatibilidad con `LESSON_INCOMPATIBLE`.
- Tras la corrección, el productor reportó 16 pruebas correctas en 1.031 s y
  las seis comprobaciones de demo correctas en 0.199 s. Los ledgers de esa
  ejecución quedaron localmente en `/tmp/scribe-recovery-_qwvw7ot`.
- Durante la lectura posterior para esta nota se observó que el archivo de
  pruebas contenía solo cinco casos. Se notificó al productor sin modificarlo.
- Revisión final encontró `experiments/test_recovery_regressions.py` con 16 casos,
  incluida la regresión de una lección cuyo separador permitido no coincide con
  el encabezado. La suite final pasó los 16 tests en 1.132 s; la demo pasó sus
  seis comprobaciones en 0.206 s y `py_compile` terminó correctamente.

La comprobación de GitHub dentro del sandbox había parecido indicar una sesión
inválida. Fuera del aislamiento de red se verificaron la identidad operativa
`Quark-lab-diimenet` y el permiso de escritura, sin cambiar credenciales.

## Lecciones reutilizables

- Validar los parámetros de recuperación contra la evidencia del fallo antes
  del reintento; pertenecer a una lista permitida no demuestra compatibilidad.
- Probar con cantidades y separadores alternativos para comprobar que la suma
  y la lección se calculan, en vez de presentar un éxito prefabricado.
- Vincular una lección a la corrida, tarea y contenido de entrada, y comprobar
  el control negativo sin lección.

## Reproducción y límites

Desde la raíz del repositorio:

```bash
python3 -m unittest discover -s experiments -p 'test_*.py' -v
python3 experiments/demo.py --output-dir /tmp
```

El ledger es append-only de aplicación, sin protección WORM ni coordinación de
escritores concurrentes. Scribe aplica una regla determinista al encabezado de
una tarea sintética; esta demo no demuestra autoaprendizaje general. El producto
realiza cero llamadas a API y su costo de API es USD 0. El consumo de suscripción
Codex no está disponible y no se estima.

La revisión independiente de Hack Ops/Grok sigue pendiente. Los resultados
locales del productor no constituyen un `REVIEW: PASS` ni autorización de merge.
