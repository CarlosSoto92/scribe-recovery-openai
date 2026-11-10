# Evaluación B2B

Cumplimiento de requisitos verificables en documentos ficticios de Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA). No mide calidad editorial general.

## Diseño

Veinte notas sintéticas: cinco tipos de documento por cuatro casos. La lección de cada tipo sale del caso 1, con el gate `fixture_simulated`. La tasa usa solo los 15 casos retenidos (casos 2 a 4).

Condiciones: **B−** sin lección, **B+** con la lección approved de su tipo, **C1** proposed, **C2** rejected, **C3** lección de otro tipo, **C4** solo lecciones de otros tipos.

Métrica primaria: documentos que cumplen todos sus requisitos críticos. Secundaria: promedio de requisitos cumplidos. Regresión: hechos no críticos conservados, cero frases prohibidas nuevas y longitud ±25 %.

El intervalo es de Wilson al 95 %. La prueba de signos es exacta y bilateral; los empates no entran. Con n = 15 el intervalo es ancho. Estas cuentas describen al writer de demostración, no a un modelo.

## Cómo reproducir

```bash
python3 -m unittest discover -s experiments
python3 experiments/eval_b2b.py --writer stub
python3 experiments/record_codex_runs.py --dry-run --controls
python3 experiments/eval_b2b.py --replay experiments/recorded/codex-20261110
```

La tercera orden solo muestra un plan. El replay puntúa las salidas ya grabadas sin red y actualiza este informe y el JSON. Regenerar el stub conserva las corridas reales.

## Resultados del writer de demostración

Etiqueta: **Writer de demostración (determinista)**. El 0 % → 100 % del stub prueba el mecanismo y los controles, no la calidad de un LLM.

| Condición | Documentos conformes | Intervalo de Wilson 95 % | Requisitos cumplidos |
| --- | --- | --- | --- |
| Sin lección | 0/15 | 0.0 % – 20.4 % | 0.0 % |
| Con lección | 15/15 | 79.6 % – 100.0 % | 100.0 % |

Pares que mejoran: 15. Pares que empeoran: 0. Empates: 0. p bilateral: 0.00006103515625.

Regresión B+ frente a B−: dentro de la regla. Razón de longitud entre 0.9880 y 1.0781.

| Tipo | Sin lección | Con lección | Wilson sin lección | Wilson con lección |
| --- | --- | --- | --- | --- |
| Cotización | 0/3 | 3/3 | 0.0 % – 56.1 % | 43.9 % – 100.0 % |
| Propuesta técnica | 0/3 | 3/3 | 0.0 % – 56.1 % | 43.9 % – 100.0 % |
| Ficha técnica | 0/3 | 3/3 | 0.0 % – 56.1 % | 43.9 % – 100.0 % |
| Reporte a cliente | 0/3 | 3/3 | 0.0 % – 56.1 % | 43.9 % – 100.0 % |
| Respuesta de soporte | 0/3 | 3/3 | 0.0 % – 56.1 % | 43.9 % – 100.0 % |

Caso 1, aparte, sin entrar en la tasa: sin lección 0/5, con lección 5/5.

## Controles

| Control | Esperado | Resultado |
| --- | --- | --- |
| C1 | Lección en proposed: el texto queda igual que sin lección. | pasa (15/15) |
| C2 | Lección rechazada: el texto queda igual que sin lección. | pasa (15/15) |
| C3 | Lección approved de otro tipo: sin efecto y sin regresión. | pasa (15/15) |
| C4 | Solo hay lecciones de otros tipos: el documento no cambia. | pasa (15/15) |

## Fallos con el texto del writer

### Cotización · caso 2 · sin lección

- Falta el texto de la nota «Vigencia: 15 días naturales».
- Falta el texto de la nota «Pago: 50 % anticipo, 50 % contra entrega».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 02 · compras@cliente-demo-02.example
Documento: Cotización · b2b-cotizacion-02

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Partida | Bomba centrífuga de demostración | 1 | 18,600.00 MXN
Partida | Sello mecánico de demostración | 2 | 1,880.00 MXN
Total | 20,480.00 MXN
Entrega estimada en la planta del cliente ficticio, sin almacenaje ni obra civil.
```

### Cotización · caso 3 · sin lección

- Falta el texto de la nota «Vigencia: 15 días naturales».
- Falta el texto de la nota «Pago: 50 % anticipo, 50 % contra entrega».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 03 · compras@cliente-demo-03.example
Documento: Cotización · b2b-cotizacion-03

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Partida | Válvula de bola de 1 pulgada | 6 | 4,560.00 MXN
Partida | Brida de demostración | 6 | 1,260.00 MXN
Total | 5,820.00 MXN
Entrega estimada en la planta del cliente ficticio, sin almacenaje ni obra civil.
```

### Cotización · caso 4 · sin lección

- Falta el texto de la nota «Vigencia: 15 días naturales».
- Falta el texto de la nota «Pago: 50 % anticipo, 50 % contra entrega».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 04 · compras@cliente-demo-04.example
Documento: Cotización · b2b-cotizacion-04

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Partida | Actuador neumático de demostración | 2 | 14,900.00 MXN
Partida | Kit de montaje de demostración | 2 | 1,060.00 MXN
Total | 15,960.00 MXN
Entrega estimada en la planta del cliente ficticio, sin almacenaje ni obra civil.
```

### Propuesta técnica · caso 2 · sin lección

- Falta la referencia (Ref. FT-210) junto a «Caudal nominal: 45 m³/h».
- Falta la referencia (Ref. FT-211) junto a «Presión de descarga: 6 bar».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 02 · compras@cliente-demo-02.example
Documento: Propuesta técnica · b2b-propuesta_tecnica-02

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Alcance: bomba de menor caudal para un circuito de demostración. Queda fuera el tablero.
Condición de la propuesta ficticia: precios y plazos no están incluidos; este texto solo describe el equipo.
Caudal nominal: 45 m³/h
Presión de descarga: 6 bar
```

### Propuesta técnica · caso 3 · sin lección

- Falta la referencia (Ref. FT-330) junto a «Par de operación: 40 N·m».
- Falta la referencia (Ref. FT-331) junto a «Ciclos de prueba: 5000».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 03 · compras@cliente-demo-03.example
Documento: Propuesta técnica · b2b-propuesta_tecnica-03

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Alcance: válvula de demostración y su actuador. Queda fuera la tubería.
Condición de la propuesta ficticia: precios y plazos no están incluidos; este texto solo describe el equipo.
Par de operación: 40 N·m
Ciclos de prueba: 5000
```

### Propuesta técnica · caso 4 · sin lección

- Falta la referencia (Ref. FT-440) junto a «Eficiencia hidráulica: 72 %».
- Falta la referencia (Ref. FT-441) junto a «NPSH requerido: 3.2 m».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 04 · compras@cliente-demo-04.example
Documento: Propuesta técnica · b2b-propuesta_tecnica-04

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Alcance: comparación de catálogo ficticio. Queda fuera la instalación.
Condición de la propuesta ficticia: precios y plazos no están incluidos; este texto solo describe el equipo.
Eficiencia hidráulica: 72 %
NPSH requerido: 3.2 m
```

### Ficha técnica · caso 2 · sin lección

- Falta el texto de la nota «Presión de trabajo: 16 bar (232 psi)».
- Falta el texto de la nota «Temperatura máxima: 120 °C».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 02 · compras@cliente-demo-02.example
Documento: Ficha técnica · b2b-ficha_tecnica-02

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Equipo: Válvula de globo serie DEMO-16, para agua limpia en un circuito de demostración.
Conexión: brida de demostración. Este dato no es un certificado ni una norma citada.
Presión de trabajo: 232 psi
Temperatura máxima: 120
```

### Ficha técnica · caso 3 · sin lección

- Falta el texto de la nota «Presión de trabajo: 6 bar (87 psi)».
- Falta el texto de la nota «Temperatura máxima: 40 °C».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 03 · compras@cliente-demo-03.example
Documento: Ficha técnica · b2b-ficha_tecnica-03

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Equipo: Sello mecánico serie DEMO-06, para agua limpia en un circuito de demostración.
Conexión: brida de demostración. Este dato no es un certificado ni una norma citada.
Presión de trabajo: 87 psi
Temperatura máxima: 40
```

### Ficha técnica · caso 4 · sin lección

- Falta el texto de la nota «Presión de trabajo: 25 bar (363 psi)».
- Falta el texto de la nota «Temperatura máxima: 150 °C».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 04 · compras@cliente-demo-04.example
Documento: Ficha técnica · b2b-ficha_tecnica-04

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Equipo: Actuador serie DEMO-25, para agua limpia en un circuito de demostración.
Conexión: brida de demostración. Este dato no es un certificado ni una norma citada.
Presión de trabajo: 363 psi
Temperatura máxima: 150
```

### Reporte a cliente · caso 2 · sin lección

- Falta el texto de la nota «Siguiente paso: Mesa Técnica Demo · 2026-11-23».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 02 · compras@cliente-demo-02.example
Documento: Reporte a cliente · b2b-reporte_cliente-02

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Visita de demostración al cliente ficticio. Se revisó el equipo instalado y se dejó constancia de lo observado.
Hallazgo: la válvula de demostración cierra, con un goteo en el empaque que conviene observar.
```

### Reporte a cliente · caso 3 · sin lección

- Falta el texto de la nota «Siguiente paso: Coordinación Demo · 2026-11-30».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 03 · compras@cliente-demo-03.example
Documento: Reporte a cliente · b2b-reporte_cliente-03

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Visita de demostración al cliente ficticio. Se revisó el equipo instalado y se dejó constancia de lo observado.
Hallazgo: el sello de demostración se mantiene seco durante la visita, y conviene repetir la observación.
```

### Reporte a cliente · caso 4 · sin lección

- Falta el texto de la nota «Siguiente paso: Mesa Técnica Demo · 2026-12-07».

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 04 · compras@cliente-demo-04.example
Documento: Reporte a cliente · b2b-reporte_cliente-04

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Visita de demostración al cliente ficticio. Se revisó el equipo instalado y se dejó constancia de lo observado.
Hallazgo: el actuador de demostración responde al aire de prueba, con una carrera completa.
```

### Respuesta de soporte · caso 2 · sin lección

- Falta el texto de la nota «Folio de soporte: SOP-1904».
- Aparece la frase prohibida «garantizamos».
- Aparece la frase prohibida «solución definitiva».
- Falta el folio SOP-nnnn de la nota.

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 02 · compras@cliente-demo-02.example
Documento: Respuesta de soporte · b2b-respuesta_soporte-02

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Síntoma reportado: goteo en el sello de la bomba de demostración.
Lectura de la mesa: hace falta un diagnóstico en sitio. Este texto no promete un resultado ni sustituye una orden de servicio.
Garantizamos una solución definitiva.
```

### Respuesta de soporte · caso 3 · sin lección

- Falta el texto de la nota «Folio de soporte: SOP-2033».
- Aparece la frase prohibida «garantizamos».
- Aparece la frase prohibida «solución definitiva».
- Falta el folio SOP-nnnn de la nota.

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 03 · compras@cliente-demo-03.example
Documento: Respuesta de soporte · b2b-respuesta_soporte-03

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Síntoma reportado: la válvula de demostración no termina de cerrar.
Lectura de la mesa: hace falta un diagnóstico en sitio. Este texto no promete un resultado ni sustituye una orden de servicio.
Garantizamos una solución definitiva.
```

### Respuesta de soporte · caso 4 · sin lección

- Falta el texto de la nota «Folio de soporte: SOP-2180».
- Aparece la frase prohibida «garantizamos».
- Aparece la frase prohibida «solución definitiva».
- Falta el folio SOP-nnnn de la nota.

```text
Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)
RFC FICT000101AAA · ventas@valvulas-ejemplo.example · +52 000 000 0000
Ciudad Ejemplo del Bajío (dirección ficticia)
Cliente: Cliente Demo 04 · compras@cliente-demo-04.example
Documento: Respuesta de soporte · b2b-respuesta_soporte-04

Aviso de documento ficticio: este texto lo preparó Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA) solo para mostrar una corrección interna. No es una oferta, un dictamen ni una promesa hacia un tercero.
Contexto de la casa: el ejemplo usa clientes, equipos y ciudades inventados. Sirve para repetir la misma corrección en documentos distintos, sin datos de una operación real.
Síntoma reportado: el actuador de demostración no completa la carrera.
Lectura de la mesa: hace falta un diagnóstico en sitio. Este texto no promete un resultado ni sustituye una orden de servicio.
Garantizamos una solución definitiva.
```

Con la lección approved, los 15 casos retenidos cumplen. Eso lo hace el writer de demostración, que tiene la corrección codificada. No es un resultado de un modelo.

## Modelo real

**Codex (codex-cli 0.167, suscripción ChatGPT)**. CLI exacto: 0.167.0. N = 65 corridas; cada repetición cuenta como un ensayo.

Fecha UTC: 2026-11-10T12:58:24.523613Z. Operador: Hack Ops. Fuente: `experiments/recorded/codex-20261110/`.

| Condición | Conformes | Tasa | Wilson 95 % |
| --- | --- | --- | --- |
| B- | 10/30 | 33.3 % | 19.2 % – 51.2 % |
| B+ | 19/30 | 63.3 % | 45.5 % – 78.1 % |
| C3 | 2/5 | 40.0 % | 11.8 % – 76.9 % |

Signos bilaterales, pares por (doc_type, case, rep): 11 mejoran, 2 empeoran y 17 empatan. Los empates se excluyen: n = 13, p bilateral = 0.0224609375.

C3 usa la skill de OTRO tipo de documento. Se mide cumplimiento; no es el control de texto idéntico al stub ni demuestra ausencia de regresión.

Stub determinista: 0/15 → 15/15; Codex: 10/30 → 19/30. En esta grabación Codex sale peor que el writer determinista con lección. El stub tiene el arreglo codificado; esta comparación no prueba calidad general de un modelo.

| Tipo | B- | B+ |
| --- | --- | --- |
| Cotización | 1/6 | 6/6 |
| Propuesta técnica | 0/6 | 5/6 |
| Ficha técnica | 1/6 | 0/6 |
| Reporte a cliente | 6/6 | 6/6 |
| Respuesta de soporte | 2/6 | 2/6 |

En ficha_tecnica, B+ sale peor que B-: 1/6 → 0/6. El checker es un regex; estos números no identifican la causa.

Muestra pequeña: una versión del CLI, un día y un operador. Generación no determinista; las repeticiones de una misma nota no son del todo independientes. El checker es un regex y no mide calidad editorial general.

## Límites honestos

El stub es una prueba de mecanismo y de los controles, no evidencia de calidad de un LLM. Los fixtures son sintéticos y los escribimos nosotros. El checker es un regex: una paráfrasis correcta puede salir no conforme, y una copia literal puede salir conforme. Las reglas son convenciones de la casa, no conocimiento del mundo. n = 15 es pequeño. La aprobación humana de estas lecciones es simulada (`fixture:`). El detalle está en `docs/LIMITATIONS.md`.
