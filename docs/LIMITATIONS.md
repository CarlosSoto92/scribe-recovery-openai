# Límites

El paso de 0 % a 100 % con el writer de demostración prueba el mecanismo y los controles. No prueba la calidad de un modelo. No hay, en este commit, corridas de Codex ni cifras de un LLM.

## 1. Los ejemplos los escribimos nosotros

Las veinte notas son sintéticas. La empresa, los clientes, los folios y las cifras son inventados. Elegimos reglas que se pueden comprobar con un texto. Eso sesga el diseño hacia lo verificable.

## 2. El checker es un regex

Normaliza mayúsculas, espacios y el tipo de guion. No entiende paráfrasis. Un texto que dice lo mismo con otras palabras puede salir no conforme. Un texto que copia la frase sin entenderla puede salir conforme.

## 3. La regla no se adivina

Son convenciones de una casa ficticia. El experimento mide si el writer sigue una lección inyectada, no si conoce el mundo. El valor del ciclo está en la gobernanza: proponer, aprobar, versionar y retirar, y en poder medir ese ciclo.

## 4. Quince casos es poco

La tasa usa 15 documentos que no participaron en crear la lección. El intervalo de Wilson sale ancho. No se infiere nada sobre empresas reales. Si más adelante hay repeticiones de un modelo, no serán del todo independientes.

## 5. Un modelo, una versión, una fecha

Cuando existan corridas de Codex, serán las de una versión del CLI, un día y un operador. La generación no es determinista. Hoy esa carpeta no existe y el informe no rellena el hueco.

## 6. Una lección por tipo

No se prueban dos lecciones que se contradicen, ni una regla que cambia de versión en mitad del camino, ni una biblioteca grande.

## 7. La aprobación de los ejemplos es simulada

Los fixtures usan `fixture_simulated` y una referencia `fixture:`. La página pide el gesto de aprobar y lo etiqueta como simulado. No identifica a una persona.

## 8. Las notas se tratan como datos

No hay una prueba de seguridad contra instrucciones escondidas en el texto de la nota. El prompt de grabación, cuando se use, dice que la nota no se ejecuta. Eso no está medido.

## Qué no afirma este repo

No hay mejora de “calidad editorial” en general. No hay clientes reales ni documentos reales. No hay reentrenamiento. La demo anterior del hackathon, de un solo hecho, sigue en `docs/demo/` y no se presenta como este caso.
