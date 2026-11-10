#!/usr/bin/env python3
"""Exporta el loop editorial V0 a HTML estático para GitHub Pages (stdlib only)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))

import scribe_editorial as ed  # noqa: E402
import webapp as web  # noqa: E402

FIXTURE = ROOT / "experiments" / "fixtures" / "synthetic_note_001.json"
OUT = ROOT / "docs" / "demo" / "index.html"
ASSETS = "../assets"


def run_flow(store: web.Store, note: dict):
    draft = store.generate(note)
    lesson = store.feedback(
        note,
        draft["draft_id"],
        reviewer="fixture_simulated",
        rating=2,
        comment="Omitiste la duración del piloto sintético.",
        targets=["f1"],
    )
    approved = store.transition(
        lesson["lesson_id"],
        "approved",
        approval_ref="fixture:demo-control",
        approved_by="fixture_simulated",
    )
    branches = store.compare(note)
    return draft, lesson, approved, branches


def section(title: str, body: str) -> str:
    return f"<section><h2>{title}</h2>{body}</section>"


def img(name: str, alt: str) -> str:
    return (
        f'<figure class="shot"><img src="{ASSETS}/{name}.png" alt="{web.h(alt)}" '
        f'loading="lazy" width="960"><figcaption>{web.h(alt)}</figcaption></figure>'
    )


def build_html(note, draft, lesson, approved, branches) -> str:
    facts = "".join(
        f'<li class="{"critical" if f["must_keep"] else ""}">{web.h(f["fact_id"])}: '
        f'{web.h(f["text"])}'
        f'{" — must_keep=true" if f["must_keep"] else ""}</li>'
        for f in note["facts"]
    )
    minus_pass = branches["B−"]["check"]["retención de hechos críticos"] == 1.0
    plus_pass = branches["B+"]["check"]["retención de hechos críticos"] == 1.0
    compare_block = web.comparison_html(note, branches)
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Scribe/Recovery · Demo V0 (RSI Hackathon)</title>
<meta name="description" content="Demo estática del loop editorial Scribe/Recovery. Proyecto del RSI Hackathon Kavak × OpenAI × Primero AI, 9 nov 2026 CDMX.">
<style>
body{{font:16px/1.5 system-ui,-apple-system,sans-serif;background:#f4f6f8;color:#182637;max-width:980px;margin:0 auto;padding:1.5rem}}
header.banner{{background:#0f2744;color:#f5f7fa;border-radius:12px;padding:1.25rem 1.5rem;margin-bottom:1.25rem}}
header.banner p{{margin:.4rem 0;opacity:.95}}
header.banner strong{{color:#ffd978}}
section,article{{background:#fff;border:1px solid #dce2e9;border-radius:10px;padding:1rem 1.15rem;margin:1rem 0}}
h1,h2,h3{{line-height:1.25;margin-top:0}}
.critical{{font-weight:700;background:#fff0c6;padding:.35rem .5rem;border-radius:4px}}
ul{{padding-left:1.2rem}}li{{margin:.4rem 0}}
.draft-text,pre{{white-space:pre-wrap;overflow-wrap:anywhere}}
.comparison{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}}
table{{border-collapse:collapse;width:100%;font-size:.92rem}}
td,th{{text-align:left;padding:.45rem;border-bottom:1px solid #ddd;overflow-wrap:anywhere}}
.diff-add{{background:#dcfce7;color:#14532d;border-bottom:2px solid #15803d}}
.diff-del{{background:#fee2e2;color:#991b1b;border-bottom:2px dashed #b91c1c}}
.diff-legend{{line-height:1.7}}
.shot{{margin:1rem 0}}
.shot img{{max-width:100%;height:auto;border:1px solid #dce2e9;border-radius:8px}}
.shot figcaption{{font-size:.9rem;color:#4a5a6d;margin-top:.4rem}}
.notice{{background:#eef5ff;border:1px solid #c7daf5;border-radius:8px;padding:.9rem 1rem}}
.limits{{background:#fff7e8;border:1px solid #f0d9a0;border-radius:8px;padding:.9rem 1rem}}
footer{{margin:2rem 0 1rem;font-size:.95rem;color:#4a5a6d}}
a{{color:#174f85}}
.badges span{{display:inline-block;background:#e8eef6;border-radius:999px;padding:.2rem .7rem;margin:.15rem .25rem 0 0;font-size:.85rem}}
@media(max-width:700px){{.comparison{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<header class="banner">
  <p><strong>Proyecto creado en el RSI Hackathon Kavak × OpenAI × Primero AI · 9 nov 2026, CDMX</strong></p>
  <h1>Scribe/Recovery · Demo pública V0</h1>
  <p>Una corrección humana se convierte en una lección aprobada que el agente siguiente usa — sin reentrenar.</p>
</header>

<div class="notice">
  <p><strong>Qué es (3 líneas).</strong></p>
  <ol>
    <li><strong>Scribe</strong> registra la falla o la corrección de forma estructurada.</li>
    <li><strong>Recovery</strong> solo aplica lecciones en estado <em>approved</em> (gate humano).</li>
    <li>El writer siguiente retiene hechos críticos medibles (B− vs B+) con fixtures sintéticos.</li>
  </ol>
</div>

<div class="badges">
  <span>MIT</span>
  <span>N=1 (Codex en vivo)</span>
  <span>Fixtures sintéticos</span>
  <span>Nada se publica solo a LinkedIn</span>
</div>

{section("1. Nota sintética", f"<p>{web.h(note['topic'])}</p><ul>{facts}</ul><p>{web.h(' '.join(note['limits']))}</p>")}

{section("2. Borrador V1 (sin lecciones)", f"<p class='draft-text'>{web.h(draft['text'])}</p><p>Lecciones usadas: ninguna · session <code>{web.h(draft['session_id'])}</code></p>" + img("02-borrador", "Captura UX · borrador V1 en la mini web local"))}

{section("3. Corrección humana (simulada)", f"<p>Reviewer: <code>fixture_simulated</code> · rating 2/5 · target <code>f1</code></p><p class='draft-text'>«Omitiste la duración del piloto sintético.»</p><p>Corrección pedida: conservar «4 semanas» y citar f1. No se atribuye a una persona real.</p>" + img("03-correccion", "Captura UX · formulario de corrección"))}

{section("4. Lección aprobada (gate simulado)", f"<p>Lección <code>{web.h(lesson['lesson_id'])}@v{lesson['version']}</code> → estado <strong>approved</strong>.</p><p>Aprobada por <code>{web.h(approved.get('approved_by',''))}</code> · ref <code>{web.h(approved.get('approval_ref',''))}</code>. La UI local pide declaración humana; esta página usa el gate de la demo.</p>" + img("04-aprobacion", "Captura UX · aprobación de lección"))}

{section("5. Comparación B− vs B+ (diff visual)", f"<p>B− sin lecciones → {'PASS' if minus_pass else 'FAIL'}. B+ con lección approved → {'PASS' if plus_pass else 'FAIL'}.</p>{compare_block}" + img("05-comparacion", "Captura UX · comparación B− vs B+ en navegador real"))}

<div class="limits">
  <p><strong>Resultado honesto.</strong> Esta demo usa fixtures sintéticos y un writer determinista en el recorrido estático. La corrida Codex en vivo del hackathon fue <strong>N=1</strong> por rama. El checker es literal + cita; una paráfrasis puede fallar. <strong>Nada se publica solo</strong> a LinkedIn u otra red: la publicación la hace una persona.</p>
</div>

<footer>
  <p>Repo: <a href="https://github.com/CarlosSoto92/scribe-recovery-openai">CarlosSoto92/scribe-recovery-openai</a></p>
  <p>Correr local: <code>python3 experiments/demo_editorial.py</code> ·
  <code>python3 experiments/demo_codex_writer.py --dry-run</code> ·
  <code>python3 experiments/webapp.py</code> (solo 127.0.0.1)</p>
  <p>Regenerar esta página: <code>python3 experiments/export_static_demo.py</code></p>
  <p>Licencia MIT · Sin trackers · Sin JS externo.</p>
</footer>
</body>
</html>
"""


def main() -> int:
    note = ed.load(FIXTURE, "research_note.v1")
    with tempfile.TemporaryDirectory(prefix="scribe-static-") as tmp:
        store = web.Store(Path(tmp) / "demo.sqlite")
        draft, lesson, approved, branches = run_flow(store, note)
        html = build_html(note, draft, lesson, approved, branches)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT} ({OUT.stat().st_size} bytes)")
    print(json.dumps({
        "B−": branches["B−"]["check"]["retención de hechos críticos"],
        "B+": branches["B+"]["check"]["retención de hechos críticos"],
        "lesson": f"{lesson['lesson_id']}@v{lesson['version']}",
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
