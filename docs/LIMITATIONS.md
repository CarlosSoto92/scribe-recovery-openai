# Límites

El paso de 0 % a 100 % con el writer de demostración prueba el mecanismo y los controles. No prueba la calidad de un modelo. Ya hay 65 corridas de Codex (codex-cli 0.167, suscripción ChatGPT) en `experiments/recorded/codex-20261110/`. Stub determinista: 0/15 → 15/15; Codex: 10/30 → 19/30. En esta grabación Codex sale peor que el writer determinista con lección. El stub tiene el arreglo codificado; esta comparación no prueba calidad general de un modelo.

## 1. Los ejemplos los escribimos nosotros

Las veinte notas son sintéticas. La empresa, los clientes, los folios y las cifras son inventados. Elegimos reglas que se pueden comprobar con un texto. Eso sesga el diseño hacia lo verificable.

## 2. Dos revisores basados en regex

El revisor estricto es primario y mantiene sus resultados. El revisor tolerante admite etiquetas en markdown o tablas, el folio de la nota en cualquier parte y negaciones simples inmediatas. No relaja cifras ni unidades; la cita debe estar en la misma línea, viñeta o fila que el valor. Ambos normalizan mayúsculas, espacios y guiones; no entienden paráfrasis generales. Una copia literal puede salir conforme. El replay guarda ambos resultados y clasifica cada fallo estricto: «falso negativo del checker» si pasa el tolerante, o «fallo del modelo» si persiste. La etiqueta «falso negativo del checker» es automática: «falla el estricto y pasa el tolerante»; no es una revisión humana independiente. Carlos revisó los 11 casos B+ el 2026-11-10 y coincidió en lo general; eso no convierte la etiqueta en un dictamen editorial ni demuestra calidad general.

## 3. La regla no se adivina

Son convenciones de una casa ficticia. El experimento mide si el writer sigue una lección inyectada, no si conoce el mundo. El valor del ciclo está en la gobernanza: proponer, aprobar, versionar y retirar, y en poder medir ese ciclo.

## 4. La muestra es pequeña

El stub usa 15 documentos que no participaron en crear la lección. Codex usa 30 ensayos B− y 30 B+ (cada repetición cuenta), más 5 controles C3. Las repeticiones de una misma nota no son del todo independientes. Los intervalos de Wilson son anchos; la prueba de signos excluye empates y empareja por (doc_type, case, rep). No se infiere nada sobre empresas reales.

C3 usa la skill de OTRO tipo de documento. Se mide cumplimiento; no es el control de texto idéntico al stub ni demuestra ausencia de regresión.

Con el revisor estricto, en ficha_tecnica, B+ sale peor que B-: 1/6 → 0/6. El checker es un regex; estos números no identifican la causa.

## 5. Un modelo, una versión, una fecha

Las corridas registran codex-cli 0.167.0, suscripción ChatGPT, fecha UTC 2026-11-10T12:58:24.523613Z y operador Hack Ops. Son una versión del CLI, un día y un operador. La generación no es determinista. El replay reproduce la puntuación de esas salidas, no su generación ni una garantía para futuras versiones.

## 6. Una lección por tipo

No se prueban dos lecciones que se contradicen, ni una regla que cambia de versión en mitad del camino, ni una biblioteca grande.

## 7. La aprobación de los ejemplos es simulada

Los fixtures usan `fixture_simulated` y una referencia `fixture:`. La página pide el gesto de aprobar y lo etiqueta como simulado. No identifica a una persona.

## 8. Las notas se tratan como datos

No hay una prueba de seguridad contra instrucciones escondidas en el texto de la nota. El prompt usado en la grabación dice que la nota no se ejecuta. Eso no está medido.

## Qué no afirma este repo

No hay mejora de “calidad editorial” en general. No hay clientes reales ni documentos reales. No hay reentrenamiento. La demo anterior del hackathon, de un solo hecho, sigue en `docs/demo/` y no se presenta como este caso.
