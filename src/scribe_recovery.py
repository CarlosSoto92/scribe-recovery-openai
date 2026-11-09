"""Fase 0: tarea CSV sintética, Scribe determinista y un solo reintento."""

import argparse
import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path


TASK_ID = "sum_inventory_v1"
FIELDS = ["producto", "cantidad"]
DELIMITERS = ",;\t|"


class DemoError(ValueError):
    """Entrada o historial inválido; no ejecutar la tarea."""


class TaskFailure(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def read_ledger(path):
    """Leer todo el historial antes de agregar; un fragmento no se repara."""
    path = Path(path)
    if not path.exists():
        return []
    raw = path.read_text(encoding="utf-8")
    if raw and not raw.endswith("\n"):
        raise DemoError("LEDGER_INVALID: falta salto de línea final")
    events = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DemoError(f"LEDGER_INVALID: JSON en línea {line_number}") from exc
        if not isinstance(event, dict) or not all(
            key in event for key in (
                "run_id", "task_id", "input_sha256", "attempt", "timestamp",
                "error", "lesson", "outcome", "result", "evidence",
            )
        ):
            raise DemoError(f"LEDGER_INVALID: evento en línea {line_number}")
        if (
            not all(isinstance(event[key], str) and event[key]
                    for key in ("run_id", "task_id", "timestamp", "input_sha256"))
            or type(event["attempt"]) is not int
            or event["attempt"] not in (1, 2)
            or event["outcome"] not in ("failed", "success")
            or not isinstance(event["evidence"], dict)
            or (event["lesson"] is not None and not isinstance(event["lesson"], dict))
            or (event["error"] is not None and not isinstance(event["error"], dict))
        ):
            raise DemoError(f"LEDGER_INVALID: tipos en línea {line_number}")
        events.append(event)
    return events


def sum_inventory(text, delimiter):
    reader = csv.DictReader(io.StringIO(text), delimiter=delimiter, strict=True)
    if reader.fieldnames != FIELDS:
        raise TaskFailure("CSV_SCHEMA", f"columnas observadas {reader.fieldnames!r}; esperadas {FIELDS!r}")
    total, count = 0, 0
    for row in reader:
        if None in row or any(row[field] is None for field in FIELDS):
            raise TaskFailure("CSV_ROW", "fila con número incorrecto de campos")
        try:
            quantity = int(row["cantidad"])
        except ValueError as exc:
            raise TaskFailure("CSV_VALUE", "cantidad debe ser un entero") from exc
        total += quantity
        count += 1
    if not count:
        raise TaskFailure("CSV_EMPTY", "no hay filas de inventario")
    return {"total": total, "rows": count}


def extract_lesson(text, error):
    """Scribe inspecciona el encabezado; no corrige ni repite la tarea."""
    if error["code"] != "CSV_SCHEMA":
        return None
    header = text.splitlines()[0] if text.splitlines() else ""
    candidates = []
    for delimiter in DELIMITERS:
        if header_matches_fields(header, delimiter):
            candidates.append(delimiter)
    if len(candidates) != 1:
        return None
    return {"kind": "csv_delimiter", "delimiter": candidates[0], "observed_header": header}


def header_matches_fields(header, delimiter):
    try:
        return next(csv.reader([header], delimiter=delimiter, strict=True)) == FIELDS
    except csv.Error:
        return False


def run_attempt(version, input_path, ledger_path, run_id):
    """Ejecutar una sola vez y devolver el evento que se agregó al ledger."""
    if version not in ("v1", "v2") or not isinstance(run_id, str) or not run_id.strip():
        raise DemoError("version/run_id inválido")
    input_path, ledger_path = Path(input_path), Path(ledger_path)
    if input_path.resolve() == ledger_path.resolve() or (
        ledger_path.exists() and input_path.samefile(ledger_path)
    ):
        raise DemoError("INPUT_LEDGER_CONFLICT: el ledger no puede ser la entrada")
    raw = input_path.read_bytes()
    text = raw.decode("utf-8")
    fingerprint = hashlib.sha256(raw).hexdigest()
    events = read_ledger(ledger_path)
    related = [event for event in events if (
        event["run_id"] == run_id and event["task_id"] == TASK_ID
        and event["input_sha256"] == fingerprint
    )]
    attempt = 1 if version == "v1" else 2
    if any(event["attempt"] == attempt for event in related) or (version == "v1" and related):
        raise DemoError("ATTEMPT_ALREADY_RECORDED: usa otro run_id; máximo un reintento")
    delimiter, source_attempt = ",", None
    if version == "v2":
        previous = [event for event in related if event["attempt"] == 1]
        if len(previous) > 1:
            raise DemoError("LEDGER_INVALID: intento 1 duplicado")
        if previous and previous[0]["lesson"] is not None:
            source = previous[0]
            lesson = source["lesson"]
            if (
                source["outcome"] != "failed"
                or not isinstance(source["error"], dict)
                or source["error"].get("code") != "CSV_SCHEMA"
                or lesson.get("kind") != "csv_delimiter"
                or not isinstance(lesson.get("delimiter"), str)
                or len(lesson["delimiter"]) != 1
                or lesson["delimiter"] not in DELIMITERS
                or lesson.get("observed_header") != (text.splitlines()[0] if text.splitlines() else "")
                or not header_matches_fields(lesson["observed_header"], lesson["delimiter"])
            ):
                raise DemoError("LESSON_INCOMPATIBLE: lección no aplicable a esta tarea")
            try:
                fields = next(csv.reader([lesson["observed_header"]],
                                         delimiter=lesson["delimiter"], strict=True))
            except csv.Error as exc:
                raise DemoError("LESSON_INCOMPATIBLE: encabezado inválido") from exc
            if fields != FIELDS:
                raise DemoError("LESSON_INCOMPATIBLE: separador incompatible con encabezado")
            delimiter = lesson["delimiter"]
            source_attempt = 1
    error, lesson, result = None, None, None
    try:
        result = sum_inventory(text, delimiter)
    except (TaskFailure, csv.Error) as exc:
        error = {"code": getattr(exc, "code", "CSV_PARSE"), "message": str(exc)}
        if version == "v1":
            try:
                lesson = extract_lesson(text, error)
            except csv.Error:
                lesson = None
    event = {
        "run_id": run_id, "task_id": TASK_ID, "input_sha256": fingerprint,
        "attempt": attempt, "timestamp": datetime.now(timezone.utc).isoformat(),
        "error": error, "lesson": lesson,
        "outcome": "failed" if error else "success", "result": result,
        "evidence": {"delimiter_used": delimiter, "lesson_source_attempt": source_attempt},
    }
    # Solo agregar. No creamos carpetas ni reparamos historiales inválidos.
    with ledger_path.open("a", encoding="utf-8", newline="\n") as ledger:
        ledger.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", choices=("v1", "v2"))
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--ledger", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args(argv)
    try:
        event = run_attempt(args.version, args.input, args.ledger, args.run_id)
    except (OSError, UnicodeError, DemoError) as exc:
        print(json.dumps({"outcome": "invalid", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(event, ensure_ascii=False))
    return 0 if event["outcome"] == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
