"""Documentos B2B sintéticos: lección por tipo, gate humano, writer y checker.

Fase 0. No hay LLM, red, llaves ni datos reales. El writer sin lección tiene
la falla codificada a propósito: demuestra el mecanismo, no la calidad de un
modelo. Las notas se tratan como datos; nunca se ejecuta su contenido.

lesson.v1 y el loop editorial no se modifican. Este módulo los importa.
"""

import argparse
from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

import scribe_editorial as ed


DOC_TYPES = (
    "cotizacion",
    "propuesta_tecnica",
    "ficha_tecnica",
    "reporte_cliente",
    "respuesta_soporte",
)
RULE_TYPES = (
    "required_clause",
    "cite_source",
    "unit_format",
    "next_step",
    "forbidden_claim",
)
RULE_OF = {
    "cotizacion": "required_clause",
    "propuesta_tecnica": "cite_source",
    "ficha_tecnica": "unit_format",
    "reporte_cliente": "next_step",
    "respuesta_soporte": "forbidden_claim",
}
DOC_LABEL = {
    "cotizacion": "Cotización",
    "propuesta_tecnica": "Propuesta técnica",
    "ficha_tecnica": "Ficha técnica",
    "reporte_cliente": "Reporte a cliente",
    "respuesta_soporte": "Respuesta de soporte",
}
CLAUSE_VIGENCIA = "Vigencia: 15 días naturales"
CLAUSE_PAGO = "Pago: 50 % anticipo, 50 % contra entrega"
FORBIDDEN = ("garantizamos", "solución definitiva")
WEAK_CLAIM = "Garantizamos una solución definitiva."
FIXED_CLOCK = "2026-11-10T15:00:00Z"
GAP_LABEL = {
    "cotizacion": "Falta vigencia y condiciones de pago",
    "propuesta_tecnica": "Falta la referencia de ficha junto a la cifra",
    "ficha_tecnica": "Falta la presión en bar y la temperatura en °C",
    "reporte_cliente": "Falta el siguiente paso con responsable y fecha",
    "respuesta_soporte": "Hay una promesa prohibida y falta el folio",
}
REVIEW = {
    "cotizacion": {
        "comment": "Otra vez sin vigencia.",
        "correction": "Incluir el texto literal de vigencia y de condiciones de pago.",
    },
    "propuesta_tecnica": {
        "comment": "Otra vez las cifras sin la ficha.",
        "correction": "Cerrar cada afirmación numérica con (Ref. FT-xxx) de la nota.",
    },
    "ficha_tecnica": {
        "comment": "Otra vez la presión solo en psi.",
        "correction": "Escribir la presión en bar y psi, y la temperatura en °C.",
    },
    "reporte_cliente": {
        "comment": "Otra vez el reporte no dice quién sigue.",
        "correction": "Cerrar con la línea Siguiente paso, responsable y fecha de la nota.",
    },
    "respuesta_soporte": {
        "comment": "Otra vez prometemos de más y se nos olvida el folio.",
        "correction": "Quitar la promesa prohibida e incluir el folio SOP de la nota.",
    },
}
RULE_TEXT = {
    "required_clause": "En toda cotización, incluye la vigencia y el pago con el texto literal de la casa.",
    "cite_source": "Cada afirmación numérica va seguida de la referencia de ficha tomada del hecho.",
    "unit_format": "La presión se escribe en bar y en psi; la temperatura, en grados Celsius.",
    "next_step": "El reporte cierra con responsable y fecha: Siguiente paso, tomados de la nota.",
    "forbidden_claim": "No prometas garantía ni solución definitiva, e incluye el folio SOP de la nota.",
}
PRESSURE = re.compile(r"(\d+(?:[.,]\d+)?) bar \((\d+(?:[.,]\d+)?) psi\)")
DASHES = str.maketrans({"—": "-", "–": "-", "−": "-", "‑": "-"})


def normalize(text):
    """Mayúsculas, espacios y guion/raya equivalentes. No cambia el significado."""
    folded = text.casefold().translate(DASHES)
    return re.sub(r"\s+", " ", folded).strip()


def loose(text):
    return normalize(text).replace("-", " ")


def require_house_shape(note):
    """La nota trae, como hechos, la convención que el checker va a medir."""
    critical = [fact for fact in note["facts"] if fact["must_keep"]]
    ed.require(critical, "el documento no trae requisitos críticos")
    ed.require(any(not fact["must_keep"] for fact in note["facts"]), "faltan hechos de contexto")
    rule = RULE_OF[note["doc_type"]]
    if rule == "required_clause":
        texts = [fact["text"] for fact in critical]
        ed.require(CLAUSE_VIGENCIA in texts and CLAUSE_PAGO in texts, "la cotización no trae las cláusulas de la casa")
    elif rule == "cite_source":
        for fact in critical:
            ed.require(re.search(r"\d", fact["text"]) is not None, "la cifra crítica no es numérica")
            ed.require(re.fullmatch(r"FT-\d{3}", fact["source_ref"]) is not None, "source_ref de ficha inválido")
    elif rule == "unit_format":
        joined = "\n".join(fact["text"] for fact in critical)
        ed.require(PRESSURE.search(joined) is not None, "falta la presión canónica en bar y psi")
        ed.require(" °C" in joined, "falta la temperatura en °C")
    elif rule == "next_step":
        ed.require(any(fact["text"].startswith("Siguiente paso: ") and " · " in fact["text"] for fact in critical),
                   "falta la línea de siguiente paso")
    else:
        ed.require(any(re.search(r"SOP-\d{4}", fact["text"]) for fact in critical), "falta el folio SOP-nnnn")
        blob = loose("\n".join(fact["text"] for fact in note["facts"]))
        ed.require(all(loose(phrase) not in blob for phrase in FORBIDDEN),
                   "la frase prohibida no puede venir como hecho de la nota")


def validate_note(document):
    ed.require(isinstance(document, dict), "documento debe ser objeto")
    ed.require(document.get("schema_version") == "doc_note.v1", "schema_version incompatible")
    ed.fields(document, "schema_version note_id doc_type company customer facts limits synthetic")
    ed.require(ed.identifier(document["note_id"]), "note_id inválido")
    ed.require(document["doc_type"] in DOC_TYPES, "doc_type inválido")
    ed.require(document["synthetic"] is True, "Fase 0 solo admite synthetic true")
    company = document["company"]
    ed.fields(company, "name rfc email phone city")
    ed.require(all(ed.string(company[key]) for key in company), "empresa inválida")
    ed.require("FICTICIA" in company["name"], "la empresa debe identificarse como FICTICIA")
    _email(company["email"])
    ed.require(company["phone"].startswith("+52 000"), "teléfono fuera del rango ficticio")
    customer = document["customer"]
    ed.fields(customer, "name email")
    ed.require(ed.string(customer["name"]), "cliente inválido")
    _email(customer["email"])
    facts = document["facts"]
    ed.require(isinstance(facts, list) and facts, "facts vacío o inválido")
    for fact in facts:
        ed.fields(fact, "fact_id text must_keep source_ref")
        ed.require(ed.identifier(fact["fact_id"]) and ed.string(fact["text"]), "fact inválido")
        ed.require(type(fact["must_keep"]) is bool, "must_keep debe ser booleano")
        ed.require(ed.identifier(fact["source_ref"]), "source_ref inválido")
    ed.strings([fact["fact_id"] for fact in facts], ids=True)
    ed.strings(document["limits"], nonempty=True)
    require_house_shape(document)
    return document


def _email(value):
    ed.require(ed.string(value) and value.count("@") == 1, "correo inválido")
    domain = value.split("@", 1)[1].lower()
    ed.require(domain.endswith(".example") and ".." not in domain, "el correo debe usar el dominio .example")


def validate_feedback(document):
    ed.require(isinstance(document, dict), "documento debe ser objeto")
    ed.require(document.get("schema_version") == "doc_feedback.v1", "schema_version incompatible")
    ed.fields(document, "schema_version feedback_id note_id reviewer rating comment target_fact_ids correction created_at")
    ed.require(ed.identifier(document["feedback_id"]) and ed.identifier(document["note_id"]), "ID inválido")
    ed.require(ed.string(document["reviewer"]) and ed.string(document["comment"]), "feedback vacío")
    ed.require(type(document["rating"]) is int and 1 <= document["rating"] <= 5, "rating debe ser entero 1-5")
    ed.strings(document["target_fact_ids"], ids=True, nonempty=True)
    ed.require(document["correction"] is None or ed.string(document["correction"]), "correction inválida")
    ed.utc(document["created_at"])
    return document


def validate_lesson(document):
    ed.require(isinstance(document, dict), "documento debe ser objeto")
    ed.require(document.get("schema_version") == "lesson.v2", "schema_version incompatible")
    ed.fields(document, "schema_version lesson_id version source_feedback_id scope rule params evidence state approved_by approval_ref created_at")
    ed.require(ed.identifier(document["lesson_id"]) and ed.identifier(document["source_feedback_id"]), "ID inválido")
    ed.require(type(document["version"]) is int and document["version"] >= 1, "version inválida")
    scope = document["scope"]
    ed.fields(scope, "task doc_type rule_type")
    ed.require(scope["task"] == "b2b_document", "task inválida")
    ed.require(scope["doc_type"] in DOC_TYPES and scope["rule_type"] == RULE_OF[scope["doc_type"]], "alcance inválido")
    ed.require(ed.string(document["rule"]), "regla vacía")
    _params(scope["rule_type"], document["params"])
    evidence = document["evidence"]
    ed.fields(evidence, "note_id fact_ids")
    ed.require(ed.identifier(evidence["note_id"]), "note_id de evidencia inválido")
    ed.strings(evidence["fact_ids"], ids=True, nonempty=True)
    ed.require(document["state"] in ("proposed", "approved", "rejected"), "estado inválido")
    if document["state"] == "approved":
        ed.require(ed.string(document["approved_by"]) and ed.string(document["approval_ref"]),
                   "approved exige approved_by y approval_ref")
        simulated = document["approved_by"] == "fixture_simulated"
        ed.require(simulated == document["approval_ref"].startswith("fixture:"),
                   "aprobación fixture debe atribuirse solo a fixture_simulated")
    else:
        ed.require(document["approved_by"] is None and document["approval_ref"] is None,
                   "estado no aprobado debe tener aprobación null")
    ed.utc(document["created_at"])
    return document


def _params(rule_type, params):
    ed.require(isinstance(params, dict), "params inválidos")
    if rule_type == "required_clause":
        ed.fields(params, "clauses")
        ed.strings(params["clauses"], nonempty=True)
    elif rule_type == "cite_source":
        ed.fields(params, "ref_template")
        ed.require(params["ref_template"] == "(Ref. {source_ref})", "ref_template inválido")
    elif rule_type == "unit_format":
        ed.fields(params, "pressure temperature")
        ed.require(params["pressure"] == "bar_and_psi" and params["temperature"] == "celsius", "formato inválido")
    elif rule_type == "next_step":
        ed.fields(params, "prefix")
        ed.require(params["prefix"] == "Siguiente paso:", "prefix inválido")
    else:
        ed.fields(params, "forbidden folio_pattern")
        ed.require(params["forbidden"] == list(FORBIDDEN), "lista prohibida inválida")
        ed.require(params["folio_pattern"] == "SOP-nnnn", "folio_pattern inválido")


def validate_draft(document):
    ed.require(isinstance(document, dict), "documento debe ser objeto")
    ed.require(document.get("schema_version") == "doc_draft.v1", "schema_version incompatible")
    ed.fields(document, "schema_version note_id doc_type applied_lesson_ids text status")
    ed.require(ed.identifier(document["note_id"]) and document["doc_type"] in DOC_TYPES, "borrador inválido")
    ed.strings(document["applied_lesson_ids"])
    ed.require(all(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]*@v[1-9][0-9]*", item)
                   for item in document["applied_lesson_ids"]), "referencia de lección inválida")
    ed.require(ed.string(document["text"]) and document["status"] == "needs_human_review", "borrador inválido")
    return document


def latest_lessons(events):
    latest = {}
    for event in events:
        validate_lesson(event)
        old = latest.get(event["lesson_id"])
        if old is not None:
            ed.require(event["version"] == old["version"] + 1, "version no consecutiva")
            ed.require((old["state"], event["state"]) in {
                ("proposed", "approved"), ("proposed", "rejected"), ("approved", "rejected")},
                "transición inválida")
            mutable = {"version", "state", "approved_by", "approval_ref", "created_at"}
            ed.require(all(event[key] == old[key] for key in old if key not in mutable),
                       "provenance/regla alterada en transición")
            ed.require(_stamp(event["created_at"]) >= _stamp(old["created_at"]),
                       "timestamp de transición anterior al origen")
        latest[event["lesson_id"]] = event
    return list(latest.values())


def _stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_lesson_log(path):
    """Historial completo, no solo el snapshot vigente. Valida la cadena."""
    path = Path(path)
    try:
        raw = path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        ed.require(not path.is_symlink(), "log apunta a un enlace sin destino")
        return []
    ed.require(not raw or raw.endswith("\n"), "JSONL incompleto: falta LF final; no se repara")
    records = [validate_lesson(ed.parse_json(line)) for line in raw.split("\n")[:-1]]
    latest_lessons(records)
    return records


def append_lesson(path, record):
    validate_lesson(record)
    records = read_lesson_log(path)
    latest_lessons(records + [record])
    with Path(path).open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(ed.encoded(record) + "\n")


def approved_for_doc(note, lessons):
    """Lecciones approved del mismo tipo de documento, no del mismo note_id.

    Una lección nacida en la semana 1 aplica a las semanas siguientes del
    mismo doc_type. Otro tipo, u otro estado, no entra al writer.
    """
    validate_note(note)
    return [lesson for lesson in latest_lessons(lessons)
            if lesson["state"] == "approved"
            and lesson["scope"]["task"] == "b2b_document"
            and lesson["scope"]["doc_type"] == note["doc_type"]
            and lesson["scope"]["rule_type"] == RULE_OF[note["doc_type"]]]


def render_document(note, text):
    """Membrete ficticio más cuerpo. Texto plano, sin HTML."""
    validate_note(note)
    ed.require(ed.string(text), "cuerpo vacío")
    company = note["company"]
    customer = note["customer"]
    header = "\n".join((
        company["name"],
        f"RFC {company['rfc']} · {company['email']} · {company['phone']}",
        company["city"],
        f"Cliente: {customer['name']} · {customer['email']}",
        f"Documento: {DOC_LABEL[note['doc_type']]} · {note['note_id']}",
    ))
    return header + "\n\n" + text.strip() + "\n"


def _critical(note):
    return [fact for fact in note["facts"] if fact["must_keep"]]


def _weaken(fact):
    text = PRESSURE.sub(lambda match: f"{match.group(2)} psi", fact["text"])
    return text.replace(" °C", "")


def weak_lines(note):
    """La falla de la casa, a propósito, cuando no hay lección approved."""
    rule = RULE_OF[note["doc_type"]]
    if rule == "cite_source":
        return [fact["text"] for fact in _critical(note)]
    if rule == "unit_format":
        return [_weaken(fact) for fact in _critical(note)]
    if rule == "forbidden_claim":
        return [WEAK_CLAIM]
    return []


def corrected_lines(note, lesson):
    """Corrige con los hechos de ESTA nota. No copia cifras de la nota origen."""
    validate_lesson(lesson)
    ed.require(lesson["state"] == "approved", "writer solo recibe approved")
    ed.require(lesson["scope"]["doc_type"] == note["doc_type"], "la lección es de otro tipo de documento")
    rule = lesson["scope"]["rule_type"]
    critical = _critical(note)
    if rule == "required_clause":
        allowed = set(lesson["params"]["clauses"])
        return [fact["text"] for fact in critical if fact["text"] in allowed]
    if rule == "cite_source":
        template = lesson["params"]["ref_template"]
        return [f"{fact['text']} {template.format(source_ref=fact['source_ref'])}" for fact in critical]
    if rule == "next_step":
        prefix = lesson["params"]["prefix"]
        return [fact["text"] for fact in critical if fact["text"].startswith(prefix)]
    return [fact["text"] for fact in critical]


def draft(note, lessons):
    validate_note(note)
    chosen = sorted(approved_for_doc(note, lessons), key=lambda item: item["lesson_id"])
    lines = [fact["text"] for fact in note["facts"] if not fact["must_keep"]]
    if chosen:
        for lesson in chosen:
            lines.extend(corrected_lines(note, lesson))
        applied = sorted(f"{lesson['lesson_id']}@v{lesson['version']}" for lesson in chosen)
    else:
        lines.extend(weak_lines(note))
        applied = []
    document = {
        "schema_version": "doc_draft.v1",
        "note_id": note["note_id"],
        "doc_type": note["doc_type"],
        "applied_lesson_ids": applied,
        "text": render_document(note, "\n".join(lines)),
        "status": "needs_human_review",
    }
    return validate_draft(document)


def check_document(note, text):
    validate_note(note)
    ed.require(isinstance(text, str) and text.strip(), "texto vacío")
    rule = RULE_OF[note["doc_type"]]
    norm = normalize(text)
    folded = loose(text)
    requirements = []
    for fact in _critical(note):
        if rule == "cite_source":
            expected = normalize(f"{fact['text']} (Ref. {fact['source_ref']})")
            ok = expected in norm
            detail = f"Falta la referencia (Ref. {fact['source_ref']}) junto a «{fact['text']}»."
        else:
            ok = normalize(fact["text"]) in norm
            detail = f"Falta el texto de la nota «{fact['text']}»."
        if rule == "next_step" and ok:
            ok = normalize(fact["text"]).startswith("siguiente paso:")
        requirements.append({"id": fact["fact_id"], "ok": ok, "detail": detail})
    if rule == "forbidden_claim":
        for phrase in FORBIDDEN:
            ok = loose(phrase) not in folded
            requirements.append({
                "id": f"forbidden:{phrase}",
                "ok": ok,
                "detail": f"Aparece la frase prohibida «{phrase}».",
            })
        expected = [found for fact in _critical(note) for found in re.findall(r"SOP-\d{4}", fact["text"])]
        present = re.findall(r"SOP-\d{4}", text)
        ok = bool(expected) and all(folio in present for folio in expected)
        requirements.append({
            "id": "folio",
            "ok": ok,
            "detail": "Falta el folio SOP-nnnn de la nota.",
        })
    met = sum(1 for item in requirements if item["ok"])
    failures = [item["detail"] for item in requirements if not item["ok"]]
    return {
        "doc_type": note["doc_type"],
        "rule_type": rule,
        "met": met,
        "total": len(requirements),
        "compliant": bool(requirements) and met == len(requirements),
        "failures": failures,
        "requirements": requirements,
    }


def _plain_markdown(text):
    """Quita delimitadores de presentación, conservando cifras y puntuación."""
    for marker in ("**", "__", "`", "*", "_"):
        text = re.sub(re.escape(marker) + r"(.+?)" + re.escape(marker), r"\1", text)
    return text


def _fact_segments(text):
    """Una línea, fila o viñeta con sus continuaciones indentadas por segmento."""
    segments = []
    bullet = False
    for raw in text.splitlines():
        line = _plain_markdown(raw).strip()
        if not line:
            bullet = False
            continue
        if line.startswith("|") and line.endswith("|"):
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            line = cells[0].rstrip(":") + ": " + " ".join(cells[1:])
            bullet = False
        elif re.match(r"(?:[-+*]|\d+[.)])\s+", line):
            bullet = True
        elif bullet and raw[:1].isspace():
            segments[-1] += " " + line
            continue
        else:
            bullet = False
        segments.append(line)
    return [normalize(segment) for segment in segments]


def _contains_exact(segment, expected):
    return re.search(r"(?<!\w)" + re.escape(normalize(expected)) + r"(?!\w)", segment) is not None


def _affirmative_forbidden(text, phrase):
    # No inferimos alcance semántico: solo las negaciones inmediatas enumeradas.
    negation = r"no\s+" if phrase == "garantizamos" else r"(?:no hay|sin)\s+"
    folded = loose(_plain_markdown(text))
    for match in re.finditer(r"\b" + re.escape(loose(phrase)) + r"\b", folded):
        if not re.search(r"\b" + negation + r"$", folded[:match.start()]):
            return True
    return False


def check_document_tolerant(note, text):
    """Mismos requisitos que el estricto; admite forma markdown y negación simple.

    Las unidades y cifras se conservan literalmente. Las referencias se buscan
    solo en el segmento del valor, nunca en el resto del documento.
    """
    result = check_document(note, text)
    segments = _fact_segments(text)
    rule = result["rule_type"]
    critical = _critical(note)
    for fact, requirement in zip(critical, result["requirements"]):
        folios = re.findall(r"SOP-\d{4}", fact["text"])
        if rule == "forbidden_claim" and folios:
            requirement["ok"] = all(_contains_exact(normalize(text), folio) for folio in folios)
        else:
            requirement["ok"] = any(
                _contains_exact(segment, fact["text"])
                and (rule != "cite_source" or _contains_exact(segment, f"(Ref. {fact['source_ref']})"))
                for segment in segments
            )
    for requirement in result["requirements"][len(critical):]:
        if requirement["id"].startswith("forbidden:"):
            phrase = requirement["id"].split(":", 1)[1]
            requirement["ok"] = not _affirmative_forbidden(text, phrase)
        elif requirement["id"] == "folio":
            expected = [folio for fact in critical for folio in re.findall(r"SOP-\d{4}", fact["text"])]
            requirement["ok"] = bool(expected) and all(_contains_exact(normalize(text), folio) for folio in expected)
    result["met"] = sum(item["ok"] for item in result["requirements"])
    result["failures"] = [item["detail"] for item in result["requirements"] if not item["ok"]]
    result["compliant"] = bool(result["total"]) and result["met"] == result["total"]
    return result


def regression(note, reference, candidate):
    """Hechos no críticos, cero frases prohibidas nuevas y longitud ±25 %."""
    validate_note(note)
    missing = [fact["fact_id"] for fact in note["facts"]
               if not fact["must_keep"] and fact["text"] not in candidate]
    known = {phrase for phrase in FORBIDDEN if loose(phrase) in loose(reference)}
    added = [phrase for phrase in FORBIDDEN if loose(phrase) in loose(candidate) and phrase not in known]
    ratio = (len(candidate) / len(reference)) if reference else None
    within = ratio is not None and 0.75 <= ratio <= 1.25
    return {
        "noncritical_missing": missing,
        "new_forbidden": added,
        "length_ratio": ratio,
        "within_length": within,
        "ok": not missing and not added and within,
    }


def make_feedback(note, reviewer, rating, comment, targets, correction=None, created_at=None):
    validate_note(note)
    created_at = created_at or ed.now()
    feedback = {
        "schema_version": "doc_feedback.v1",
        "note_id": note["note_id"],
        "reviewer": reviewer,
        "rating": rating,
        "comment": comment,
        "target_fact_ids": list(targets),
        "correction": correction,
        "created_at": created_at,
    }
    feedback["feedback_id"] = ed.stable_id("fb-", feedback)
    validate_feedback(feedback)
    known = {fact["fact_id"] for fact in note["facts"]}
    ed.require(set(targets) <= known, "target_fact_ids desconocidos")
    ed.require(any(fact["must_keep"] and fact["fact_id"] in targets for fact in note["facts"]),
               "feedback no apunta a must_keep")
    return feedback


def propose_lesson(note, feedback, created_at=None):
    validate_note(note)
    validate_feedback(feedback)
    ed.require(feedback["note_id"] == note["note_id"], "feedback de otra nota")
    known = {fact["fact_id"]: fact for fact in note["facts"]}
    ed.require(set(feedback["target_fact_ids"]) <= set(known), "target_fact_ids desconocidos")
    targets = [fact_id for fact_id in feedback["target_fact_ids"] if known[fact_id]["must_keep"]]
    ed.require(bool(targets), "feedback no apunta a must_keep")
    rule = RULE_OF[note["doc_type"]]
    lesson = {
        "schema_version": "lesson.v2",
        "lesson_id": ed.stable_id("lesson-", feedback["feedback_id"]),
        "version": 1,
        "source_feedback_id": feedback["feedback_id"],
        "scope": {"task": "b2b_document", "doc_type": note["doc_type"], "rule_type": rule},
        "rule": RULE_TEXT[rule],
        "params": _params_from(note, targets),
        "evidence": {"note_id": note["note_id"], "fact_ids": targets},
        "state": "proposed",
        "approved_by": None,
        "approval_ref": None,
        "created_at": created_at or feedback["created_at"],
    }
    return validate_lesson(lesson)


def _params_from(note, targets):
    rule = RULE_OF[note["doc_type"]]
    chosen = [fact for fact in note["facts"] if fact["fact_id"] in targets]
    if rule == "required_clause":
        return {"clauses": [fact["text"] for fact in chosen]}
    if rule == "cite_source":
        return {"ref_template": "(Ref. {source_ref})"}
    if rule == "unit_format":
        return {"pressure": "bar_and_psi", "temperature": "celsius"}
    if rule == "next_step":
        return {"prefix": "Siguiente paso:"}
    return {"forbidden": list(FORBIDDEN), "folio_pattern": "SOP-nnnn"}


def transition_event(events, lesson_id, state, approval_ref=None, approved_by=None, created_at=None):
    latest = {record["lesson_id"]: record for record in latest_lessons(events)}
    ed.require(lesson_id in latest, "lesson_id desconocido")
    event = deepcopy(latest[lesson_id])
    event.update(version=event["version"] + 1, state=state, approval_ref=approval_ref,
                 approved_by=approved_by, created_at=created_at or ed.now())
    latest_lessons(events + [event])
    return event


def simulate_approval(note, approval_ref, created_at=FIXED_CLOCK):
    """Flujo de demostración: feedback → proposed → approved con fixture_simulated.

    El reloj es fijo para que la evaluación sea reproducible. No es una
    aprobación de una persona.
    """
    review = REVIEW[note["doc_type"]]
    targets = [fact["fact_id"] for fact in note["facts"] if fact["must_keep"]]
    feedback = make_feedback(note, "fixture_simulated", 2, review["comment"], targets,
                             review["correction"], created_at)
    proposed = propose_lesson(note, feedback, created_at)
    approved = transition_event([proposed], proposed["lesson_id"], "approved",
                                approval_ref, "fixture_simulated", created_at)
    return {"feedback": feedback, "events": [proposed, approved], "lesson": approved}


def write_new(path, document):
    validate_draft(document)
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(ed.encoded(document) + "\n")


def load_note(path):
    return validate_note(ed.parse_json(Path(path).read_text(encoding="utf-8")))


def iter_fixtures(root):
    root = Path(root)
    paths = sorted(root.glob("*/*.json"))
    ed.require(len(paths) == 20, "se esperaban 20 fixtures B2B")
    return [(path, load_note(path)) for path in paths]


def case_number(note):
    match = re.search(r"-(\d+)$", note["note_id"])
    ed.require(match is not None, "note_id sin número de caso")
    return int(match.group(1))


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ed.Invalid(message)


def parser():
    result = Parser(description=__doc__)
    commands = result.add_subparsers(dest="command", required=True)
    command = commands.add_parser("draft")
    command.add_argument("--note", required=True, type=Path)
    command.add_argument("--lessons", required=True, type=Path)
    command.add_argument("--out", type=Path)
    command = commands.add_parser("check")
    command.add_argument("--note", required=True, type=Path)
    command.add_argument("--text", required=True, type=Path)
    return result


def run(args):
    if args.command == "draft":
        paths = [args.note, args.lessons]
        if args.out:
            paths.append(args.out)
        ed.distinct(paths)
        note = load_note(args.note)
        result = draft(note, read_lesson_log(args.lessons))
        if args.out:
            ed.require(not args.out.exists(), "salida ya existe; no se sobrescribe")
            write_new(args.out, result)
        return result
    note = load_note(args.note)
    text = Path(args.text).read_text(encoding="utf-8")
    return check_document(note, text)


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        result = run(args)
        print(ed.encoded(result))
        if args.command == "check" and not result["compliant"]:
            return 1
        return 0
    except (ed.Invalid, OSError, UnicodeError, json.JSONDecodeError) as exc:
        message = str(exc) if isinstance(exc, ed.Invalid) else type(exc).__name__
        print(ed.encoded({"outcome": "invalid", "error": message}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
