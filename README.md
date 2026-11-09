# 🧠 Scribe/Recovery — los agentes de IA que aprenden de sus propios errores

> **Estado: experimental (hackathon, 9 nov 2026, CDMX).** El nombre, el concepto, la arquitectura y el stack son provisionales y pueden cambiar durante el evento.

## Hipótesis

Los agentes de IA (como Codex, Antigravity o Claude Code) fallan de formas que se repiten: comandos rotos, supuestos falsos, bucles, pasos que olvidan el contexto. Hoy esos errores se pierden en los logs.

**Creemos que si un "escriba" (Scribe) registra cada falla de forma estructurada y un módulo de recuperación (Recovery) la convierte en una lección reutilizable, los agentes pueden recuperarse más rápido y repetir menos errores.**

## Problema

- Los errores de los agentes no quedan registrados de forma útil.
- Cada sesión empieza de cero: el agente no recuerda qué falló antes ni por qué.
- Recuperarse depende de que un humano lea el log y corrija a mano.

## Solución (propuesta)

1. **Scribe**: captura los eventos y errores de un agente (qué intentó, qué falló, en qué contexto).
2. **Recovery**: clasifica la falla y propone o ejecuta una estrategia de recuperación.
3. **Aprendizaje**: guarda la lección para que la siguiente corrida la use desde el inicio.

## Arquitectura y tecnologías

Por definir durante el hackathon; el CTO Sintético dirige la arquitectura. Codex (OpenAI) es el harness protagonista de la implementación.

```
src/          código de la solución (stack por definir)
experiments/  pruebas rápidas de ideas, modelos y herramientas
docs/         decisiones, bitácora y notas del equipo
```

## Quickstart

```bash
git clone https://github.com/CarlosSoto92/scribe-recovery-openai.git
cd scribe-recovery-openai
```

Las instrucciones de instalación se agregan cuando se fije el stack. Nunca subas llaves ni secretos: usa un archivo `.env` local (ya está en `.gitignore`).

## Equipo

- **Carlos Soto Santis**: decisiones finales y producto.
- **CTO Sintético**: arquitectura, mandatos técnicos y evaluación.
- **Codex (OpenAI)**: implementación.
- **Antigravity**: conocimiento del entorno LT-01.
- **Hack Ops**: operaciones y coordinación del hackathon.

## Licencia

[MIT](LICENSE)
