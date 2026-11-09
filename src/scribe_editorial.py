"""Loop editorial sintético Fase 0: contratos, gate y writer determinista.

V1 omite deliberadamente hechos críticos. No hay LLM, red ni publicación.
Un escritor secuencial; JSONL append-only de aplicación, no WORM ni ACID.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile


class Invalid(ValueError):
    """Entrada, referencias o historial incompatibles."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def string(value):
    return isinstance(value, str) and bool(value.strip())


def identifier(value):
    return string(value) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*", value) is not None


def fields(value, names):
    require(isinstance(value, dict) and set(value) == set(names.split()),
            "campos de contrato incorrectos")


def strings(value, ids=False, nonempty=False):
    require(isinstance(value, list), "se esperaba lista")
    require(not nonempty or bool(value), "lista vacía")
    require(all((identifier if ids else string)(item) for item in value), "elemento inválido")
    require(len(value) == len(set(value)), "elemento duplicado")


def utc(value):
    require(string(value) and 'T' in value, "timestamp UTC inválido")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Invalid("timestamp UTC inválido") from exc
    require(stamp.utcoffset() == timedelta(0), "timestamp debe ser UTC")


def now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def validate(document, schema=None):
    require(isinstance(document, dict), "documento debe ser objeto")
    kind = document.get("schema_version")
    require(schema is None or kind == schema, "schema_version incompatible")
    if kind == "research_note.v1":
        fields(document, "schema_version note_id source topic facts limits")
        require(identifier(document["note_id"]) and string(document["topic"]), "nota inválida")
        source = document["source"]
        fields(source, "type url retrieved_at")
        require(source["type"] == "synthetic" and source["url"] is None,
                "Fase 0 solo admite source.type=synthetic y url=null")
        utc(source["retrieved_at"])
        facts = document["facts"]
        require(isinstance(facts, list) and bool(facts), "facts vacío o inválido")
        for fact in facts:
            fields(fact, "fact_id text must_keep")
            require(identifier(fact["fact_id"]) and string(fact["text"])
                    and type(fact["must_keep"]) is bool, "fact inválido")
        strings([fact["fact_id"] for fact in facts], ids=True)
        strings(document["limits"], nonempty=True)
    elif kind == "draft.v1":
        fields(document, "schema_version draft_id session_id note_id applied_lesson_ids text fact_refs status")
        for key in ("draft_id", "session_id", "note_id"):
            require(identifier(document[key]), f"{key} inválido")
        strings(document["applied_lesson_ids"])
        require(all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*@v[1-9][0-9]*", item)
                    for item in document["applied_lesson_ids"]), "referencia de lección inválida")
        strings(document["fact_refs"], ids=True)
        require(string(document["text"]) and document["status"] == "needs_human_review",
                "borrador inválido")
    elif kind == "feedback.v1":
        fields(document, "schema_version feedback_id draft_id reviewer rating rating_scale comment target_fact_ids correction created_at")
        require(identifier(document["feedback_id"]) and identifier(document["draft_id"]), "ID inválido")
        require(string(document["reviewer"]) and string(document["comment"]), "feedback vacío")
        require(type(document["rating"]) is int and 1 <= document["rating"] <= 5
                and document["rating_scale"] == "1-5", "rating debe ser entero 1-5")
        strings(document["target_fact_ids"], ids=True, nonempty=True)
        require(document["correction"] is None or string(document["correction"]), "correction inválida")
        utc(document["created_at"])
    elif kind == "lesson.v1":
        fields(document, "schema_version lesson_id version source_feedback_id scope trigger rule evidence state approved_by approval_ref created_at")
        require(identifier(document["lesson_id"]) and identifier(document["source_feedback_id"]), "ID inválido")
        require(type(document["version"]) is int and document["version"] >= 1, "version inválida")
        fields(document["scope"], "task rule_type")
        require(all(identifier(v) for v in document["scope"].values()), "scope inválido")
        require(string(document["trigger"]) and string(document["rule"]), "regla vacía")
        fields(document["evidence"], "note_id fact_ids")
        require(identifier(document["evidence"]["note_id"]), "note_id inválido")
        strings(document["evidence"]["fact_ids"], ids=True, nonempty=True)
        require(document["state"] in ("proposed", "approved", "rejected"), "estado inválido")
        if document["state"] == "approved":
            require(string(document["approved_by"]) and string(document["approval_ref"]),
                    "approved exige approved_by y approval_ref")
            simulated = document["approved_by"] == "fixture_simulated"
            require(simulated == document["approval_ref"].startswith("fixture:"),
                    "aprobación fixture debe atribuirse solo a fixture_simulated")
        else:
            require(document["approved_by"] is None and document["approval_ref"] is None,
                    "estado no aprobado debe tener aprobación null")
        utc(document["created_at"])
    else:
        raise Invalid("schema_version desconocido")
    return document


def reject_duplicates(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "clave JSON duplicada")
        result[key] = value
    return result


def parse_json(raw):
    def invalid_constant(_):
        raise Invalid("constante JSON no permitida")
    try:
        return json.loads(raw, object_pairs_hook=reject_duplicates, parse_constant=invalid_constant)
    except (ValueError, RecursionError) as exc:
        raise Invalid("JSON inválido") from exc


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


def load(path, schema):
    return validate(parse_json(Path(path).read_bytes().decode("utf-8")), schema)


def stable_id(prefix, value):
    return prefix + hashlib.sha256(encoded(value).encode("utf-8")).hexdigest()[:24]


def latest_lessons(events):
    latest = {}
    for event in events:
        validate(event, "lesson.v1")
        old = latest.get(event["lesson_id"])
        # También admitir un snapshot aprobado importado con provenance válida.
        # Si hay historial previo, cada transición debe conservarlo y ser válida.
        if old is not None:
            require(event["version"] == old["version"] + 1, "version no consecutiva")
            require((old["state"], event["state"]) in {
                ("proposed", "approved"), ("proposed", "rejected"), ("approved", "rejected")},
                "transición inválida")
            mutable = {"version", "state", "approved_by", "approval_ref", "created_at"}
            require(all(event[k] == old[k] for k in old if k not in mutable),
                    "provenance/regla alterada en transición")
            require(datetime.fromisoformat(event["created_at"].replace("Z", "+00:00")) >=
                    datetime.fromisoformat(old["created_at"].replace("Z", "+00:00")),
                    "timestamp de transición anterior al origen")
        latest[event["lesson_id"]] = event
    return list(latest.values())


def read_log(path, schema):
    path = Path(path)
    try:
        raw = path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        require(not path.is_symlink(), "log apunta a un enlace sin destino")
        return []
    require(not raw or raw.endswith("\n"), "JSONL incompleto: falta LF final; no se repara")
    records = [validate(parse_json(line), schema) for line in raw.split("\n")[:-1]]
    if schema == "lesson.v1":
        latest_lessons(records)
    else:
        ids = [r["feedback_id"] for r in records]
        require(len(ids) == len(set(ids)), "feedback_id duplicado")
    return records


def append_log(path, record):
    validate(record)
    schema = record["schema_version"]
    require(schema in ("lesson.v1", "feedback.v1"), "tipo de log inválido")
    records = read_log(path, schema)
    if schema == "lesson.v1":
        latest_lessons(records + [record])
    else:
        require(all(r["feedback_id"] != record["feedback_id"] for r in records), "feedback duplicado")
    # Nunca reparar, truncar o reescribir el historial existente.
    with Path(path).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(record) + "\n")


def save_new(path, document):
    validate(document)
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded(document) + "\n")


def distinct(paths):
    paths = [Path(p) for p in paths]
    for index, path in enumerate(paths):
        for other in paths[index + 1:]:
            require(path.resolve() != other.resolve() and not (
                path.exists() and other.exists() and path.samefile(other)), "rutas en conflicto")


def approved_for(note, lessons):
    """Filtrar snapshots vigentes ANTES de entregarlos al writer."""
    validate(note, "research_note.v1")
    return [lesson for lesson in latest_lessons(lessons)
            if lesson["state"] == "approved"
            and lesson["scope"] == {"task": "linkedin_draft", "rule_type": "required_fact"}
            and lesson["evidence"]["note_id"] == note["note_id"]]


def check_draft(note, document):
    validate(note, "research_note.v1")
    validate(document, "draft.v1")
    require(document["note_id"] == note["note_id"], "nota/borrador incompatibles")
    known = {fact["fact_id"]: fact for fact in note["facts"]}
    require(set(document["fact_refs"]) <= set(known), "fact_ref desconocido")
    critical = [fact for fact in note["facts"] if fact["must_keep"]]
    retained = [fact["fact_id"] for fact in critical if fact["fact_id"] in document["fact_refs"]
                and fact["text"] in document["text"]
                and f'[{note["note_id"]}:{fact["fact_id"]}]' in document["text"]]
    return {"retained_fact_ids": retained, "critical_total": len(critical),
            "retención de hechos críticos": len(retained) / len(critical) if critical else None}


def draft(note, approved_lessons, session_id="session-default"):
    """Writer puro: mismo input produce el mismo documento completo.

    Debilidad sintética V1: sin regla aprobada, omitir todos los must_keep.
    Las notas se tratan como datos; nunca se ejecuta su contenido.
    """
    validate(note, "research_note.v1")
    require(identifier(session_id), "session_id inválido")
    critical = {fact["fact_id"] for fact in note["facts"] if fact["must_keep"]}
    required, applied = set(), []
    for lesson in approved_lessons:
        validate(lesson, "lesson.v1")
        require(lesson["state"] == "approved", "writer solo recibe approved")
        require(lesson["scope"] == {"task": "linkedin_draft", "rule_type": "required_fact"}
                and lesson["evidence"]["note_id"] == note["note_id"], "scope/evidence incompatible")
        require(set(lesson["evidence"]["fact_ids"]) <= critical, "lección apunta a facts no críticos/desconocidos")
        required.update(lesson["evidence"]["fact_ids"])
        applied.append(f'{lesson["lesson_id"]}@v{lesson["version"]}')
    facts = [fact for fact in note["facts"] if fact["fact_id"] in required]
    text = "Borrador sintético: un piloto de IA muestra oportunidades para mejorar procesos."
    for fact in facts:
        text += f' {fact["text"]} [{note["note_id"]}:{fact["fact_id"]}]'
    result = {"schema_version": "draft.v1", "session_id": session_id, "note_id": note["note_id"],
              "applied_lesson_ids": sorted(applied), "text": text,
              "fact_refs": [fact["fact_id"] for fact in facts], "status": "needs_human_review"}
    result["draft_id"] = stable_id("draft-", {"note": note, "draft": result})
    return validate(result, "draft.v1")


def make_feedback(note, document, reviewer, rating, comment, targets, correction=None):
    check_draft(note, document)
    feedback = {"schema_version": "feedback.v1", "draft_id": document["draft_id"],
                "reviewer": reviewer, "rating": rating, "rating_scale": "1-5", "comment": comment,
                "target_fact_ids": targets, "correction": correction, "created_at": now()}
    feedback["feedback_id"] = stable_id("fb-", feedback)
    validate(feedback, "feedback.v1")
    require(set(targets) <= {f["fact_id"] for f in note["facts"]}, "target_fact_ids desconocidos")
    return feedback


def propose_candidate(note, document, feedback):
    check_draft(note, document)
    validate(feedback, "feedback.v1")
    require(feedback["draft_id"] == document["draft_id"], "feedback/draft incompatibles")
    known = {f["fact_id"] for f in note["facts"]}
    require(set(feedback["target_fact_ids"]) <= known, "target_fact_ids desconocidos")
    critical = {f["fact_id"] for f in note["facts"] if f["must_keep"]}
    targets = [f for f in feedback["target_fact_ids"] if f in critical]
    require(bool(targets), "feedback no apunta a must_keep")
    lesson = {"schema_version": "lesson.v1", "lesson_id": stable_id("lesson-", feedback["feedback_id"]),
              "version": 1, "source_feedback_id": feedback["feedback_id"],
              "scope": {"task": "linkedin_draft", "rule_type": "required_fact"},
              "trigger": "La nota contiene un fact con must_keep=true",
              "rule": "Incluir los datos críticos de evidence y conservar su referencia verificable",
              "evidence": {"note_id": note["note_id"], "fact_ids": targets},
              "state": "proposed", "approved_by": None, "approval_ref": None, "created_at": now()}
    return validate(lesson, "lesson.v1")


def transition(path, lesson_id, state, approval_ref=None, approved_by=None):
    latest = {r["lesson_id"]: r for r in latest_lessons(read_log(path, "lesson.v1"))}
    require(lesson_id in latest, "lesson_id desconocido")
    event = deepcopy(latest[lesson_id])
    event.update(version=event["version"] + 1, state=state, approval_ref=approval_ref,
                 approved_by=approved_by, created_at=now())
    append_log(path, event)
    return event


def context_paths(log, feedback_id):
    # Hash del ID: ningún identificador de entrada se usa como ruta libre.
    base = Path(str(log) + ".context") / stable_id("", feedback_id)
    return Path(str(base) + ".note.json"), Path(str(base) + ".draft.json")


def fresh_draft(note_path, lessons_path, session_id):
    result = subprocess.run([sys.executable, str(Path(__file__).resolve()), "draft",
                             "--note", str(note_path), "--lessons", str(lessons_path),
                             "--session-id", session_id], capture_output=True, encoding="utf-8", timeout=15)
    require(result.returncode == 0, "subproceso draft inválido")
    return validate(parse_json(result.stdout), "draft.v1")


def compare(note_path, lessons_path, prefix):
    note = load(note_path, "research_note.v1")
    require(identifier(prefix), "session-prefix inválido")
    require(any(f["must_keep"] for f in note["facts"]), "compare requiere hechos críticos")
    # B− y B+ son invocaciones nuevas secuenciales, mismo writer/checker y nota.
    with tempfile.TemporaryDirectory(prefix="scribe-editorial-control-") as temporary:
        empty = Path(temporary) / "empty.jsonl"
        empty.touch()
        minus = fresh_draft(note_path, empty, prefix + "-minus")
        plus = fresh_draft(note_path, lessons_path, prefix + "-plus")
    before, after = check_draft(note, minus), check_draft(note, plus)
    passed = (before["retención de hechos críticos"] == 0
              and after["retención de hechos críticos"] > before["retención de hechos críticos"]
              and bool(plus["applied_lesson_ids"]) and not minus["applied_lesson_ids"])
    return {"outcome": "success" if passed else "failed", "metric": "retención de hechos críticos",
            "B−": {"draft": minus, "check": before}, "B+": {"draft": plus, "check": after},
            "lessons_used": plus["applied_lesson_ids"]}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Invalid(message)


def parser():
    result = Parser(description=__doc__)
    subs = result.add_subparsers(dest="command", required=True)
    command = subs.add_parser("draft")
    command.add_argument("--note", required=True, type=Path)
    command.add_argument("--lessons", required=True, type=Path)
    command.add_argument("--session-id", required=True)
    command.add_argument("--out", type=Path)
    command = subs.add_parser("feedback")
    command.add_argument("--draft", required=True, type=Path)
    command.add_argument("--reviewer", required=True)
    command.add_argument("--rating", required=True, type=int)
    command.add_argument("--comment", required=True)
    command.add_argument("--target-facts", required=True)
    command.add_argument("--correction")
    command.add_argument("--feedback-log", type=Path, default=Path("feedback.jsonl"))
    command = subs.add_parser("propose")
    command.add_argument("--feedback", required=True)
    command.add_argument("--feedback-log", required=True, type=Path)
    command.add_argument("--lessons", required=True, type=Path)
    for action in ("approve", "reject"):
        command = subs.add_parser(action)
        command.add_argument("--lesson-id", required=True)
        command.add_argument("--lessons", required=True, type=Path)
        if action == "approve":
            command.add_argument("--approval-ref", required=True)
            command.add_argument("--approved-by")
    command = subs.add_parser("compare")
    command.add_argument("--note", required=True, type=Path)
    command.add_argument("--lessons", required=True, type=Path)
    command.add_argument("--session-prefix", required=True)
    return result


def run(args):
    if args.command == "draft":
        paths = [args.note, args.lessons]
        if args.out:
            paths.extend([args.out, Path(str(args.out) + ".note.json")])
        distinct(paths)
        note = load(args.note, "research_note.v1")
        result = draft(note, approved_for(note, read_log(args.lessons, "lesson.v1")), args.session_id)
        if args.out:
            require(not args.out.exists() and not Path(str(args.out) + ".note.json").exists(),
                    "salida ya existe; no se sobrescribe")
            save_new(Path(str(args.out) + ".note.json"), note)
            save_new(args.out, result)
        return result
    if args.command == "feedback":
        note_path = Path(str(args.draft) + ".note.json")
        distinct([args.draft, note_path, args.feedback_log])
        note = load(note_path, "research_note.v1")
        document = load(args.draft, "draft.v1")
        result = make_feedback(note, document, args.reviewer, args.rating, args.comment,
                               args.target_facts.split(","), args.correction)
        read_log(args.feedback_log, "feedback.v1")  # Validar antes de escribir auxiliares.
        note_context, draft_context = context_paths(args.feedback_log, result["feedback_id"])
        note_context.parent.mkdir(exist_ok=True)
        save_new(note_context, note)
        save_new(draft_context, document)
        append_log(args.feedback_log, result)
        return result
    if args.command == "propose":
        distinct([args.feedback_log, args.lessons])
        records = read_log(args.feedback_log, "feedback.v1")
        found = [f for f in records if f["feedback_id"] == args.feedback]
        if not found:
            supplied = load(args.feedback, "feedback.v1")
            found = [f for f in records if f == supplied]
        require(len(found) == 1, "feedback no registrado en feedback-log")
        feedback = found[0]
        note_path, draft_path = context_paths(args.feedback_log, feedback["feedback_id"])
        distinct([args.lessons, note_path, draft_path])
        result = propose_candidate(load(note_path, "research_note.v1"), load(draft_path, "draft.v1"), feedback)
        append_log(args.lessons, result)
        return result
    if args.command in ("approve", "reject"):
        actor = getattr(args, "approved_by", None)
        ref = getattr(args, "approval_ref", None)
        if args.command == "approve" and actor is None and ref.startswith("fixture:"):
            actor = "fixture_simulated"
        return transition(args.lessons, args.lesson_id,
                          "approved" if args.command == "approve" else "rejected", ref, actor)
    distinct([args.note, args.lessons])
    return compare(args.note, args.lessons, args.session_prefix)


def main(argv=None):
    try:
        result = run(parser().parse_args(argv))
        print(encoded(result))
        return 1 if result.get("outcome") == "failed" else 0
    except (Invalid, OSError, UnicodeError, subprocess.SubprocessError, RuntimeError) as exc:
        # No volcar contenido sensible de entrada en errores.
        message = str(exc) if isinstance(exc, Invalid) else type(exc).__name__
        print(encoded({"outcome": "invalid", "error": message}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
