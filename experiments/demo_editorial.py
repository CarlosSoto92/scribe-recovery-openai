"""Demo editorial de tres minutos: control sintético, gate simulado y procesos frescos."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import scribe_editorial as editorial

CLI = ROOT / "src" / "scribe_editorial.py"
FIXTURE = ROOT / "experiments" / "fixtures" / "synthetic_note_001.json"


def execute(*arguments):
    result = subprocess.run([sys.executable, str(CLI), *map(str, arguments)],
                            capture_output=True, encoding="utf-8", timeout=30)
    document = editorial.parse_json(result.stdout)
    if result.returncode != 0 and not (arguments[0] == "compare" and result.returncode == 1):
        raise editorial.Invalid(f"paso {arguments[0]} terminó con código {result.returncode}")
    return document


def demonstrate(directory, show_json=False):
    note = editorial.load(FIXTURE, "research_note.v1")
    lessons, feedback_log = directory / "lessons.jsonl", directory / "feedback.jsonl"
    draft_path = directory / "draft-v1.json"
    print("1. Nota sintética: piloto ficticio de 4 semanas; hecho crítico f1.")
    first = execute("draft", "--note", FIXTURE, "--lessons", lessons,
                    "--session-id", "demo-v1", "--out", draft_path)
    print("2. V1 sin lecciones (debilidad sintética deliberada):", first["text"])
    feedback = execute("feedback", "--draft", draft_path, "--reviewer", "fixture_simulated",
                       "--rating", "2", "--comment", "Omitiste la duración del piloto sintético.",
                       "--target-facts", "f1", "--correction", "Conservar 4 semanas y citar f1.",
                       "--feedback-log", feedback_log)
    print("3. Feedback SIMULADO: fixture_simulated, rating 2/5; no se atribuye a Carlos.")
    lesson = execute("propose", "--feedback", feedback["feedback_id"],
                     "--feedback-log", feedback_log, "--lessons", lessons)
    print(f'4. Candidata proposed: {lesson["lesson_id"]}@v{lesson["version"]}')
    negative = execute("draft", "--note", FIXTURE, "--lessons", lessons, "--session-id", "demo-proposed")
    unchanged = (negative["text"] == first["text"] and negative["fact_refs"] == first["fact_refs"]
                 and not negative["applied_lesson_ids"])
    print("5. Control con solo proposed:", "BORRADOR SIN CAMBIO" if unchanged else "FAIL")
    prefix = lessons.read_bytes()
    approved = execute("approve", "--lesson-id", lesson["lesson_id"], "--lessons", lessons,
                       "--approval-ref", "fixture:demo-control", "--approved-by", "fixture_simulated")
    print("6. Gate SIMULADO aprobado por fixture_simulated; referencia fixture:demo-control.")
    print("En V0, para rule_type=required_fact, el writer determinista COPIA desde la nota "
          "los hechos citados por evidence.fact_ids de la lección aprobada; no inventa hechos.")
    result = execute("compare", "--note", FIXTURE, "--lessons", lessons, "--session-prefix", "demo-control")
    before, after = result["B−"], result["B+"]
    metric = "retención de hechos críticos"
    print(f'7. Procesos frescos · {metric}: B−={before["check"][metric]:.1f} / B+={after["check"][metric]:.1f}')
    checks = {
        "baseline_omits_critical_fact": before["check"][metric] == 0
            and not before["draft"]["fact_refs"] and not before["draft"]["applied_lesson_ids"],
        "approved_preserves_and_cites": after["check"][metric] == 1.0,
        "proposed_does_not_change_draft": unchanged,
        "lesson_id_and_version_recorded": after["draft"]["applied_lesson_ids"] == [
            f'{approved["lesson_id"]}@v{approved["version"]}'],
        "separate_sessions": before["draft"]["session_id"] != after["draft"]["session_id"],
        "append_only_approval_history": lessons.read_bytes().startswith(prefix)
            and [r["state"] for r in editorial.read_log(lessons, "lesson.v1")] == ["proposed", "approved"],
        "simulated_gate_labelled": approved["approved_by"] == "fixture_simulated"
            and approved["approval_ref"] == "fixture:demo-control",
    }
    passed = all(checks.values())
    print("\nComparación final · gate simulado")
    for label, branch in (("B−", before), ("B+", after)):
        for fact in note["facts"]:
            if not fact["must_keep"]:
                continue
            cited = fact["fact_id"] in branch["check"]["retained_fact_ids"]
            present = fact["text"] in branch["draft"]["text"]
            status = "PRESENTE + cita" if cited else ("PRESENTE sin cita" if present else "OMITIDO")
            print(f'{label}: {fact["fact_id"]} {status} · check {"PASS" if cited else "FAIL"}')
    print("Lección usada:", ", ".join(result["lessons_used"]) or "ninguna")
    if show_json:
        print(editorial.encoded({"checks": checks, "passed": passed}))
    return passed


def main(argv=None):
    started = time.perf_counter()
    parser = editorial.Parser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="carpeta existente donde conservar una corrida nueva")
    parser.add_argument("--json", action="store_true", help="mostrar además el JSON de checks")
    try:
        args = parser.parse_args(argv)
        if args.output_dir:
            directory = Path(tempfile.mkdtemp(prefix="scribe-editorial-", dir=args.output_dir))
            print(f"Evidencia conservada: {directory}")
            passed = demonstrate(directory, show_json=args.json)
        else:
            with tempfile.TemporaryDirectory(prefix="scribe-editorial-") as temporary:
                print(f"Evidencia temporal: {temporary} (se limpia al terminar)")
                passed = demonstrate(Path(temporary), show_json=args.json)
    except (editorial.Invalid, OSError, UnicodeError, subprocess.SubprocessError) as exc:
        message = str(exc) if isinstance(exc, editorial.Invalid) else type(exc).__name__
        print(json.dumps({"outcome": "invalid", "error": message}, ensure_ascii=False))
        return 2
    print(f"Duración: {time.perf_counter() - started:.3f} s; sin LLM, red ni API.")
    print("Control de una fixture: no prueba calidad editorial general ni aprobación humana real.")
    print("DEMO EDITORIAL PASS" if passed else "DEMO EDITORIAL FAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
