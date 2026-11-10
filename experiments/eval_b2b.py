"""Evaluación offline de los 20 casos B2B.

`--writer stub` usa el writer determinista y regenera el JSON y docs/EVAL.md.
`--replay DIR` puntúa salidas grabadas y falla con código 2 si un hash no coincide.
Un replay con pares completos y C3 actualiza el marcador sin cambiar el stub.

No llama a un modelo. El 0 % → 100 % del stub prueba el mecanismo, no un LLM.
"""

from decimal import Decimal, ROUND_HALF_UP
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))
import record_codex_runs as rec
import scribe_b2b as b2b

RESULTS = ROOT / "experiments" / "results" / "eval_b2b.json"
EVAL_MD = ROOT / "docs" / "EVAL.md"
Z = Decimal("1.959963984540054")
PENDING = "pendiente: corridas de Codex por grabar"
TENTH = Decimal("0.1")


def wilson(k, n, z=Z):
    if n <= 0:
        raise b2b.ed.Invalid("Wilson sin casos")
    successes = Decimal(k)
    total = Decimal(n)
    z2 = z * z
    phat = successes / total
    denom = 1 + z2 / total
    center = (phat + z2 / (2 * total)) / denom
    margin = z * (phat * (1 - phat) / total + z2 / (4 * total * total)).sqrt() / denom
    low = max(Decimal(0), center - margin)
    high = min(Decimal(1), center + margin)
    return low, high


def bound(value):
    return f"{Decimal(value):.10f}"


def percent(value):
    shown = (Decimal(value) * Decimal(100)).quantize(TENTH, rounding=ROUND_HALF_UP)
    return f"{shown} %"


def interval(k, n):
    low, high = wilson(k, n)
    return {
        "low": bound(low),
        "high": bound(high),
        "display": f"{percent(low)} – {percent(high)}",
    }


def sign_test(improved, worsened):
    """Prueba exacta de signos, bilateral. Los empates no entran."""
    improved, worsened = int(improved), int(worsened)
    n = improved + worsened
    if n == 0:
        p = None
    elif improved == worsened:
        p = 1.0
    else:
        k = min(improved, worsened)
        tail = sum(math.comb(n, i) for i in range(k + 1))
        p = min(1.0, (tail * 2) / (2 ** n))
    text = None if p is None else format(p, ".14f").rstrip("0").rstrip(".")
    return {"improved": improved, "worsened": worsened, "n": n, "p_two_sided": text}


def library():
    return {doc_type: rec.origin_pack(doc_type) for doc_type in b2b.DOC_TYPES}


def next_type(doc_type):
    types = b2b.DOC_TYPES
    return types[(types.index(doc_type) + 1) % len(types)]


def condition_view(note, document):
    check = b2b.check_document(note, document["text"])
    return {
        "compliant": check["compliant"],
        "met": check["met"],
        "total": check["total"],
        "failures": check["failures"],
        "applied_lesson_ids": document["applied_lesson_ids"],
        "text": document["text"],
    }


def evaluate_note(note, packs):
    own = packs[note["doc_type"]]
    proposed = own["events"][0]
    rejected = b2b.transition_event([proposed], proposed["lesson_id"], "rejected",
                                     created_at=b2b.FIXED_CLOCK)
    wrong = packs[next_type(note["doc_type"])]
    others = [event for kind, pack in packs.items() if kind != note["doc_type"] for event in pack["events"]]
    drafts = {
        "B-": b2b.draft(note, []),
        "B+": b2b.draft(note, own["events"]),
        "C1": b2b.draft(note, [proposed]),
        "C2": b2b.draft(note, [proposed, rejected]),
        "C3": b2b.draft(note, wrong["events"]),
        "C4": b2b.draft(note, others),
    }
    views = {name: condition_view(note, document) for name, document in drafts.items()}
    baseline = views["B-"]["text"]
    for name in ("C1", "C2", "C3", "C4"):
        views[name]["same_as_baseline"] = views[name]["text"] == baseline
        reg = b2b.regression(note, baseline, views[name]["text"])
        views[name]["regression_ok"] = reg["ok"]
        views[name]["length_ratio"] = None if reg["length_ratio"] is None else format(reg["length_ratio"], ".4f")
    plus = b2b.regression(note, baseline, views["B+"]["text"])
    views["B+"]["regression_ok"] = plus["ok"]
    views["B+"]["length_ratio"] = None if plus["length_ratio"] is None else format(plus["length_ratio"], ".4f")
    views["B+"]["new_forbidden"] = plus["new_forbidden"]
    views["B+"]["noncritical_missing"] = plus["noncritical_missing"]
    views["C3"]["wrong_type"] = wrong["lesson"]["scope"]["doc_type"]
    for name in ("C1", "C2", "C3", "C4"):
        del views[name]["text"]
    return views


def quote_parts(note):
    items = []
    total = None
    for fact in note["facts"]:
        if fact["text"].startswith("Partida | "):
            _tag, desc, qty, amount = fact["text"].split(" | ")
            items.append({"desc": desc, "qty": qty, "amount": amount})
        elif fact["text"].startswith("Total | "):
            total = fact["text"].split(" | ", 1)[1]
    if len(items) != 2 or not total:
        raise b2b.ed.Invalid("cotización sin partidas")
    return items, total


def rate_block(rows, key):
    k = sum(1 for row in rows if row["conditions"][key]["compliant"])
    n = len(rows)
    ratios = [Decimal(row["conditions"][key]["met"]) / Decimal(row["conditions"][key]["total"]) for row in rows]
    mean = sum(ratios, Decimal(0)) / Decimal(n)
    return {
        "k": k,
        "n": n,
        "fraction": f"{k}/{n}",
        "rate": bound(Decimal(k) / Decimal(n)),
        "rate_display": percent(Decimal(k) / Decimal(n)),
        "wilson95": interval(k, n),
        "requirements_mean": bound(mean),
        "requirements_display": percent(mean),
    }


def build_report():
    packs = library()
    loaded = b2b.iter_fixtures(rec.FIX)
    cases = []
    for _path, note in loaded:
        views = evaluate_note(note, packs)
        cases.append({
            "note_id": note["note_id"],
            "doc_type": note["doc_type"],
            "label": b2b.DOC_LABEL[note["doc_type"]],
            "case": b2b.case_number(note),
            "held_out": b2b.case_number(note) != 1,
            "customer": note["customer"]["name"],
            "conditions": views,
        })
    cases.sort(key=lambda row: (b2b.DOC_TYPES.index(row["doc_type"]), row["case"]))
    held = [row for row in cases if row["held_out"]]
    train = [row for row in cases if not row["held_out"]]
    improved = sum(1 for row in held if row["conditions"]["B+"]["compliant"] and not row["conditions"]["B-"]["compliant"])
    worsened = sum(1 for row in held if row["conditions"]["B-"]["compliant"] and not row["conditions"]["B+"]["compliant"])
    ties = len(held) - improved - worsened
    by_type = []
    for doc_type in b2b.DOC_TYPES:
        rows = [row for row in held if row["doc_type"] == doc_type]
        by_type.append({
            "doc_type": doc_type,
            "label": b2b.DOC_LABEL[doc_type],
            "B-": rate_block(rows, "B-"),
            "B+": rate_block(rows, "B+"),
        })
    controls = {}
    for name, detail in (
        ("C1", "Lección en proposed: el texto queda igual que sin lección."),
        ("C2", "Lección rechazada: el texto queda igual que sin lección."),
        ("C3", "Lección approved de otro tipo: sin efecto y sin regresión."),
        ("C4", "Solo hay lecciones de otros tipos: el documento no cambia."),
    ):
        ok = all(row["conditions"][name]["same_as_baseline"] for row in held)
        if name in ("C3", "C4"):
            ok = ok and all(row["conditions"][name]["regression_ok"] for row in held)
        controls[name] = {"pass": ok, "n": len(held), "detail": detail}
    ratios = [Decimal(row["conditions"]["B+"]["length_ratio"]) for row in held]
    lessons = []
    for doc_type in b2b.DOC_TYPES:
        pack = packs[doc_type]
        applied = sum(
            1 for row in held
            if row["doc_type"] == doc_type and any(
                item.startswith(pack["lesson"]["lesson_id"] + "@")
                for item in row["conditions"]["B+"]["applied_lesson_ids"]
            )
        )
        lessons.append({
            "doc_type": doc_type,
            "label": b2b.DOC_LABEL[doc_type],
            "rule": pack["lesson"]["rule"],
            "rule_type": pack["lesson"]["scope"]["rule_type"],
            "state": "approved",
            "scope": b2b.DOC_LABEL[doc_type],
            "evidence_note": pack["lesson"]["evidence"]["note_id"],
            "applied_held_out": applied,
            "gap_label": b2b.GAP_LABEL[doc_type],
            "comment": b2b.REVIEW[doc_type]["comment"],
            "correction": b2b.REVIEW[doc_type]["correction"],
            "approval_ref": pack["lesson"]["approval_ref"],
            "approved_by": pack["lesson"]["approved_by"],
        })
    weeks = []
    for row in cases:
        if row["doc_type"] != "cotizacion":
            continue
        note = b2b.load_note(rec.fixture_path("cotizacion", row["case"]))
        items, total = quote_parts(note)
        weeks.append({
            "week": row["case"],
            "held_out": row["held_out"],
            "customer": row["customer"],
            "email": note["customer"]["email"],
            "items": items,
            "total": total,
            "clauses": [b2b.CLAUSE_VIGENCIA, b2b.CLAUSE_PAGO],
            "text_without": row["conditions"]["B-"]["text"],
            "text_with": row["conditions"]["B+"]["text"],
            "compliant_without": row["conditions"]["B-"]["compliant"],
            "compliant_with": row["conditions"]["B+"]["compliant"],
        })
    primary_minus = rate_block(held, "B-")
    primary_plus = rate_block(held, "B+")
    company = b2b.load_note(rec.fixture_path("cotizacion", 1))["company"]
    return {
        "schema_version": "eval_b2b.v1",
        "writer": "stub",
        "writer_label": "Writer de demostración (determinista)",
        "honesty": "El 0 % → 100 % del stub prueba el mecanismo y los controles, no la calidad de un LLM.",
        "clock": "Las lecciones fixture usan el reloj fijo 2026-11-10T15:00:00Z. No es una aprobación de una persona.",
        "codex_recorded": {
            "status": PENDING,
            "runs": None,
            "note": "No hay salidas de Codex en este resultado. No se inventan cifras de un modelo.",
        },
        "held_out": {
            "n": len(held),
            "B-": primary_minus,
            "B+": primary_plus,
            "sign_test": {**sign_test(improved, worsened), "ties": ties},
            "regression": {
                "ok": all(row["conditions"]["B+"]["regression_ok"] for row in held),
                "min_length_ratio": format(min(ratios), ".4f"),
                "max_length_ratio": format(max(ratios), ".4f"),
            },
        },
        "by_type": by_type,
        "train_case_1": {
            "note": "El caso 1 enseña la lección y no entra en la tasa.",
            "B-": rate_block(train, "B-"),
            "B+": rate_block(train, "B+"),
        },
        "controls": controls,
        "lessons": lessons,
        "demo": {"company": company, "weeks": weeks},
        "cases": cases,
    }


def recorded_markdown(recorded):
    if not recorded.get("runs") or recorded["status"] != "grabado":
        return [f"**{recorded['status']}.**", "", recorded["note"]]
    tolerant = recorded["tolerant"]
    lines = [
        f"**{recorded['label']}**. CLI exacto: {recorded['codex_version']}. "
        f"N = {recorded['n']} corridas; cada repetición cuenta como un ensayo.",
        "",
        f"Fecha UTC: {recorded['date_utc']}. Operador: {recorded['operator']}. "
        f"Fuente: `experiments/recorded/{recorded['source']}/`.",
        "",
        "El revisor estricto sigue siendo primario. El revisor tolerante admite markdown, "
        "tablas y folios sin prefijo; conserva cifras, unidades y cita junto al valor. "
        "Solo excluye negaciones simples inmediatas de las frases prohibidas.",
        "",
        "| Condición | Revisor estricto (primario) | Tasa | Wilson 95 % | Revisor tolerante | Tasa | Wilson 95 % |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for key in ("B-", "B+", "C3"):
        strict, relaxed = recorded[key], tolerant[key]
        lines.append(f"| {key} | {strict['fraction']} | {strict['rate_display']} | {strict['wilson95']['display']} | "
                     f"{relaxed['fraction']} | {relaxed['rate_display']} | {relaxed['wilson95']['display']} |")
    lines += ["", "| Prueba de signos bilateral | Mejoran | Empeoran | Empatan | n sin empates | p bilateral |",
              "| --- | --- | --- | --- | --- | --- |"]
    for label, block in (("Revisor estricto (primario)", recorded), ("Revisor tolerante", tolerant)):
        signs = block["sign_test"]
        lines.append(f"| {label} | {signs['improved']} | {signs['worsened']} | {signs['ties']} | {signs['n']} | {signs['p_two_sided']} |")
    lines += ["", "Pares por (doc_type, case, rep); se excluyen los empates.", "", recorded["control_note"],
              "", recorded["comparison"], "", recorded["tolerant_comparison"], "",
              "| Tipo | Revisor | B-: fracción; tasa; Wilson 95 % | B+: fracción; tasa; Wilson 95 % | C3: fracción; tasa; Wilson 95 % |",
              "| --- | --- | --- | --- | --- |"]
    for strict, relaxed in zip(recorded["by_type"], tolerant["by_type"]):
        for label, row in (("revisor estricto (primario)", strict), ("revisor tolerante", relaxed)):
            cells = [f"{row[key]['fraction']}; {row[key]['rate_display']}; {row[key]['wilson95']['display']}"
                     if row.get(key) else "—" for key in ("B-", "B+", "C3")]
            lines.append(f"| {row['label']} | {label} | " + " | ".join(cells) + " |")
    lines += ["", *recorded["observations"], "", "### Clasificación de cada fallo estricto", "",
              "«Fallo del modelo» es provisional; Carlos lo confirmará a ojo. "
              "Los fallos que persisten están en las corridas listadas abajo y en el JSON.", "",
              "| Corrida | Clasificación | Fallos que persisten con el tolerante |", "| --- | --- | --- |"]
    for row in recorded["failure_classification"]:
        remaining = "; ".join(row["tolerant_failures"]) or "Ninguno"
        lines.append(f"| {row['file']} | {row['classification']} | {remaining} |")
    return lines + ["", recorded["note"]]


def render_markdown(report):
    held = report["held_out"]
    lines = [
        "# Evaluación B2B",
        "",
        "Cumplimiento de requisitos verificables en documentos ficticios de "
        "Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA). "
        "No mide calidad editorial general.",
        "",
        "## Diseño",
        "",
        "Veinte notas sintéticas: cinco tipos de documento por cuatro casos. "
        "La lección de cada tipo sale del caso 1, con el gate `fixture_simulated`. "
        "La tasa usa solo los 15 casos retenidos (casos 2 a 4).",
        "",
        "Condiciones: **B−** sin lección, **B+** con la lección approved de su tipo, "
        "**C1** proposed, **C2** rejected, **C3** lección de otro tipo, "
        "**C4** solo lecciones de otros tipos.",
        "",
        "Métrica primaria: documentos que cumplen todos sus requisitos críticos. "
        "Secundaria: promedio de requisitos cumplidos. "
        "Regresión: hechos no críticos conservados, cero frases prohibidas nuevas y longitud ±25 %.",
        "",
        "El intervalo es de Wilson al 95 %. La prueba de signos es exacta y bilateral; "
        "los empates no entran. Con n = 15 el intervalo es ancho. "
        "Estas cuentas describen al writer de demostración, no a un modelo.",
        "",
        "## Cómo reproducir",
        "",
        "```bash",
        "python3 -m unittest discover -s experiments",
        "python3 experiments/eval_b2b.py --writer stub",
        "python3 experiments/record_codex_runs.py --dry-run --controls",
        "python3 experiments/eval_b2b.py --replay experiments/recorded/codex-20261110",
        "```",
        "",
        "La tercera orden solo muestra un plan. El replay puntúa las salidas ya grabadas "
        "sin red y actualiza este informe y el JSON. Regenerar el stub conserva las corridas reales.",
        "",
        "## Resultados del writer de demostración",
        "",
        f"Etiqueta: **{report['writer_label']}**. {report['honesty']}",
        "",
        "| Condición | Documentos conformes | Intervalo de Wilson 95 % | Requisitos cumplidos |",
        "| --- | --- | --- | --- |",
        f"| Sin lección | {held['B-']['fraction']} | {held['B-']['wilson95']['display']} | {held['B-']['requirements_display']} |",
        f"| Con lección | {held['B+']['fraction']} | {held['B+']['wilson95']['display']} | {held['B+']['requirements_display']} |",
        "",
        f"Pares que mejoran: {held['sign_test']['improved']}. "
        f"Pares que empeoran: {held['sign_test']['worsened']}. "
        f"Empates: {held['sign_test']['ties']}. "
        f"p bilateral: {held['sign_test']['p_two_sided']}.",
        "",
        f"Regresión B+ frente a B−: {'dentro de la regla' if held['regression']['ok'] else 'fuera de la regla'}. "
        f"Razón de longitud entre {held['regression']['min_length_ratio']} y {held['regression']['max_length_ratio']}.",
        "",
        "| Tipo | Sin lección | Con lección | Wilson sin lección | Wilson con lección |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in report["by_type"]:
        lines.append(
            f"| {row['label']} | {row['B-']['fraction']} | {row['B+']['fraction']} | "
            f"{row['B-']['wilson95']['display']} | {row['B+']['wilson95']['display']} |"
        )
    lines += [
        "",
        f"Caso 1, aparte, sin entrar en la tasa: sin lección {report['train_case_1']['B-']['fraction']}, "
        f"con lección {report['train_case_1']['B+']['fraction']}.",
        "",
        "## Controles",
        "",
        "| Control | Esperado | Resultado |",
        "| --- | --- | --- |",
    ]
    for name in ("C1", "C2", "C3", "C4"):
        row = report["controls"][name]
        lines.append(f"| {name} | {row['detail']} | {'pasa' if row['pass'] else 'no pasa'} ({row['n']}/{row['n']}) |")
    lines += ["", "## Fallos con el texto del writer", ""]
    failures = [row for row in report["cases"] if row["held_out"] and not row["conditions"]["B-"]["compliant"]]
    if not failures:
        lines.append("Ningún caso retenido falló sin lección.")
    for row in failures:
        view = row["conditions"]["B-"]
        lines += [
            f"### {row['label']} · caso {row['case']} · sin lección",
            "",
            "\n".join(f"- {item}" for item in view["failures"]),
            "",
            "```text",
            view["text"].rstrip(),
            "```",
            "",
        ]
    plus_failures = [row for row in report["cases"] if row["held_out"] and not row["conditions"]["B+"]["compliant"]]
    if plus_failures:
        lines.append("Con la lección approved también hubo fallos:")
        lines.append("")
        for row in plus_failures:
            lines.append(f"- {row['note_id']}: {'; '.join(row['conditions']['B+']['failures'])}")
    else:
        lines.append(
            "Con la lección approved, los 15 casos retenidos cumplen. "
            "Eso lo hace el writer de demostración, que tiene la corrección codificada. "
            "No es un resultado de un modelo."
        )
    lines += [
        "",
        "## Modelo real",
        "",
        *recorded_markdown(report["codex_recorded"]),
        "",
        "## Límites honestos",
        "",
        "El stub es una prueba de mecanismo y de los controles, no evidencia de calidad de un LLM. "
        "Los fixtures son sintéticos y los escribimos nosotros. Cada checker es un regex: "
        "el estricto penaliza formatos equivalentes; el tolerante acepta formas acotadas, no paráfrasis generales. "
        "Una copia literal puede salir conforme. Las clasificaciones requieren revisión humana. "
        "Las reglas son convenciones de la casa, no conocimiento del mundo. "
        "n = 15 es pequeño. La aprobación humana de estas lecciones es simulada (`fixture:`). "
        "El detalle está en `docs/LIMITATIONS.md`.",
        "",
    ]
    return "\n".join(lines)


def write_report(report):
    import json
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    markdown = render_markdown(report)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(text, encoding="utf-8")
    EVAL_MD.write_text(markdown, encoding="utf-8")
    return report


def write_stub():
    import json
    report = build_report()
    if RESULTS.is_file():
        recorded = json.loads(RESULTS.read_text(encoding="utf-8")).get("codex_recorded", {})
        if recorded.get("runs") and recorded.get("status") == "grabado":
            report["codex_recorded"] = recorded
    return write_report(report)


def recorded_scores(runs):
    """Cuenta ensayos, sin colapsar repeticiones ni emparejar por posición."""
    grouped = {key: [run for run in runs if run["condition"] == key]
               for key in ("B-", "B+", "C3")}

    def rate(rows, key):
        return rate_block([{"conditions": {key: row}} for row in rows], key) if rows else None

    pairs = {}
    for run in runs:
        if run["condition"] in ("B-", "B+"):
            pairs.setdefault((run["doc_type"], run["case"], run["rep"]), {})[run["condition"]] = run
    paired = bool(pairs) and all(set(pair) == {"B-", "B+"} for pair in pairs.values())
    signs = None
    if paired:
        improved = sum(pair["B+"]["compliant"] and not pair["B-"]["compliant"] for pair in pairs.values())
        worsened = sum(pair["B-"]["compliant"] and not pair["B+"]["compliant"] for pair in pairs.values())
        signs = {**sign_test(improved, worsened), "ties": len(pairs) - improved - worsened}
    by_type = []
    for kind in b2b.DOC_TYPES:
        rows = {key: [run for run in grouped[key] if run["doc_type"] == kind] for key in ("B-", "B+", "C3")}
        if rows["B-"] and rows["B+"]:
            by_type.append({"doc_type": kind, "label": b2b.DOC_LABEL[kind],
                            **{key: rate(rows[key], key) for key in rows}})
    return {**{key: rate(rows, key) for key, rows in grouped.items()},
            "sign_test": signs, "by_type": by_type,
            "status": "grabado" if paired and grouped["C3"] else "incompleto"}


def summarize_recorded(replayed):
    runs = replayed["runs"]
    scores = recorded_scores(runs)
    paired = scores["sign_test"] is not None
    by_type = scores["by_type"]
    version = replayed["codex_version"].removeprefix("codex-cli ")
    label_version = version.removesuffix(".0")
    summary = {
        **scores,
        "label": f"Codex (codex-cli {label_version}, suscripción ChatGPT)",
        **{key: replayed[key] for key in ("source", "codex_version", "date_utc", "operator", "runs")},
        "n": len(runs),
        "control_note": "C3 usa la skill de OTRO tipo de documento. Se mide cumplimiento; "
                        "no es el control de texto idéntico al stub ni demuestra ausencia de regresión.",
        "note": "Muestra pequeña: una versión del CLI, un día y un operador. "
                "Generación no determinista; las repeticiones de una misma nota no son del todo independientes. "
                "El checker es un regex y no mide calidad editorial general.",
        "observations": [],
    }
    if paired:
        stub = build_report()["held_out"]
        worse = Decimal(summary["B+"]["rate"]) < Decimal(stub["B+"]["rate"])
        summary["worse_than_stub"] = worse
        summary["comparison"] = (
            f"Stub determinista: {stub['B-']['fraction']} → {stub['B+']['fraction']}; "
            f"Codex: {summary['B-']['fraction']} → {summary['B+']['fraction']}. "
            + ("En esta grabación Codex sale peor que el writer determinista con lección. " if worse else
               "Codex alcanza la tasa del writer determinista con lección en esta grabación. ")
            + "El stub tiene el arreglo codificado; esta comparación no prueba calidad general de un modelo."
        )
    for row in by_type:
        if Decimal(row["B+"]["rate"]) < Decimal(row["B-"]["rate"]):
            summary["observations"].append(
                f"Revisor estricto (primario): en {row['doc_type']}, B+ sale peor que B-: "
                f"{row['B-']['fraction']} → {row['B+']['fraction']}. "
                "El checker es un regex; estos números no identifican la causa."
            )
    if all("tolerant" in run for run in runs):
        summary["primary_reviewer"] = "revisor estricto"
        summary["tolerant"] = recorded_scores([{**run, **run["tolerant"]} for run in runs])
        summary["tolerant"]["label"] = "revisor tolerante"
        summary["failure_classification"] = [
            {**{key: run[key] for key in ("file", "doc_type", "case", "rep", "condition", "classification", "failures")},
             "tolerant_failures": run["tolerant"]["failures"]}
            for run in runs if not run["compliant"]
        ]
        summary["classification_counts"] = {
            condition: {label: sum(run.get("classification") == label for run in runs if run["condition"] == condition)
                        for label in ("falso negativo del checker", "fallo del modelo")}
            for condition in ("B-", "B+", "C3")
        }
        plus = summary["tolerant"]["B+"]
        counts = summary["classification_counts"]["B+"]
        summary["tolerant_comparison"] = (
            f"B+ con revisor estricto: {summary['B+']['fraction']}; con revisor tolerante: {plus['fraction']}. "
            f"El tolerante {'mejora la tasa' if Decimal(plus['rate']) > Decimal(summary['B+']['rate']) else 'no mejora la tasa'}. "
            f"De los fallos B+ estrictos, {counts['falso negativo del checker']} son falso negativo del checker "
            f"y {counts['fallo del modelo']} siguen como fallo del modelo (provisional; Carlos lo confirmará a ojo)."
        )
    return summary


def _utc(value):
    b2b.ed.utc(value)


def replay(directory):
    directory = Path(directory)
    manifest_path = directory / "MANIFEST.json"
    if not manifest_path.is_file():
        raise b2b.ed.Invalid("falta MANIFEST.json")
    manifest = b2b.ed.parse_json(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("example_only") is True:
        raise b2b.ed.Invalid("manifiesto de ejemplo: no es una corrida")
    for key in ("schema_version", "codex_version", "prompt_sha256", "sandbox", "date_utc", "operator", "runs"):
        if key not in manifest or manifest[key] in ("", None):
            raise b2b.ed.Invalid("manifiesto incompleto")
    if manifest["schema_version"] != "codex_record_manifest.v1":
        raise b2b.ed.Invalid("schema de manifiesto desconocido")
    if manifest["sandbox"] != "workspace-write":
        raise b2b.ed.Invalid("sandbox distinta de la grabación")
    if not manifest["runs"]:
        raise b2b.ed.Invalid("el manifiesto no tiene corridas")
    _utc(manifest["date_utc"])
    if manifest["prompt_sha256"] != rec.sha256_bytes(rec.PROMPT.encode("utf-8")):
        raise b2b.ed.Invalid("hash del prompt no coincide")
    if "/home/" in json_command(manifest) or "/Users/" in json_command(manifest):
        raise b2b.ed.Invalid("el manifiesto conserva una ruta de usuario")
    packs = library()
    scored = []
    seen = set()
    for run in manifest["runs"]:
        for key in ("doc_type", "case", "condition", "rep", "file", "note_sha256", "skill_sha256", "output_sha256"):
            if key not in run:
                raise b2b.ed.Invalid("corrida incompleta")
        identity = (run["doc_type"], run["case"], run["rep"], run["condition"])
        if identity in seen:
            raise b2b.ed.Invalid("ensayo duplicado en el manifiesto")
        seen.add(identity)
        condition, kind, skill = run["condition"], run["doc_type"], run.get("skill_doc_type")
        if condition not in ("B-", "B+", "C3") or (
            (condition == "B-" and skill is not None)
            or (condition == "B+" and skill != kind)
            or (condition == "C3" and (not skill or skill == kind))
        ):
            raise b2b.ed.Invalid("condición y tipo de skill incompatibles")
        path = directory / run["file"]
        if not path.is_file() or path.parent.resolve() != directory.resolve():
            raise b2b.ed.Invalid("falta la salida grabada")
        raw = path.read_bytes()
        if rec.sha256_bytes(raw) != run["output_sha256"]:
            raise b2b.ed.Invalid("hash de la salida no coincide")
        note_path = rec.fixture_path(run["doc_type"], int(run["case"]))
        if rec.sha256_bytes(note_path.read_bytes()) != run["note_sha256"]:
            raise b2b.ed.Invalid("hash de la nota no coincide")
        lesson = None if not run.get("skill_doc_type") else packs[run["skill_doc_type"]]["lesson"]
        if rec.bundle_sha(lesson) != run["skill_sha256"]:
            raise b2b.ed.Invalid("hash de la skill no coincide")
        command = run.get("command", "")
        if "/home/" in command or "/Users/" in command:
            raise b2b.ed.Invalid("la corrida conserva una ruta de usuario")
        note = b2b.load_note(note_path)
        text = raw.decode("utf-8")
        check = b2b.check_document(note, text)
        tolerant = b2b.check_document_tolerant(note, text)
        classification = None if check["compliant"] else (
            "falso negativo del checker" if tolerant["compliant"] else "fallo del modelo")
        scored.append({
            "file": run["file"],
            "doc_type": run["doc_type"],
            "case": run["case"],
            "condition": run["condition"],
            "rep": run["rep"],
            **check,
            "tolerant": tolerant,
            "classification": classification,
        })
    report = {
        "schema_version": "eval_b2b_replay.v1",
        "source": directory.name,
        "codex_version": manifest["codex_version"],
        "operator": manifest["operator"],
        "date_utc": manifest["date_utc"],
        "runs": scored,
        "note": "Puntuación offline de salidas grabadas. La generación no es determinista.",
    }
    report["codex_recorded"] = summarize_recorded(report)
    return report


def json_command(manifest):
    return str(manifest.get("command", ""))


def main(argv=None):
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--writer", choices=("stub",))
    parser.add_argument("--replay", type=Path)
    try:
        args = parser.parse_args(argv)
        if bool(args.writer) == bool(args.replay):
            raise b2b.ed.Invalid("elige --writer stub o --replay")
        if args.replay:
            report = replay(args.replay)
            if report["codex_recorded"]["status"] == "grabado":
                scoreboard = build_report()
                scoreboard["codex_recorded"] = report["codex_recorded"]
                write_report(scoreboard)
            print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        report = write_stub()
        failed = [name for name, row in report["controls"].items() if not row["pass"]]
        print(json.dumps({
            "results": str(RESULTS.relative_to(ROOT)),
            "eval": str(EVAL_MD.relative_to(ROOT)),
            "held_out_minus": report["held_out"]["B-"]["fraction"],
            "held_out_plus": report["held_out"]["B+"]["fraction"],
            "codex": report["codex_recorded"]["status"],
            "controls_failed": failed,
        }, ensure_ascii=False))
        return 1 if failed else 0
    except (b2b.ed.Invalid, OSError, UnicodeError, ValueError) as exc:
        message = str(exc) if isinstance(exc, b2b.ed.Invalid) else type(exc).__name__
        print(b2b.ed.encoded({"outcome": "invalid", "error": message}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
