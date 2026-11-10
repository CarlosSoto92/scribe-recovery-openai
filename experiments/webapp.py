"""Demo web local y sintética del loop editorial; Python 3 stdlib, sin API."""

import argparse
from contextlib import contextmanager
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
import secrets
import sqlite3
import sys
from urllib.parse import parse_qs
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import scribe_editorial as ed

FIXTURE = ROOT / "experiments/fixtures/synthetic_note_001.json"
METRIC = "retención de hechos críticos"
KINDS = {"draft.v1": "draft_id", "feedback.v1": "feedback_id", "lesson.v1": "lesson_id"}


class Store:
    """Eventos JSON validados, append-only; una transacción por acción."""

    def __init__(self, path):
        self.path = Path(path).resolve()
        ed.require(self.path != ROOT and ROOT not in self.path.parents,
                   "La DB debe estar fuera del repo")
        with self.connection() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY,
                    kind TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    UNIQUE(kind, record_id, version)
                );
                CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
                BEGIN SELECT RAISE(ABORT, 'historial append-only'); END;
                CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
                BEGIN SELECT RAISE(ABORT, 'historial append-only'); END;
            """)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(str(self.path))
        try:
            with db:
                db.execute("BEGIN IMMEDIATE")
                yield db
        finally:
            db.close()

    def rows(self, db):
        return [(seq, label, ed.validate(ed.parse_json(payload), kind))
                for seq, kind, label, payload in db.execute(
                    "SELECT seq, kind, label, payload FROM events ORDER BY seq")]

    def records(self, db, schema):
        return [document for _, _, document in self.rows(db)
                if document["schema_version"] == schema]

    def history(self):
        with self.connection() as db:
            return self.rows(db)

    def read(self, schema):
        with self.connection() as db:
            return self.records(db, schema)

    def insert(self, db, document, label=""):
        ed.validate(document)
        kind = document["schema_version"]
        ed.require(kind in KINDS, "Tipo de evento no admitido")
        if kind == "lesson.v1":
            ed.latest_lessons(self.records(db, kind) + [document])
        try:
            db.execute("INSERT INTO events(kind, record_id, version, label, payload) "
                       "VALUES (?, ?, ?, ?, ?)",
                       (kind, document[KINDS[kind]], document.get("version", 1),
                        label, ed.encoded(document)))
        except sqlite3.IntegrityError as exc:
            raise ed.Invalid("Evento duplicado o historial incompatible") from exc
        return document

    def append(self, document):
        with self.connection() as db:
            return self.insert(db, document)

    def generate(self, note):
        with self.connection() as db:
            selected = ed.approved_for(note, self.records(db, "lesson.v1"))
            return self.insert(db, ed.draft(note, selected, "web-" + uuid4().hex), "V1")

    def feedback(self, note, draft_id, reviewer, rating, comment, targets):
        with self.connection() as db:
            documents = [d for d in self.records(db, "draft.v1") if d["draft_id"] == draft_id]
            ed.require(len(documents) == 1, "Borrador desconocido; genera V1 primero")
            feedback = ed.make_feedback(note, documents[0], reviewer, rating, comment, targets)
            lesson = ed.propose_candidate(note, documents[0], feedback)
            self.insert(db, feedback)
            self.insert(db, lesson)
            return lesson

    def transition(self, lesson_id, state, approval_ref=None, approved_by=None):
        with self.connection() as db:
            event = ed.transition_event(self.records(db, "lesson.v1"), lesson_id, state,
                                        approval_ref, approved_by)
            return self.insert(db, event)

    def compare(self, note):
        with self.connection() as db:
            selected = ed.approved_for(note, self.records(db, "lesson.v1"))
            prefix = "web-" + uuid4().hex
            branches = {}
            for label, lessons, suffix in (("B−", [], "minus"), ("B+", selected, "plus")):
                document = self.insert(db, ed.draft(note, lessons, prefix + "-" + suffix), label)
                branches[label] = {"draft": document, "check": ed.check_draft(note, document)}
            return branches


def h(value):
    return escape(str(value), quote=True)


def fact_table(note, document):
    """Presencia textual y cita son observaciones separadas del checker."""
    check = ed.check_draft(note, document)
    rows = []
    for fact in note["facts"]:
        fact_id = fact["fact_id"]
        present = fact["text"] in document["text"]
        cited = f'[{note["note_id"]}:{fact_id}]' in document["text"]
        retained = fact_id in check["retained_fact_ids"]
        rows.append(f'<tr><td>{h(fact_id)}</td><td>{"Sí" if present else "No"}</td>'
                    f'<td>{"Sí" if cited else "No"}</td>'
                    f'<td>{("PASS" if retained else "FAIL") if fact["must_keep"] else "No crítico"}</td></tr>')
    return ('<table><tr><th>Fact</th><th>dato literal</th><th>cita</th>'
            '<th>Checker crítico</th></tr>' + ''.join(rows) + '</table>')


def comparison_html(note, branches):
    panels = []
    for label, branch in branches.items():
        document, check = branch["draft"], branch["check"]
        passed = check[METRIC] == 1.0
        metric = f'{len(check["retained_fact_ids"])}/{check["critical_total"]}'
        panels.append(f'<article><h3>{h(label)} · {"PASS" if passed else "FAIL"}</h3>'
                      f'<p>{h(document["text"])}</p>{fact_table(note, document)}'
                      f'<p>Retención: {h(metric)} ({check[METRIC]:.0%})</p>'
                      f'<p>Lecciones usadas: {h(", ".join(document["applied_lesson_ids"]) or "ninguna")}</p>'
                      '</article>')
    return '<div class="comparison">' + ''.join(panels) + '</div>'


def page(store, note, token, message="", branches=None, feedback_form=None, script_nonce=""):
    history = store.history()
    drafts = [d for _, label, d in history if label == "V1"]
    latest = ed.latest_lessons([d for _, _, d in history if d["schema_version"] == "lesson.v1"])
    reviewers = [d["reviewer"] for _, _, d in history if d["schema_version"] == "feedback.v1"]
    reviewer = reviewers[-1] if reviewers else "carlos"
    feedback_form = feedback_form if feedback_form is not None else {}

    def entered(name, default=""):
        return feedback_form.get(name, [default])[0]

    def form(action, content):
        return (f'<form method="post" action="/action/{action}">'
                f'<input type="hidden" name="csrf" value="{h(token)}">{content}</form>')

    facts = ''.join(f'<li class="{"critical" if f["must_keep"] else ""}">{h(f["fact_id"])}: '
                    f'{h(f["text"])} {"— must_keep=true" if f["must_keep"] else ""}</li>'
                    for f in note["facts"])
    targets = ''.join(f'<label><input type="checkbox" name="target" value="{h(f["fact_id"])}"'
                      f'{" data-must-keep" if f["must_keep"] else ""}'
                      f'{" checked" if f["fact_id"] in feedback_form.get("target", []) else ""}>'
                      f'{h(f["fact_id"])}: {h(f["text"])}'
                      f'{" — must_keep" if f["must_keep"] else ""}</label>' for f in note["facts"])
    correction = '<p>Genera un borrador antes de corregirlo.</p>'
    if drafts:
        correction = form("feedback", f'<input type="hidden" name="draft_id" value="{h(entered("draft_id", drafts[-1]["draft_id"]))}">'
                          f'<label>Reviewer <input name="reviewer" value="{h(entered("reviewer", reviewer))}" required></label>'
                          f'<label>Rating (1–5) <input type="number" name="rating" min="1" max="5" value="{h(entered("rating", "2"))}" required></label>'
                          f'<label>Comentario <textarea name="comment" required>{h(entered("comment"))}</textarea></label>'
                          f'<fieldset aria-describedby="target-help"><legend>Target facts (al menos un must_keep)</legend>{targets}'
                          '<p id="target-help">Marca al menos un hecho crítico (must_keep) para guardar la corrección.</p></fieldset>'
                          '<button>Guardar corrección y proponer lección</button>')
    lessons_html = ''
    for lesson in latest:
        lessons_html += (f'<article><h3>{h(lesson["lesson_id"])}@v{lesson["version"]} · {h(lesson["state"])}</h3>'
                         f'<p>{h(lesson["rule"])}</p><p>Facts: {h(", ".join(lesson["evidence"]["fact_ids"]))}</p>')
        identity = f'<input type="hidden" name="lesson_id" value="{h(lesson["lesson_id"])}">'
        if lesson["state"] == "proposed":
            approval_ref = "fixture:web-review" if reviewer == "fixture_simulated" else "review-l4:auto"
            lessons_html += '<p>Lección propuesta — aún no se aplica</p>' + form("approve", identity +
                            f'<label>approved_by <input name="approved_by" value="{h(reviewer)}" required></label>'
                            f'<label>approval_ref <input name="approval_ref" value="{h(approval_ref)}" placeholder="decision-l4:demo" required></label>'
                            '<button>Aprobar lección</button>')
        if lesson["state"] in ("proposed", "approved"):
            lessons_html += form("reject", identity + '<button>Rechazar lección</button>')
        lessons_html += '</article>'
    rows = ''.join(f'<tr><td>{seq}</td><td>{h(d["schema_version"])} {h(label)}</td>'
                   f'<td>{h(d[KINDS[d["schema_version"]]])}</td><td>{h(d.get("version", "—"))}</td>'
                   f'<td>{h(d.get("state", d.get("status", "registrado")))}</td>'
                   f'<td><details><summary>Ver registro</summary><pre>{h(ed.encoded(d))}</pre></details></td></tr>'
                   for seq, label, d in history)
    return f'''<!doctype html><html lang="es"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Scribe · Loop editorial V0</title>
<style>
body{{font:16px system-ui,sans-serif;background:#f4f6f8;color:#182637;max-width:1100px;margin:2rem auto;padding:0 1rem}}
section,article{{background:white;border:1px solid #dce2e9;border-radius:8px;padding:1rem;margin:1rem 0}}
h1,h2,h3{{line-height:1.3}}h3,pre{{overflow-wrap:anywhere}}pre{{white-space:pre-wrap}}
.critical{{font-weight:700;background:#fff0c6;padding:.5rem}}li{{margin:.5rem 0}}
label{{display:block;margin:.7rem 0}}input,textarea,button{{font:inherit;padding:.5rem}}textarea{{display:block;width:95%}}
button{{background:#174f85;color:white;border:0;border-radius:5px;cursor:pointer;margin:.4rem 0}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}}td,th{{text-align:left;padding:.5rem;border-bottom:1px solid #ddd;overflow-wrap:anywhere}}
.comparison{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}}.notice{{padding:1rem;background:#e4eef9}}
@media(max-width:700px){{.comparison{{grid-template-columns:1fr}}}}.history{{overflow-x:auto}}
</style><body><h1>Scribe · Loop editorial V0</h1>
<p>Demo local · datos sintéticos · writer determinista. Copia los hechos autorizados de la nota; no usa LLM ni API.</p>
<p>La aprobación registra una declaración humana; no autentica identidad ni verifica la referencia en GitHub.</p>
{f'<p class="notice">{h(message)}</p>' if message else ''}
<section><h2>1. Nota sintética</h2><p>{h(note["topic"])}</p><ul>{facts}</ul><p>{h(" ".join(note["limits"]))}</p></section>
<section><h2>2. Borrador V1</h2>{form("draft", '<button>Generar borrador V1</button>')}
{f'<p>{h(drafts[-1]["text"])}</p><p>Lecciones usadas: {h(", ".join(drafts[-1]["applied_lesson_ids"]) or "ninguna")}</p>' if drafts else ''}</section>
<section><h2>3. Tu corrección</h2>{correction}</section>
<section><h2>4. Revisar y aprobar lección</h2>{lessons_html or '<p>Sin lecciones todavía.</p>'}</section>
<section><h2>5. Comparar</h2><p>B− sin lecciones; B+ solo con approved vigentes. Mismo writer y checker literal; invocaciones separadas en este proceso.</p>
{form("compare", '<button>Comparar</button>')}{comparison_html(note, branches) if branches else ''}</section>
<section class="history"><h2>Historial SQLite · append-only</h2><table><tr><th>#</th><th>Tipo</th><th>ID</th><th>Versión</th><th>Estado</th><th>Contenido</th></tr>{rows}</table></section>
<script nonce="{h(script_nonce)}">
const feedbackForm = document.querySelector('form[action="/action/feedback"]');
if (feedbackForm) {{
    const criticalFacts = Array.from(feedbackForm.querySelectorAll('input[name="target"][data-must-keep]'));
    function validateTargets() {{
        const valid = criticalFacts.some(input => input.checked);
        if (criticalFacts.length) {{
            criticalFacts[0].setCustomValidity(valid ? '' : 'Marca al menos un hecho crítico (must_keep) para guardar la corrección.');
        }}
        return valid;
    }}
    feedbackForm.addEventListener('change', validateTargets);
    feedbackForm.addEventListener('submit', event => {{
        if (!validateTargets()) {{
            event.preventDefault();
            feedbackForm.reportValidity();
        }}
    }});
    validateTargets();
}}
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # No registrar comentarios ni entradas del operador.

    def respond(self, status, message="", branches=None, feedback_form=None):
        nonce = secrets.token_urlsafe(16)
        body = page(self.server.store, self.server.note, self.server.csrf, message, branches,
                    feedback_form, nonce).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def valid_host(self):
        return self.headers.get("Host") in (f'127.0.0.1:{self.server.server_port}',
                                             f'localhost:{self.server.server_port}')

    def do_GET(self):
        if not self.valid_host():
            self.respond(400, "Host inválido; usa la URL local indicada")
        elif self.path != "/":
            self.respond(404, "Ruta desconocida")
        else:
            self.respond(200)

    def do_POST(self):
        feedback_form = None
        try:
            ed.require(self.valid_host(), "Host inválido; usa la URL local indicada")
            ed.require(self.headers.get("Content-Type", "").split(";")[0] ==
                       "application/x-www-form-urlencoded", "Se esperaba un formulario")
            length = int(self.headers.get("Content-Length", "0"))
            ed.require(0 < length <= 32768, "Formulario vacío o demasiado grande")
            form = parse_qs(self.rfile.read(length).decode("utf-8"), keep_blank_values=True,
                            max_num_fields=100)
            if self.path == "/action/feedback":
                feedback_form = form

            def one(key):
                values = form.get(key, [])
                ed.require(len(values) == 1, f"Campo requerido o repetido: {key}")
                return values[0]

            ed.require(secrets.compare_digest(one("csrf").encode("utf-8"),
                                              self.server.csrf.encode("utf-8")),
                       "Formulario vencido o inválido; recarga la página")
            store, note = self.server.store, self.server.note
            branches, message = None, "Acción registrada"
            if self.path == "/action/draft":
                store.generate(note)
                message = "Borrador generado con las lecciones approved vigentes"
            elif self.path == "/action/feedback":
                store.feedback(note, one("draft_id"), one("reviewer"), int(one("rating")),
                               one("comment"), form.get("target", []))
                message = "Lección propuesta — aún no se aplica"
            elif self.path == "/action/approve":
                store.transition(one("lesson_id"), "approved", one("approval_ref"), one("approved_by"))
            elif self.path == "/action/reject":
                store.transition(one("lesson_id"), "rejected")
            elif self.path == "/action/compare":
                branches = store.compare(note)
                message = "Comparación registrada con el mismo checker"
            else:
                raise ed.Invalid("Acción desconocida")
            self.respond(200, message, branches)
        except (ed.Invalid, ValueError, UnicodeError) as exc:
            message = str(exc) if isinstance(exc, ed.Invalid) else "Formulario inválido; revisa los campos"
            self.respond(400, message, feedback_form=feedback_form)
        except sqlite3.Error:
            self.respond(400, "No se pudo registrar la acción en SQLite", feedback_form=feedback_form)


def make_server(store, port=8765):
    server = HTTPServer(("127.0.0.1", port), Handler)
    server.store = store
    server.note = ed.load(FIXTURE, "research_note.v1")
    server.csrf = secrets.token_urlsafe(32)
    return server


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", type=Path, default=Path("/tmp/scribe-web.db"))
    args = parser.parse_args(argv)
    try:
        ed.require(0 <= args.port <= 65535, "Puerto inválido")
        with make_server(Store(args.db), args.port) as server:
            print(f"Scribe: http://127.0.0.1:{server.server_port}/ · DB: {server.store.path}", flush=True)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
        return 0
    except (ed.Invalid, OSError, sqlite3.Error) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
