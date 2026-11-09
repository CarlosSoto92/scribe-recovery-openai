# VISION V0 — Scribe/Recovery con primer caso editorial LinkedIn

**Estado:** propuesta de arquitectura para revisión L4 + Hack Ops; no es código ejecutado ni autorización T2.  
**Corte:** 2026-11-09, hackathon. **Base Git:** main 8e09bd4 (PR #1 integrado).  
**Responsable de esta visión:** CTO Sintético. **Operación:** Grok/Hack Ops dirige Codex. **Merge y producto:** Carlos/L4.  
**Autoridad:** [Issue #7](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/7) (decisión de L4 + [RELEASE condicionado CTO](https://github.com/CarlosSoto92/scribe-recovery-openai/issues/7#issuecomment-6751242996)). [PR #4](https://github.com/CarlosSoto92/scribe-recovery-openai/pull/4) es el antecedente Fase 0 CSV, no la V0 editorial.

## 1. Tesis arquitectónica y lectura C-level

**Qué buscamos:** que un asistente reciba una investigación trazable, redacte un **borrador** y aprenda una **corrección aprobada por Carlos** para aplicarla en una **ejecución nueva**, sin reentrenar un modelo, sin publicar automáticamente y sin mover IP privada al repositorio público.

- **Fuerte (COMPROBADO):** el PR #4 construyó un reintento determinista con ledger JSONL, control negativo y pruebas; Cursor/Grok reprodujo 20 tests y la demo en Python 3.12.3 en el SHA 7c34712. La construcción con Codex vía codex exec, worktree exclusivo, push gobernado y revisión cruzada ya produjo evidencia trazable.
- **Fuerte (INFERIDO):** un editor humano ofrece señal correctiva más útil y auditable que una supuesta autocorrección sin criterio externo. El caso editorial permite ver la lección en un borrador, sin publicar en LinkedIn.
- **Débil (COMPROBADO):** PR #4 no transfiere lecciones entre distintos run_id; el ledger es append-only de aplicación, sin locking/transacción; la demo solo repara CSV_SCHEMA. No hay todavía DALI interno funcional demostrado en este repo ni integración con Sherlock.
- **Débil (HIPÓTESIS):** una corrección editorial puede no mejorar la siguiente generación de un LLM de forma estable. «Mejoró» requiere contraste entre pares y criterio de evaluación prefijado, no solo un texto que parezca mejor.
- **Restricción comercial e IP:** la demostración pública **no contiene prompts, System Card, estilo privado, datos de clientes ni arquitectura reservada de DALI**. Se puede mencionar DALI como antecedente interno o rol externo, pero no afirmar su implementación pública.

**Postura:** construir un **núcleo de evidencias y aprobación**; usar un generador de borradores como adaptador sustituible. No construir otra plataforma de agentes. La V0 debe enseñar el contrato de datos y demostrar causalidad, no prometer autonomía general.

## 2. Contexto de extremo a extremo

~~~mermaid
flowchart LR
    S["Sherlock / Radar Stack / Evidencia IA<br/>investigación: FUTURO"] --> R[("Repositorio de hallazgos<br/>fuentes y notas autorizadas")]
    R --> D["DALI privado / adaptador de redacción<br/>FUERA del repo público"]
    D --> B["Borrador de post<br/>nunca se publica solo"]
    B --> C["Carlos · editor humano<br/>corrige y califica"]
    C --> F["Feedback estructurado"]
    F --> SR["Scribe/Recovery público<br/>lección candidata"]
    SR --> G{"Gate humano<br/>¿aprobar lección?"}
    G -->|No| X["Rechazada / pendiente<br/>no se aplica"]
    G -->|Sí| L[("Memoria de lecciones aprobadas<br/>versionada y recuperable")]
    L -->|siguiente sesión, lectura explícita| D
~~~

**Límite del diagrama:** las flechas Sherlock→repo y DALI privado→borrador son objetivo de integración. Para la demo pública se usan **notas sintéticas o una fuente pública seleccionada y validada**, y un **escritor genérico** reemplazable. No se habilitan repositorios internos ni LinkedIn API.

## 3. Componentes mínimos, almacenes y contratos

~~~mermaid
flowchart TB
    subgraph PUBLIC["Repo público — Scribe/Recovery V0 (Python stdlib)"]
        I["Importador de nota<br/>valida origen, ID y claims"]
        W["Writer Adapter (interfaz)<br/>draft(brief, approved_lessons)"]
        V["Validador determinista<br/>factos y citas"]
        FB["Feedback Intake<br/>comentario/rating humano"]
        P["Scribe Candidate<br/>lesson candidate"]
        A["Approval Gate<br/>proposed / approved / rejected"]
        M[("Lecciones JSONL<br/>version + hash + scope")]
        E[("Evidencia y evaluación<br/>sesiones B+ y B-")]
        I --> W --> V --> FB --> P --> A
        A -->|solo approved| M --> W
        V --> E
        FB --> E
    end
    O["Codex exec --json<br/>harness externo opcional"] -.->|adaptador, eventos sanitizados| W
    H["Carlos/L4<br/>aprobación real vía PR"] --> A
    S["DALI/Sherlock privados<br/>nunca en repo público"] -.->|integración futura, por contrato| I
~~~

### Contrato común

Cada documento tiene **schema_version**, ID estable, **source/provenance**, UTC timestamp, **run_id/session_id** cuando aplica, y datos **sintéticos por defecto**. Cada evento es una línea JSON válida terminada en \n; los JSONL son **append-only a nivel de aplicación, NO WORM/ACID**. Prohibir tokens, cookies, perfiles de terceros, prompts internos y datos de clientes.

**A. Investigación (research_note.v1.json)** — ENTRADA de Sherlock o fixture; una nota por fuente/claim, no asumir feed real.

~~~json
{
  "schema_version": "research_note.v1",
  "note_id": "synthetic-note-001",
  "source": {"type": "synthetic", "url": null, "retrieved_at": "2026-11-09T21:00:00Z"},
  "topic": "ejemplo de adopción de IA",
  "facts": [
    {"fact_id": "f1", "text": "El piloto sintético duró 4 semanas", "must_keep": true}
  ],
  "limits": ["No presentar cifras sintéticas como hechos de una empresa real"]
}
~~~

Al usar investigación pública real: URL verificable, fecha de consulta y fragmento propio/parafraseado; no redistribuir materiales privados o textos extensos protegidos.

**B. Borrador (draft.v1.json)** — SALIDA del escritor genérico. La referencia a fuente es verificable; jamás publica.

~~~json
{
  "schema_version": "draft.v1",
  "draft_id": "draft-001",
  "session_id": "session-A",
  "note_id": "synthetic-note-001",
  "applied_lesson_ids": [],
  "text": "Un piloto de IA muestra oportunidades para mejorar procesos.",
  "fact_refs": [],
  "status": "needs_human_review"
}
~~~

**C. Corrección humana (feedback.v1.jsonl)** — señal editorial; si es simulada debe etiquetarse como tal, nunca atribuirse a Carlos.

~~~json
{
  "schema_version": "feedback.v1",
  "feedback_id": "fb-001",
  "draft_id": "draft-001",
  "reviewer": "fixture_simulated",
  "rating": 2,
  "rating_scale": "1-5",
  "comment": "Omitiste la duración del piloto",
  "target_fact_ids": ["f1"],
  "correction": "Conservar el dato de 4 semanas y atribuirlo a la nota",
  "created_at": "2026-11-09T21:01:00Z"
}
~~~

**D. Lección (lesson.v1.jsonl)** — propuesta **NO activa** hasta ratificación humana por PR. Puede tener historial de cambios; una nueva versión no borra la anterior.

~~~json
{
  "schema_version": "lesson.v1",
  "lesson_id": "lesson-001",
  "version": 1,
  "source_feedback_id": "fb-001",
  "scope": {"task": "linkedin_draft", "rule_type": "required_fact"},
  "trigger": "La nota contiene un fact con must_keep=true",
  "rule": "Incluir el dato crítico y mantener su referencia verificable",
  "evidence": {"note_id": "synthetic-note-001", "fact_ids": ["f1"]},
  "state": "proposed",
  "approved_by": null,
  "approval_ref": null,
  "created_at": "2026-11-09T21:02:00Z"
}
~~~

**Regla de activación:** solo usar versión con state=approved **y referencia de aprobación humana real** (PR merge/decisión L4 trazable). Antes de eso, la lección permanece proposed. En la demo, un ejemplo con estado approved artificial se declara explícitamente **fixture de control**, no aprobación real de Carlos. No editar automáticamente AGENTS.md, .agents/skills/, configuraciones Codex ni rama main.

### Integridad mínima
- IDs y referencias cruzadas comprobados; UTF-8 / JSONL parseable, separación por \n, timestamps UTC, datos sintéticos.
- El generador recibe solo **approved_lessons** filtradas por scope/tarea; las candidatas y rechazadas quedan excluidas.
- Evidencia de entrada + salida + SHA o identificador de versión de lección; al cambiar una aprobación se conserva rastro de qué versión se aplicó.
- Las pruebas usan archivos temporales, un escritor secuencial y no prometen atomicidad entre procesos.

## 4. Secuencia de un ciclo completo V1 → revisión → V2

~~~mermaid
sequenceDiagram
    autonumber
    actor Editor as Carlos / Editor
    participant H as Grok / Harness Codex
    participant W as Writer Adapter
    participant S as Scribe/Recovery
    participant G as Gate por PR
    participant M as Memoria JSONL
    participant E as Evaluador
    H->>W: Sesión A: nota + approved_lessons=[]
    W-->>H: draft V1 + source_refs
    H->>Editor: Presentar borrador para revisión
    Editor->>S: Feedback: dato crítico omitido + rating
    S->>G: lesson_candidate (proposed)
    G->>Editor: PR de aprobación / rechazo
    alt Aprobación humana real registrada
        Editor-->>G: Aceptar cambio
        G->>M: Promover versión a approved
    else Pendiente o rechazada
        G-->>H: No habilitar lección
    end
    par Control B- · sesión limpia
        H->>W: Nueva sesión sin lección
        W-->>E: draft B- + evidencia
    and Tratamiento B+ · sesión limpia
        H->>M: Leer solo versión approved
        M-->>H: lesson_id + regla + provenance
        H->>W: Nueva sesión con lección
        W-->>E: draft B+ + evidencia
    end
    E-->>Editor: Contraste de dato conservado, citas y rating
~~~

**Condición causal:** B+ y B− parten del **mismo brief y criterios**, procesos separados y mismo writer/runtime; única diferencia controlada es el contexto de la lección aprobada. La ejecución de un LLM puede variar: reportar número de muestras y resultados observados, **sin garantía de mejora por una sola corrida**. Controles deterministas pueden demostrar que la lección fue cargada y que un dato obligatorio se preservó, pero no prueban calidad creativa general.

## 5. Loop de mejora inspirado en Hermes, con límite humano

1. **Observa** salida, causa y feedback durante o al terminar la tarea (errores, correcciones, calificación humana). La ausencia de feedback no implica aprobación.
2. **Propone** una regla corta: trigger, acción, contexto, evidencia, alcance, versión y qué prueba detecta regresión.
3. **Evalúa** en fixture + control negativo, sin aplicar la candidata a sesiones normales.
4. **Somete al humano** como PR; solo revisión/merge L4 habilita la lección. No hay auto-merge ni skill que se instale sola.
5. **Recupera** la versión aprobada desde disco en proceso nuevo y compara resultados; una lección que no mejora o tiene efecto adverso se marca para retiro posterior, sin borrar historial.

Dos memorias **conceptuales**: **hechos/preferencias breves** (dados con consentimiento y caducidad) y **procedimientos verificables** (skills/guías aprobadas). Para V0 pública basta un **registro JSONL único con scope y estado**; no construir motor de memoria, schedulers ni auto-revisión background. Referencia de patrones: [Hermes Agent skills](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills), **sin reutilizar código ni asumir equivalencia**.

## 6. Vista rápida para Carlos (mockup de flujo, no interfaz construida)

~~~text
┌──────────────────────────────────────────────────────────────────────┐
│  SCRIBE / RECOVERY — V0, revisión humana · demo local                │
├──────────────────────┬───────────────────────────────────────────────┤
│ INVESTIGACIÓN        │ BORRADOR A · SESIÓN 1                         │
│ Nota: piloto 4       │ "Un piloto de IA muestra oportunidades..."   │
│ semanas (SINTÉTICO)  │ Facto obligatorio f1: OMITIDO               │
│ Fuente: fixture      │ Rating: 2/5 (fixture, no Carlos)             │
├──────────────────────┴───────────────────────────────────────────────┤
│ SCRIBE: PROPONE «conservar f1 y fuente» → [PENDIENTE de L4/PR]       │
│ Solo cuando esté APPROVED: sesiones nuevas B+ / B-                  │
├──────────────────────────────────────────────────────────────────────┤
│ B- SIN LECCIÓN                │ B+ CON LECCIÓN aprobada              │
│ f1: OMITIDO                   │ f1: PRESENTE + referencia           │
│ check: FAIL                   │ check: PASS                         │
└──────────────────────────────────────────────────────────────────────┘
~~~

Lo esencial para la demostración es la **comparación antes/después y control sin lección**. No crear webapp para dibujar este panel: la consola + un guion de 3 minutos es suficiente.

## 7. Alcance y reloj de la V0 · meta del hackathon antes de 17:00 CDMX

**La hora es un límite de priorización, no un compromiso de entrega sin medir.** El cierre de PR #4, el preflight y el gate L4 pueden consumir margen. Separar lo imprescindible de la aspiración.

| Nivel | Qué debe verse | Evidencia / parada |
|---|---|---|
| **P0 obligatorio** | PR #4 aprobado por CTO, merge L4 y smoke en main. Núcleo del proyecto en estado verificable. | EXACT_HEAD, SHA de main, 20 tests + demo reproducidos. |
| **P1 V0 demostrable** | Nota **sintética** → borrador básico → feedback explícitamente simulado o humano real → lección propuesta → control de aprobación → sesiones B- / B+ desde procesos limpios con regla persistida. | PR M2, pruebas positiva/negativa, evidencia de archivo leído por B+. Si falta aprobación humana real, declarar «gate simulado» y **NO** afirmar que Carlos aprobó. |
| **P2 valioso si hay margen** | Una ejecución real de escritor mediante codex exec --json con entrada saneada y trazas guardadas fuera del repo; revisión real por Carlos y demo editorial de 3 minutos. | Versión CLI, sesión/uso, salida sanitisada, resultados observados, no métricas inventadas. |
| **Después de 17:00 / siguiente ciclo** | Conexión a Sherlock/Radar/Evidencia IA, DALI privado, iteraciones de voz editorial, skills versionadas, pruebas de robustez multi-caso, métricas longitudinales, seguimiento Lázaro. | Nuevos RELEASE y superficies privadas, autorización humana según riesgo. |

**Criterio de parada:** si falta cierre PR #4, ownership o autorización humana, entregar P0 + diseño M2 + pruebas unitarias; no fabricar una demo de mejora que no existe. Ninguna publicación automática o scraping de LinkedIn.

## 8. Medición honesta de «mejoró»

| Métrica | Definición auditable | V0 |
|---|---|---|
| **Retención de hechos críticos** | must_keep presentes y referenciados / must_keep totales; comparar B− vs B+. | Primaria, calculable |
| **Fidelidad de fuentes** | claims verificables con referencia correcta / claims verificables totales; atribuir según nota. | Primaria; revisión humana si hay ambigüedad |
| **Aprobado sin retrabajo** | borradores aceptados por Carlos en primera revisión / borradores revisados. | POR_VALIDAR, requiere muestras reales |
| **Rating humano** | escala 1–5 fijada, con comentario y cambio por pareja comparable. | Señal humana, no prueba automática |
| **Lección realmente usada** | B+ registra lesson_id/version y evidencia de regla aplicada; B− no la carga. | Primaria causal |
| **Costo/tiempo de sesión** | duración, Codex CLI/versión, número de intervenciones y uso disponible; sin inferir precio de créditos. | Secundaria operativa |

**PASS experimental mínimo:** mismo brief y verificador, B− omite el fact_id crítico y B+ lo conserva **y cita** luego de cargar explícitamente una lección aprobada desde disco; una candidata no aprobada **no** cambia B+. Para lenguaje natural no prometer un efecto determinista de modelo. Con una sola nota no afirmar eficacia estadística ni mejora comercial.

## 9. Riesgos, STOP y frontera público/IP

| Riesgo | Control / decisión |
|---|---|
| **IP DiimeNET o de clientes en público** | Repo público SOLO mecanismo, contratos sintéticos y patrones genéricos. **Nunca** System Card, prompts, memoria personal, tono interno DALI, secretos, investigaciones privadas, datos de clientes. DALI y Sherlock reales solo mediante repositorio/superficie privados explícitamente designados por L4. |
| **Falsa mejora** | Control B−, sesión limpia, misma nota y rúbrica, trazas, resultado observable, etiquetar fixtures simuladas, revisión humana. |
| **Contaminación de contexto** | Session IDs distintos; nuevas invocaciones; skills candidatas no cargadas ni instaladas; no compartir chat oculto. |
| **Colisión Codex/host** | Un escritor + worktree exclusivo + LOCKED_PATHS + git status + dueño; Grok despacha, Antigravity verifica nodo, Cursor revisa, CTO valida, L4 mergea. |
| **Inyección en investigación** | Notas como **datos no confiables**, no instrucciones; no ejecutar comandos del texto investigado ni permitir tool access de la nota. |
| **Errores de ledger** | Un escritor, JSONL validable, no WORM/transaccional; sin tareas con efectos reales ni simultaneidad. |
| **Coste/servicios/privacidad** | Fase 0 autenticación Codex existente; sin API OpenAI propia, secretos, conectores o acciones T2. La suscripción tiene cuota, no declarar «tokens ilimitados» ni costo total cero. |
| **Publicación accidental** | Solo borradores; ningún acceso LinkedIn, DM, likes, programación o navegación sobre cuentas. |
| **Plazo 17:00** | Reutilizar Python stdlib y PR #4; no interfaz, DB, scheduler, infra ni integración real de cuatro agentes. |

## 10. Misiones técnicas pequeñas para Grok → Codex

**Precondición común:** PR #4 integrado en main por L4; smoke PASS; nueva rama/worktree exclusivo y CLAIM con SESSION_ID, ISSUE, WORKTREE_PATH, BRANCH, START_PIN, LOCKED_PATHS, OWNER. Un solo escritor Codex en LT-01. **Cada misión necesita RELEASE CTO de superficie si sale de Issue #7; Grok puede descomponer, no ampliar límites.** Revisión Cursor/Grok por SHA, merge L4.

| Orden | Misión/usuario | Tier / LOCKED_PATHS | Activo y aceptación | Prueba verificable |
|---|---|---|---|---|
| **M2a** | *Contrato editorial genérico* (harness) | **T1**, src/, experiments/ | Parsear nota, borrador, feedback y lesson candidate sintéticos; schemas/versiones, sin fuentes internas. | unittest de validación, IDs, referencias, Unicode y rechazo de entrada malformada. |
| **M2b** | *Memoria con aprobación humana* (Carlos/editor) | **T1**, src/, experiments/ | Candidata no afecta comportamiento; solo aprobación real trazable o fixture claramente etiquetada; cargar lección por scope en sesión nueva. No instalar skills. | positivos/negativos proposed/rejected/approved, prueba de disco en 2 procesos, evidencia de version/hash. |
| **M2c** | *Demostración causal* (jurado) | **T1**, src/, experiments/ | Misma nota y rúbrica: B− no conserva dato, B+ tras lectura de approved sí; output CLI + tiempo; no publicación. | demo reproducible, control negativo y comparación de JSON output. |
| **M2d** | *Adaptador Codex exec* (Grok/harness) | **T1 condicionado**, src/, experiments/ | Probar con suscripción, sandbox/read-only adecuado, prompts sanitizados; registrar eventos JSONL reales sin volcarlos al repo público. | ejecución controlada, evidence run_id/version y review externo; si CLI exige API/secreto: STOP. |
| **M2e** | *DALI/Sherlock real* (Carlos) | **NO RELEASE público**; repo privado POR_DESIGNAR | Integración editorial interna, System Card y sourcing autorizados; sin contactos LinkedIn. | decisión L4 y revisión de superficie/IP antes de cualquier código. |
| **M2f** | *Narrativa/documentación* (Hack Ops) | **T1 docs/ vía PR separado**, no invadir productor | README con límites y comando; corregir «siguiente corrida», actualizar DECISIONS #2 y guion honesto de 3 min. | enlaces, claims, comandos desde main, review documental. |

**Importante:** M2a–M2c pueden ser **un solo PR T1 con tests separados** si dividirlos crea más coste de coordinación que evidencia. El objetivo es densidad de entrega, no micro-Issues. M2d y M2e son decisiones de integración independientes.

## 11. Arquitectura de decisiones y estado

- **COMPROBADO:** PR #1 merge a main 8e09bd4; PR #4 código y 20 tests/re-review PASS en 7c34712; Codex exec --json validado en LT-01 según RETURN de Hack Ops, aún sin integración en producto.
- **INFERIDO:** una primera V0 de notas sintéticas + lección versionada puede construirse con Python stdlib, sin servicios.
- **HIPÓTESIS:** mejora editorial transferible entre briefs y sesiones; requiere muestras, feedback Carlos, métricas y evaluación.
- **POR_VALIDAR:** repo privado de DALI, feed autorizado de Sherlock, aprobación humana real de una primera lección, efecto real en generación de modelo, publicación y valor comercial.
- **GATES:** Grok dirige Codex; CTO revisión y alcance; L4 define IP, autoriza T2/merge; Cursor revisa en contexto limpio.

**Siguiente decisión L4:** merge de PR #4 cuando confirme HEAD/mergeability, escoger entre (a) demo V0 sintética con prueba causal antes de 17:00 o (b) integración editorial genuina en superficie privada en fase posterior. No sustituir (b) por una simulación etiquetada falsamente como DALI real.
