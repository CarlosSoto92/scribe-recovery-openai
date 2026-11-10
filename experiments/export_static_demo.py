#!/usr/bin/env python3
"""Exporta el loop editorial V0 a HTML estático para GitHub Pages (stdlib only)."""

from __future__ import annotations

import html
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


def export_legacy() -> int:
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


RESULTS = ROOT / "experiments" / "results" / "eval_b2b.json"
CORRIGE = ROOT / "docs" / "corrige" / "index.html"
DEMO_V0 = ROOT / "docs" / "demo" / "index.html"


def esc(value):
    return html.escape(str(value), quote=True)


def recorded_html(recorded):
    if not recorded.get("runs") or recorded["status"] != "grabado":
        return f"""<p data-figure="{esc(recorded['status'])}"><strong>{esc(recorded['status'])}</strong></p>
      <p>{esc(recorded['note'])}</p>
      <p>Grabado, N = pendiente. No hay intervalo porque no hay corridas.</p>"""
    rows = []
    for key in ("B-", "B+", "C3"):
        cells = []
        for label, block in (("Revisor estricto (primario)", recorded), ("Revisor tolerante", recorded["tolerant"])):
            rate = block[key]
            cells.append(f'<td data-label="{label}">' + "; ".join(
                f'<span data-figure="{esc(value)}">{esc(value)}</span>'
                for value in (rate["fraction"], rate["rate_display"], rate["wilson95"]["display"])) + "</td>")
        rows.append(f"<tr><th>{esc(key)}</th>{''.join(cells)}</tr>")
    signs_html = []
    for label, block in (("Revisor estricto (primario)", recorded), ("Revisor tolerante", recorded["tolerant"])):
        signs = block["sign_test"]
        signs_html.append(f"<p>{label}: {esc(signs['improved'])} mejoran, {esc(signs['worsened'])} empeoran, "
                          f"{esc(signs['ties'])} empatan. Sin empates: n = {esc(signs['n'])}, "
                          f"p bilateral = {esc(signs['p_two_sided'])}.</p>")
    types = []
    for strict, tolerant in zip(recorded["by_type"], recorded["tolerant"]["by_type"]):
        for label, row in (("Revisor estricto (primario)", strict), ("Revisor tolerante", tolerant)):
            cells = ["; ".join((row[key]["fraction"], row[key]["rate_display"], row[key]["wilson95"]["display"]))
                     for key in ("B-", "B+", "C3")]
            types.append(f"<tr><th>{esc(row['label'])} · {label}</th>" +
                         "".join(f'<td data-label="{key}: fracción; tasa; Wilson 95 %">{esc(cell)}</td>'
                                 for key, cell in zip(("B-", "B+", "C3"), cells)) + "</tr>")
    counts = recorded["classification_counts"]
    classifications = "".join(
        f"<li>{esc(key)}: {esc(row['falso negativo del checker'])} falso negativo del checker; "
        f"{esc(row['fallo del modelo'])} fallo del modelo.</li>" for key, row in counts.items())
    return f"""<p><strong data-figure="{esc(recorded['label'])}">{esc(recorded['label'])}</strong></p>
      <p>N = {esc(recorded['n'])} corridas; cada repetición cuenta como un ensayo.</p>
      <p>CLI exacto: {esc(recorded['codex_version'])}. Fecha UTC: {esc(recorded['date_utc'])}.
      Operador: {esc(recorded['operator'])}. Fuente: {esc(recorded['source'])}.</p>
      <p>El revisor tolerante acepta markdown, tablas y folios sin prefijo. Conserva cifras, unidades,
      citas junto al valor y rechaza promesas afirmativas. Ambos son regex; no miden calidad editorial.</p>
      <table><thead><tr><th>Condición</th><th>Revisor estricto (primario): fracción; tasa; Wilson 95 %</th>
      <th>Revisor tolerante: fracción; tasa; Wilson 95 %</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
      <p>Prueba de signos bilateral, pares por (doc_type, case, rep):</p>{''.join(signs_html)}
      <p>{esc(recorded['control_note'])}</p>
      <p>{esc(recorded['comparison'])}</p>
      <p>{esc(recorded['tolerant_comparison'])}</p>
      <ul>{classifications}</ul><p>«Falso negativo del checker»: etiqueta automática, «falla el estricto y pasa el tolerante»;
      «fallo del modelo» indica que el fallo persiste con el tolerante. No es una revisión humana independiente.
      Carlos revisó los 11 casos B+ el 2026-11-10 y coincidió en lo general;
      eso no convierte las etiquetas en dictámenes editoriales ni demuestra calidad general.
      Los fallos restantes y cada reclasificación están en <a href="../EVAL.md">la evaluación completa</a>.</p>
      <details><summary>Resultados por tipo con ambos revisores</summary>
      <table><thead><tr><th>Tipo y revisor</th><th>B-: fracción; tasa; Wilson 95 %</th>
      <th>B+: fracción; tasa; Wilson 95 %</th><th>C3: fracción; tasa; Wilson 95 %</th></tr></thead>
      <tbody>{''.join(types)}</tbody></table></details>
      {''.join('<p>' + esc(note) + '</p>' for note in recorded['observations'])}
      <p>{esc(recorded['note'])}</p>"""


def render_corrige(report):
    """Página estática. Los números salen del JSON de la evaluación."""
    company = report["demo"]["company"]
    weeks = report["demo"]["weeks"]
    lessons = report["lessons"]
    quote = next(lesson for lesson in lessons if lesson["doc_type"] == "cotizacion")
    held = report["held_out"]
    payload = {
        "lessons": [
            {"doc_type": lesson["doc_type"], "minus": next(row["B-"]["fraction"] for row in report["by_type"] if row["doc_type"] == lesson["doc_type"]),
             "plus": next(row["B+"]["fraction"] for row in report["by_type"] if row["doc_type"] == lesson["doc_type"])}
            for lesson in lessons
        ],
        "held": {
            "minus": held["B-"]["fraction"],
            "plus": held["B+"]["fraction"],
            "rate_minus": held["B-"]["rate_display"],
            "rate_plus": held["B+"]["rate_display"],
        },
    }
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
    first = next(week for week in weeks if week["week"] == 1)
    later = [week for week in weeks if week["week"] != 1]
    first_sheet = sheet_html(first, company, quote)
    later_sheets = "\n".join(sheet_html(week, company, quote) for week in later)
    cards = "\n".join(card_html(lesson, report) for lesson in lessons)
    rows = "\n".join(score_row(row) for row in report["by_type"])
    return f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Corrige una vez · Válvulas y Bombas Ejemplo del Bajío</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAzMiAzMiI+PHJlY3Qgd2lkdGg9IjMyIiBoZWlnaHQ9IjMyIiByeD0iNiIgZmlsbD0iIzE0M2QzMiIvPjxwYXRoIGQ9Ik0yMyA5YTEwIDEwIDAgMSAwIDAgMTQiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2ZmZmRmOCIgc3Ryb2tlLXdpZHRoPSI0Ii8+PC9zdmc+">
<meta name="description" content="Caso ficticio: una corrección en las cotizaciones se vuelve una lección y la persona decide si la IA la usa.">
<style>
:root {{
  --ink: #1c1915;
  --muted: #3f382f;
  --paper: #f3efe6;
  --sheet: #fffdf8;
  --line: #e3dac8;
  --green: #143d32;
  --green-ink: #f4f7f4;
  --miss-bg: #fde8e8;
  --miss: #7f1d1d;
  --ok-bg: #e5f6ea;
  --ok: #14532d;
  --amber-bg: #fff4cc;
  --amber: #6b4e00;
  --focus: #9a3412;
}}
* {{ box-sizing: border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
  margin: 0;
  font: 17px/1.5 "Segoe UI", system-ui, sans-serif;
  color: var(--ink);
  background: var(--paper);
}}
a {{ color: #143d32; }}
a:hover {{ color: #0f2e26; }}
:focus-visible {{ outline: 3px solid var(--focus); outline-offset: 3px; }}
.skip {{
  position: absolute; left: 1rem; top: 0; transform: translateY(-120%);
  background: #fff; color: var(--ink); padding: .6rem 1rem; z-index: 2;
}}
.skip:focus {{ transform: none; }}
.hero {{
  background: var(--green); color: var(--green-ink);
  padding: 2.5rem 1.25rem 2rem;
}}
.hero-inner, main, .site-footer {{ max-width: 980px; margin: 0 auto; }}
main {{ padding: 1.25rem; }}
.kicker {{ letter-spacing: .04em; text-transform: uppercase; font-size: 16px; margin: 0 0 .6rem; }}
h1 {{ font-size: 2rem; line-height: 1.2; margin: 0 0 .8rem; font-weight: 650; }}
h2 {{ font-size: 1.45rem; line-height: 1.25; margin: 0 0 .6rem; }}
h3 {{ font-size: 1.15rem; margin: 0; }}
.lead {{ font-size: 1.15rem; margin: 0 0 1rem; max-width: 38rem; }}
.button, button {{
  font: inherit; min-height: 44px; border-radius: 8px; cursor: pointer;
}}
.button {{
  display: inline-block; background: #f4e1b5; color: #1c1915; text-decoration: none;
  padding: .7rem 1.1rem; font-weight: 650;
}}
button {{
  background: var(--green); color: var(--green-ink); border: 2px solid var(--green);
  padding: .55rem 1rem;
}}
button[disabled] {{ opacity: .55; cursor: not-allowed; }}
button[aria-pressed="false"] {{ background: #fff; color: var(--green); }}
button[aria-pressed="true"] {{ background: var(--green); color: var(--green-ink); }}
button.switch[aria-checked="false"] {{ background: var(--green); color: var(--green-ink); }}
button.switch[aria-checked="true"] {{ background: var(--miss-bg); color: var(--miss); border-color: var(--miss); }}
.chips {{ display: flex; flex-wrap: wrap; gap: .5rem; padding: 0; margin: 1rem 0 0; list-style: none; }}
.chips li {{
  border: 1px solid rgba(244, 247, 244, .45); border-radius: 999px;
  padding: .2rem .75rem; font-size: 16px;
}}
.plain {{ font-size: 1.05rem; max-width: 40rem; }}
section {{ margin: 1.5rem 0; }}
.sheet {{
  background: var(--sheet); border: 1px solid var(--line); border-radius: 12px;
  padding: 1.1rem 1.1rem 1.2rem; margin: 1rem 0;
  box-shadow: 0 10px 28px rgba(40, 32, 20, .05);
}}
.stamp {{
  display: inline-block; border: 2px solid var(--miss); color: var(--miss);
  font-weight: 750; letter-spacing: .12em; padding: .1rem .45rem; margin: 0 0 .4rem;
}}
.company {{ margin: 0; font-family: Georgia, "Iowan Old Style", Palatino, serif; }}
.meta {{ color: var(--muted); margin: .2rem 0; }}
table {{ width: 100%; border-collapse: collapse; margin: .8rem 0; }}
th, td {{ text-align: left; padding: .45rem .3rem; border-bottom: 1px solid var(--line); vertical-align: top; }}
.gap {{ background: var(--miss-bg); color: var(--miss); border-radius: 8px; padding: .8rem 1rem; }}
.added {{ background: var(--ok-bg); color: var(--ok); border-radius: 8px; padding: .8rem 1rem; }}
.added p, .gap p {{ margin: .25rem 0; }}
.review {{ margin: .8rem 0 0; }}
.toggle {{ display: flex; flex-wrap: wrap; gap: .5rem; margin-top: .8rem; }}
.lesson, .proposal {{
  background: var(--sheet); border: 1px solid var(--line); border-radius: 12px;
  padding: 1rem; margin: .8rem 0;
}}
.badge {{
  display: inline-block; font-weight: 750; border-radius: 999px; padding: .15rem .7rem; font-size: 16px;
}}
.propuesta {{ background: var(--amber-bg); color: var(--amber); }}
.aprobada {{ background: var(--ok-bg); color: var(--ok); }}
.retirada {{ background: var(--miss-bg); color: var(--miss); }}
.switch {{ background: #fff; color: var(--ink); border: 2px solid var(--green); }}
.bars {{ display: grid; gap: .7rem; }}
.bar-row {{ display: grid; grid-template-columns: minmax(8rem, 14rem) 1fr auto; gap: .6rem; align-items: center; }}
.track {{ background: #efe8d8; border-radius: 999px; height: 12px; }}
.bar {{ height: 12px; border-radius: 999px; }}
.bar.empty {{ width: 8%; background: var(--miss); }}
.bar.full {{ width: 100%; background: var(--ok); }}
.official, .pending, .note {{
  background: var(--sheet); border: 1px solid var(--line); border-radius: 12px; padding: 1rem;
}}
.pending {{ background: #fff8e8; }}
.site-footer {{ padding: 0 1.25rem 2.5rem; color: var(--muted); }}
.sr-only {{
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip: rect(0, 0, 0, 0); border: 0;
}}
details {{ margin-top: .8rem; }}
summary {{ cursor: pointer; min-height: 44px; display: flex; align-items: center; }}
pre {{ white-space: pre-wrap; overflow-wrap: anywhere; font: 16px/1.45 ui-monospace, monospace; }}
@media (max-width: 700px) {{
  h1 {{ font-size: 1.7rem; }}
  .bar-row {{ grid-template-columns: 1fr; }}
  table, thead, tbody, tr, th, td {{ display: block; }}
  thead, tfoot th {{ position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); }}
  td {{ border-bottom: 0; padding: .2rem 0; }}
  tr {{ border-bottom: 1px solid var(--line); padding: .45rem 0; }}
  td::before {{ content: attr(data-label); font-weight: 700; display: block; }}
}}
@media (prefers-reduced-motion: reduce) {{
  html {{ scroll-behavior: auto; }}
  * {{ transition: none !important; animation: none !important; }}
}}
</style>
</head>
<body>
<a class="skip" href="#caso">Saltar al caso</a>
<header class="hero" id="inicio">
  <div class="hero-inner">
    <p class="kicker">Válvulas y Bombas Ejemplo del Bajío · FICTICIA</p>
    <h1>Cada semana la misma corrección. Esta vez la IA la aprende.</h1>
    <p class="lead">Corrige una vez. El siguiente documento ya sale bien, y tú decides qué aprende la IA.</p>
    <p class="plain">El error de esta casa: las cotizaciones salían sin vigencia y sin condiciones de pago. Una persona lo corrige, lo aprueba, y las de las semanas siguientes salen bien.</p>
    <p><a class="button" href="#caso">Ver el caso</a></p>
    <ul class="chips">
      <li>Datos 100 % ficticios</li>
      <li>Sin reentrenar</li>
      <li>Tú apruebas</li>
    </ul>
  </div>
</header>
<main>
  <section id="caso">
    <h2>Semana 1 — el error</h2>
    <p>{esc(first["customer"])} pidió una cotización. Faltó lo de siempre. El caso 1 es donde nace la corrección; no entra en la medición de las semanas siguientes.</p>
    {first_sheet}
  </section>
  <section id="correccion">
    <h2>La corrección</h2>
    <p>El revisor escribe: «{esc(quote["correction"])}»</p>
    <p><button type="button" id="convertir">Convertir en lección</button></p>
    <article class="proposal" id="tarjeta-cotizacion" hidden>
      <p><span class="badge propuesta" id="estado-cotizacion">PROPUESTA</span></p>
      <h3>Cotizaciones</h3>
      <p>{esc(quote["rule"])}</p>
      <p>Alcance: cotizaciones. Evidencia: {esc(quote["evidence_note"])}. En la evaluación se aplicó a {esc(quote["applied_held_out"])} casos retenidos.</p>
      <p id="detalle-aprobacion" hidden>Aprobada por {esc(quote["approved_by"])} · {esc(quote["approval_ref"])}. Aprobación simulada · fixture.</p>
    </article>
  </section>
  <section id="compuerta">
    <h2>La compuerta humana</h2>
    <p>Sin tu aprobación, la IA no la usa.</p>
    <p><button type="button" id="aprobar" disabled>Aprobar <span>aprobación simulada · fixture</span></button></p>
  </section>
  <section id="semanas">
    <h2>Semanas 2, 3 y 4</h2>
    <p>Otros clientes y otras partidas. Si apruebas la lección, estas cotizaciones salen con vigencia y con condiciones de pago. Si la retiras, el hueco vuelve.</p>
    {later_sheets}
  </section>
  <section id="biblioteca">
    <h2>Biblioteca de lecciones</h2>
    <p>Cinco reglas de la casa, una por tipo de documento. Retirar una lección devuelve el fallo: el efecto depende de que siga aprobada.</p>
    {cards}
  </section>
  <section id="marcador">
    <h2>Marcador</h2>
    <div class="official">
      <p><strong data-figure="{esc(report["writer_label"])}">{esc(report["writer_label"])}</strong></p>
      <p>{esc(report["honesty"])}</p>
      <div class="bars" id="marcador-vivo">{rows}</div>
      <p id="total-vivo">Parcial: la cotización de esta página aún no está aprobada.</p>
    </div>
    <div class="note">
      <h3>Resultado de la evaluación</h3>
      <p>Sin lección <strong data-figure="{esc(held["B-"]["fraction"])}">{esc(held["B-"]["fraction"])}</strong>
        ({esc(held["B-"]["rate_display"])}, Wilson 95 % {esc(held["B-"]["wilson95"]["display"])}).</p>
      <p>Con lección <strong data-figure="{esc(held["B+"]["fraction"])}">{esc(held["B+"]["fraction"])}</strong>
        ({esc(held["B+"]["rate_display"])}, Wilson 95 % {esc(held["B+"]["wilson95"]["display"])}).</p>
      <p>Requisitos críticos cumplidos: {esc(held["B-"]["rate_display"])} → {esc(held["B+"]["rate_display"])}.</p>
    </div>
  </section>
  <section id="modelo-real">
    <h2>Con un modelo real</h2>
    <div class="note">
      {recorded_html(report["codex_recorded"])}
      <p><a href="../EVAL.md">Ver la metodología</a> · <a href="../LIMITATIONS.md">Ver los límites</a></p>
    </div>
  </section>
</main>
<footer class="site-footer" id="pie">
  <h2>¿Qué corrección repites tú cada semana?</h2>
  <p><a href="https://github.com/CarlosSoto92/scribe-recovery-openai/issues/new?template=feedback-experto.yml">Contarlo en un issue</a></p>
  <p>Repo <a href="https://github.com/CarlosSoto92/scribe-recovery-openai">MIT</a> · <a href="../demo/">Demo anterior</a> · Sin trackers.</p>
  <p id="aviso-vivo" aria-live="polite">La lección de cotización todavía no está propuesta.</p>
</footer>
<script type="application/json" id="datos">{blob}</script>
<script>
(function () {{
  var data = JSON.parse(document.getElementById("datos").textContent);
  var state = {{ proposed: false, approved: false, retired: {{}} }};
  data.lessons.forEach(function (lesson) {{ state.retired[lesson.doc_type] = false; }});
  var card = document.getElementById("tarjeta-cotizacion");
  var status = document.getElementById("estado-cotizacion");
  var detail = document.getElementById("detalle-aprobacion");
  var live = document.getElementById("aviso-vivo");
  var total = document.getElementById("total-vivo");

  function quoteActive() {{
    return state.approved && !state.retired.cotizacion;
  }}
  function lessonActive(kind) {{
    if (kind === "cotizacion") return quoteActive();
    return !state.retired[kind];
  }}
  function render() {{
    card.hidden = !(state.proposed || state.approved);
    status.className = "badge propuesta";
    status.textContent = "PROPUESTA";
    detail.hidden = true;
    if (state.approved && state.retired.cotizacion) {{
      status.className = "badge retirada";
      status.textContent = "RETIRADA";
    }} else if (state.approved) {{
      status.className = "badge aprobada";
      status.textContent = "APROBADA";
      detail.hidden = false;
    }}
    document.querySelectorAll("[data-week]").forEach(function (sheet) {{
      var showWith = quoteActive() && sheet.getAttribute("data-mode") === "con";
      sheet.querySelector("[data-view=sin]").hidden = showWith;
      sheet.querySelector("[data-view=con]").hidden = !showWith;
      sheet.querySelector("[data-mode-button=sin]").setAttribute("aria-pressed", showWith ? "false" : "true");
      sheet.querySelector("[data-mode-button=con]").setAttribute("aria-pressed", showWith ? "true" : "false");
      sheet.querySelector("[data-mode-button=con]").disabled = !quoteActive();
    }});
    var allOn = true;
    var allOff = true;
    data.lessons.forEach(function (lesson) {{
      var active = lessonActive(lesson.doc_type);
      allOn = allOn && active;
      allOff = allOff && !active;
      var label = document.querySelector('[data-live-label="' + lesson.doc_type + '"]');
      var bar = document.querySelector('[data-live-bar="' + lesson.doc_type + '"]');
      label.textContent = active ? lesson.plus : lesson.minus;
      bar.classList.toggle("full", active);
      bar.classList.toggle("empty", !active);
      var sw = document.querySelector('[data-retire="' + lesson.doc_type + '"]');
      if (lesson.doc_type === "cotizacion") sw.disabled = !state.approved;
      sw.setAttribute("aria-checked", state.retired[lesson.doc_type] ? "true" : "false");
      sw.textContent = state.retired[lesson.doc_type] ? "Restaurar lección" : "Retirar lección";
    }});
    if (allOn) total.textContent = data.held.plus + " · " + data.held.rate_plus;
    else if (allOff) total.textContent = data.held.minus + " · " + data.held.rate_minus;
    else total.textContent = "Parcial: la cotización de esta página aún no está aprobada, o hay una lección retirada.";
  }}
  document.getElementById("convertir").addEventListener("click", function () {{
    state.proposed = true;
    document.getElementById("aprobar").disabled = false;
    live.textContent = "La lección quedó en propuesta. Todavía no se usa.";
    render();
  }});
  document.getElementById("aprobar").addEventListener("click", function () {{
    if (!state.proposed) return;
    state.approved = true;
    document.querySelectorAll("[data-week]").forEach(function (sheet) {{
      sheet.setAttribute("data-mode", "con");
    }});
    live.textContent = "Lección aprobada con una aprobación simulada. Las semanas 2, 3 y 4 salen con vigencia y pago.";
    render();
  }});
  document.querySelectorAll("[data-mode-button]").forEach(function (button) {{
    button.addEventListener("click", function () {{
      var sheet = button.closest("[data-week]");
      var mode = button.getAttribute("data-mode-button");
      if (mode === "con" && !quoteActive()) {{
        live.textContent = "Sin tu aprobación, la IA no la usa.";
        return;
      }}
      sheet.setAttribute("data-mode", mode);
      live.textContent = mode === "con" ? "Esta cotización se muestra con la lección." : "Esta cotización se muestra sin la lección.";
      render();
    }});
  }});
  document.querySelectorAll("[data-retire]").forEach(function (button) {{
    button.addEventListener("click", function () {{
      var kind = button.getAttribute("data-retire");
      if (kind === "cotizacion" && !state.approved) return;
      state.retired[kind] = !state.retired[kind];
      if (kind === "cotizacion" && state.retired.cotizacion) {{
        document.querySelectorAll("[data-week]").forEach(function (sheet) {{
          sheet.setAttribute("data-mode", "sin");
        }});
        live.textContent = "Lección retirada. Las cotizaciones vuelven a salir sin vigencia y sin condiciones de pago.";
      }} else if (kind === "cotizacion") {{
        document.querySelectorAll("[data-week]").forEach(function (sheet) {{
          sheet.setAttribute("data-mode", "con");
        }});
        live.textContent = "La lección de cotización vuelve a estar en uso.";
      }} else {{
        live.textContent = state.retired[kind] ? "Lección retirada. Ese tipo de documento vuelve a fallar." : "Lección otra vez en uso.";
      }}
      render();
    }});
  }});
  render();
}})();
</script>
</body>
</html>
"""


def sheet_html(week, company, quote):
    rows = "\n".join(
        "<tr><td data-label=\"Descripción\">"
        + esc(item["desc"])
        + "</td><td data-label=\"Cantidad\">"
        + esc(item["qty"])
        + "</td><td data-label=\"Importe\">"
        + esc(item["amount"])
        + "</td></tr>"
        for item in week["items"]
    )
    header = f"""
    <p class="stamp">FICTICIA</p>
    <h3 class="company">{esc(company["name"])}</h3>
    <p class="meta">RFC {esc(company["rfc"])} · {esc(company["email"])} · {esc(company["phone"])}</p>
    <p class="meta">{esc(company["city"])}</p>
    <p><strong>Cotización · Semana {esc(week["week"])} · {esc(week["customer"])}</strong></p>
    <p class="meta">{esc(week["email"])}</p>
    <table>
      <caption class="sr-only">Partidas de la cotización</caption>
      <thead><tr><th>Descripción</th><th>Cant.</th><th>Importe</th></tr></thead>
      <tbody>{rows}</tbody>
      <tfoot><tr><th>Total</th><td colspan="2" data-label="Total">{esc(week["total"])}</td></tr></tfoot>
    </table>
    """
    gap = f'<div class="gap" data-view="sin"><p><strong>{esc(quote["gap_label"])}</strong></p></div>'
    added = '<div class="added" data-view="con" hidden>' + "".join(
        f"<p>{esc(clause)}</p>" for clause in week["clauses"]
    ) + "</div>"
    texts = (
        "<details><summary>Ver el texto del writer sin la lección</summary><pre>"
        + esc(week["text_without"])
        + "</pre></details><details><summary>Ver el texto del writer con la lección</summary><pre>"
        + esc(week["text_with"])
        + "</pre></details>"
    )
    if week["week"] == 1:
        return f"""<article class="sheet" id="semana-1">
        {header}
        {gap}
        <p class="review">Revisor de la casa, persona ficticia: «{esc(quote["comment"])}»</p>
        {texts}
        </article>"""
    return f"""<article class="sheet" id="semana-{esc(week["week"])}" data-week="{esc(week["week"])}" data-mode="sin">
    {header}
    {gap}
    {added}
    <div class="toggle" role="group" aria-label="Versión de la semana {esc(week["week"])}">
      <button type="button" data-mode-button="sin" aria-pressed="true">Ver sin la lección</button>
      <button type="button" data-mode-button="con" aria-pressed="false">Ver con la lección</button>
    </div>
    {texts}
    </article>"""


def card_html(lesson, report):
    minus = next(row["B-"]["fraction"] for row in report["by_type"] if row["doc_type"] == lesson["doc_type"])
    plus = next(row["B+"]["fraction"] for row in report["by_type"] if row["doc_type"] == lesson["doc_type"])
    return f"""<article class="lesson" id="leccion-{esc(lesson["doc_type"])}">
    <h3>{esc(lesson["label"])}</h3>
    <p>{esc(lesson["rule"])}</p>
    <p>Estado en la evaluación: {esc(lesson["state"])}. Alcance: {esc(lesson["scope"])}. Evidencia: {esc(lesson["evidence_note"])}. Veces aplicada en los casos retenidos: {esc(lesson["applied_held_out"])}.</p>
    <p>Sin la lección {esc(minus)}. Con la lección {esc(plus)}.</p>
    <p><button type="button" class="switch" role="switch" aria-checked="false" data-retire="{esc(lesson["doc_type"])}">Retirar lección</button></p>
    </article>"""


def score_row(row):
    initial = row["B-"]["fraction"] if row["doc_type"] == "cotizacion" else row["B+"]["fraction"]
    klass = "empty" if row["doc_type"] == "cotizacion" else "full"
    return f"""<div class="bar-row">
    <span>{esc(row["label"])}</span>
    <div class="track" aria-hidden="true"><div class="bar {klass}" data-live-bar="{esc(row["doc_type"])}"></div></div>
    <strong data-live-label="{esc(row["doc_type"])}" data-figure="{esc(initial)}">{esc(initial)}</strong>
    </div>"""


def export_corrige():
    report = json.loads(RESULTS.read_text(encoding="utf-8"))
    page = render_corrige(report)
    CORRIGE.parent.mkdir(parents=True, exist_ok=True)
    CORRIGE.write_text(page, encoding="utf-8")
    print(f"Wrote {CORRIGE} ({len(page.encode('utf-8'))} bytes)")
    return 0


def main(argv=None):
    # La demo V0 sigue en docs/demo/ para no cambiar su URL publicada.
    # --v0 la regenera (lleva reloj y no es estable). Lo normal es esta página.
    if argv and argv[:1] == ["--v0"]:
        return export_legacy()
    return export_corrige()


if __name__ == "__main__":
    raise SystemExit(main())
