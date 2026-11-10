> **Aviso de madurez:** este es un experimento de hackathon, construido en un día y medio. Hay que leerlo como una nota de laboratorio, no como un paper maduro.

En una empresa, corregir el mismo detalle en cada documento consume tiempo y atención.  
La idea de «corrige una vez» es guardar una corrección aprobada y usarla en documentos nuevos del mismo tipo.  
Al medirlo, aumentó el cumplimiento global con lección, aunque hubo retrocesos y el resultado dependió mucho del revisor.  
Es una señal para seguir probando; todavía no demuestra ahorro en una empresa ni calidad general de la IA.

## El problema real

Una cotización vuelve a salir sin vigencia; una propuesta pierde la referencia de una cifra. La persona arregla el documento, pero la siguiente entrega repite el error. La corrección queda en esa entrega, sin convertirse en una regla reutilizable.

## El invento

**Corrige una vez:** una corrección humana se vuelve lección aprobada por tipo de documento. Los documentos nuevos del mismo tipo la usan, sin reentrenar el modelo. La aprobación decide qué lección entra; una lección de otro tipo queda fuera de su alcance. En este experimento la aprobación fue simulada.

## La hipótesis

Una lección aprobada del mismo tipo aumentará el cumplimiento de requisitos críticos en documentos nuevos frente a escribir sin ella. Medimos si están los requisitos pedidos por la casa; no la calidad editorial general.

## Cómo lo probamos

Usamos documentos sintéticos de **Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)**. La lección sale del caso inicial de cada tipo; los casos retenidos sirven para medir su uso en documentos nuevos.

Las condiciones fueron **B-**, sin lección; **B+**, con lección aprobada del mismo tipo; y **C3**, con lección de otro tipo. Se publicaron **65 corridas**: 30 B-, 30 B+ y 5 C3, con **Codex 0.167** (CLI exacto 0.167.0), mediante suscripción ChatGPT, operadas por **Hack Ops** el **2026-11-10**. Cada repetición cuenta como ensayo. Esta nota usa los resultados publicados: no añade corridas ni vuelve a puntuar grabaciones.

## Resultados

Fuentes: [evaluación publicada](EVAL.md) y [resultados JSON](../experiments/results/eval_b2b.json). El **revisor estricto es el primario**; el tolerante se presenta por separado. Ambos son checkers automáticos.

| Condición | Estricto: conformes | Tasa | Wilson 95 % | Tolerante: conformes | Tasa | Wilson 95 % |
| --- | --- | --- | --- | --- | --- | --- |
| B- | 10/30 | 33.3 % | 19.2 % – 51.2 % | 24/30 | 80.0 % | 62.7 % – 90.5 % |
| B+ | 19/30 | 63.3 % | 45.5 % – 78.1 % | 30/30 | 100.0 % | 88.6 % – 100.0 % |
| C3 | 2/5 | 40.0 % | 11.8 % – 76.9 % | 4/5 | 80.0 % | 37.6 % – 96.4 % |

Prueba de signos exacta y bilateral para B- frente a B+, emparejando por tipo, caso y repetición. Los empates no entran en la prueba.

| Revisor | Mejoran | Empeoran | Empatan | p bilateral |
| --- | --- | --- | --- | --- |
| Estricto (primario) | 11 | 2 | 17 | 0.0224609375 |
| Tolerante | 6 | 0 | 24 | 0.03125 |

Por tipo, cada celda muestra **estricto → tolerante** para la misma condición:

| Tipo | B- | B+ | C3 |
| --- | --- | --- | --- |
| Cotización | 1/6 → 6/6 | 6/6 → 6/6 | 0/1 → 1/1 |
| Propuesta técnica | 0/6 → 0/6 | 5/6 → 6/6 | 0/1 → 0/1 |
| Ficha técnica | 1/6 → 6/6 | 0/6 → 6/6 | 0/1 → 1/1 |
| Reporte a cliente | 6/6 → 6/6 | 6/6 → 6/6 | 1/1 → 1/1 |
| Respuesta de soporte | 2/6 → 6/6 | 2/6 → 6/6 | 1/1 → 1/1 |

Los negativos también cuentan: con el estricto, ficha técnica cae de 1/6 en B- a 0/6 en B+; soporte y reporte no mejoran. Con el tolerante persisten los fallos de referencias junto a cifras en propuestas B- y en la propuesta C3. C3 mide cumplimiento con una lección ajena; no demuestra ausencia de regresión ni exige texto idéntico al de B-.

De los **11 fallos B+ estrictos, 11 se clasificaron como falso negativo del checker**. La etiqueta «falso negativo del checker» es automática: «falla el estricto y pasa el tolerante»; no es una revisión humana independiente. Carlos revisó los 11 casos B+ el 2026-11-10 y coincidió en lo general; eso no convierte la etiqueta en un dictamen editorial ni demuestra calidad general.

El **0/15 → 15/15 del writer de demostración determinista** prueba el mecanismo: tiene el fallo y el arreglo codificados. No mide calidad de un modelo ni sirve como referencia de superioridad frente a Codex.

## Lo que nos enseñó el revisor

El revisor tolerante se escribió después de ver estas 65 salidas y no estuvo preregistrado: es un análisis post hoc y un techo optimista; el revisor estricto sigue siendo el resultado primario.

Hay que calibrar el medidor y separar fallo del modelo de fallo del checker, al estilo UK AISI. Un regex literal puede castigar una tabla markdown que conserva el dato, un folio incluido en el asunto o «no garantizamos» por contener la palabra prohibida. Los conteos por sí solos no identifican la causa.

El tolerante admite esas formas acotadas, pero sigue exigiendo cifras, unidades y referencias junto al valor. La diferencia entre revisores exige calibrar con etiquetas humanas independientes; la coincidencia general de Carlos en los 11 casos B+ no sustituye esa calibración ni autoriza a borrar el resultado primario.

## Cómo se construyó

La **squad sintética es el método de trabajo**: Codex implementa; Antigravity y Cursor revisan por separado; Hack Ops opera; Carlos aprueba. Esa distribución de responsabilidades describe cómo construimos el experimento. No medimos si produce mejores resultados que otra forma de trabajar.

## Lo que esto NO demuestra

| Límite | Qué impide concluir |
| --- | --- |
| N pequeño | Los intervalos son anchos; falta evidencia para generalizar. |
| Un solo modelo y una versión | No sabemos si el resultado se repite con otros escritores. |
| Aprobación simulada | No se validó el flujo de aprobación humana en una empresa. |
| Fixtures y checker escritos por nosotros | La prueba puede favorecer nuestras convenciones; no acredita calidad editorial general. |
| Repeticiones no independientes | Repetir una nota no equivale a observar empresas o documentos independientes. |
| Sin significancia por tipo | Las diferencias por tipo son descriptivas. |
| Sin medir revisión cruzada entre familias | No sabemos si esa revisión mejora los documentos. |

## Qué probaríamos después

Calibrar el checker con etiquetas humanas y usar notas con datos crudos, donde el formato esperado no venga ya en el dato. Probar más escritores y familias, incluyendo una condición de revisión cruzada entre familias. Preregistrar hipótesis, criterios y análisis antes de correr.
