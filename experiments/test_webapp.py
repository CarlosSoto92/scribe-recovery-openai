"""Persistencia y flujo HTTP local de la demo; sin servicios externos."""

from copy import deepcopy
from html.parser import HTMLParser
import http.client
from io import BytesIO
from pathlib import Path
import sqlite3
import tempfile
from threading import Thread
from types import SimpleNamespace
import unittest
from urllib.parse import urlencode
from unittest.mock import patch

if __package__:
    from . import webapp as web
else:
    import webapp as web


class ComparisonText(HTMLParser):
    """Leer los borradores visibles y sus marcas, sin incluir la leyenda o tablas."""

    def __init__(self, html):
        super().__init__()
        self.drafts = []
        self.marks = {"diff-add": [], "diff-del": []}
        self.in_draft = False
        self.mark = None
        self.draft_tags = []
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "p" and attributes.get("class") == "draft-text":
            self.in_draft = True
            self.drafts.append("")
        elif self.in_draft:
            self.draft_tags.append(tag)
            if tag == "mark":
                self.mark = attributes["class"]
                self.marks[self.mark].append("")

    def handle_endtag(self, tag):
        if tag == "p":
            self.in_draft = False
        elif tag == "mark":
            self.mark = None

    def handle_data(self, data):
        if self.in_draft:
            self.drafts[-1] += data
            if self.mark:
                self.marks[self.mark][-1] += data


class StoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-web-test-")
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "demo.db"
        self.store = web.Store(self.path)
        self.note = web.ed.load(web.FIXTURE, "research_note.v1")

    def propose(self):
        document = self.store.generate(self.note)
        return self.store.feedback(self.note, document["draft_id"], "fixture_simulated", 2,
                                   "Falta la duración del piloto.", ["f1"])

    def test_insert_read_persist_and_duplicate_rejected(self):
        document = self.store.generate(self.note)
        self.assertEqual(web.Store(self.path).read("draft.v1"), [document])
        before = self.store.history()
        with self.assertRaises(web.ed.Invalid):
            self.store.append(document)
        self.assertEqual(self.store.history(), before)
        with sqlite3.connect(str(self.path)) as db:
            for statement in ("UPDATE events SET label='alterado'", "DELETE FROM events"):
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute(statement)
        self.assertEqual(self.store.history(), before)

    def test_proposed_approve_reject_is_append_only_and_controls_writer(self):
        proposed = self.propose()
        prefix = self.store.history()
        self.assertEqual(web.ed.approved_for(self.note, self.store.read("lesson.v1")), [])
        negative = self.store.compare(self.note)
        for branch in negative.values():
            self.assertEqual(branch["check"][web.METRIC], 0)
            self.assertEqual(branch["draft"]["applied_lesson_ids"], [])
        approved = self.store.transition(proposed["lesson_id"], "approved", "fixture:web-test", "fixture_simulated")
        self.assertEqual(approved["version"], 2)
        self.assertEqual(self.store.history()[:len(prefix)], prefix)
        self.assertEqual(web.ed.approved_for(self.note, self.store.read("lesson.v1")), [approved])
        branches = self.store.compare(self.note)
        self.assertEqual(branches["B−"]["check"][web.METRIC], 0)
        self.assertEqual(branches["B+"]["check"][web.METRIC], 1)
        self.assertEqual(branches["B+"]["draft"]["applied_lesson_ids"], [approved["lesson_id"] + "@v2"])
        self.assertEqual(self.store.generate(self.note)["fact_refs"], ["f1"])
        self.store.transition(proposed["lesson_id"], "rejected")
        self.assertEqual([d["state"] for d in self.store.read("lesson.v1")], ["proposed", "approved", "rejected"])
        self.assertEqual(web.ed.approved_for(self.note, self.store.read("lesson.v1")), [])
        self.assertEqual(self.store.generate(self.note)["fact_refs"], [])

    def test_invalid_gate_and_transition_never_append(self):
        lesson = self.propose()
        before = self.store.history()
        for ref, actor in (("", "carlos"), ("  ", "carlos"), ("decision-l4:test", ""),
                           ("fixture:test", "carlos"), ("decision-l4:test", "fixture_simulated")):
            with self.subTest(ref=ref, actor=actor), self.assertRaises(web.ed.Invalid):
                self.store.transition(lesson["lesson_id"], "approved", ref, actor)
            self.assertEqual(self.store.history(), before)
        self.store.transition(lesson["lesson_id"], "rejected")
        before = self.store.history()
        with self.assertRaises(web.ed.Invalid):
            self.store.transition(lesson["lesson_id"], "approved", "fixture:test", "fixture_simulated")
        self.assertEqual(self.store.history(), before)

    def test_reject_proposed_and_invalid_feedback_rolls_back(self):
        document = self.store.generate(self.note)
        before = self.store.history()
        for targets in ([], ["missing"], ["f2"]):
            with self.subTest(targets=targets), self.assertRaises(web.ed.Invalid):
                self.store.feedback(self.note, document["draft_id"], "fixture_simulated", 2, "Corregir", targets)
            self.assertEqual(self.store.history(), before)
        lesson = self.propose()
        self.store.transition(lesson["lesson_id"], "rejected")
        self.assertEqual(web.ed.approved_for(self.note, self.store.read("lesson.v1")), [])

    def test_repo_db_and_symlink_alias_refused_before_creation(self):
        forbidden = web.ROOT / "experiments/forbidden-demo.db"
        with self.assertRaises(web.ed.Invalid):
            web.Store(forbidden)
        self.assertFalse(forbidden.exists())
        alias = self.path.parent / "repo-alias"
        alias.symlink_to(web.ROOT, target_is_directory=True)
        with self.assertRaises(web.ed.Invalid):
            web.Store(alias / "forbidden-demo.db")

    def test_presence_and_citation_are_independent_observations(self):
        document = self.store.generate(self.note)
        fact = self.note["facts"][0]
        for text, expected in ((fact["text"], '<td>Sí</td><td>No</td><td>FAIL</td>'),
                               ('[synthetic-note-001:f1]', '<td>No</td><td>Sí</td><td>FAIL</td>')):
            altered = deepcopy(document)
            altered["text"] = text
            altered["fact_refs"] = ["f1"]
            self.assertIn(expected, web.fact_table(self.note, altered))

    def test_comparison_marks_approved_fact_and_citation_without_fake_negative_text(self):
        lesson = self.propose()
        self.store.transition(lesson["lesson_id"], "approved", "fixture:diff", "fixture_simulated")
        branches = self.store.compare(self.note)
        before = deepcopy(branches)
        html = web.comparison_html(self.note, branches)
        parsed = ComparisonText(html)
        added = ''.join(parsed.marks["diff-add"])
        self.assertIn(self.note["facts"][0]["text"], added)
        self.assertIn('[synthetic-note-001:f1]', added)
        self.assertEqual(parsed.marks["diff-del"], [])
        self.assertEqual(parsed.drafts, [branches[label]["draft"]["text"] for label in ("B−", "B+")])
        self.assertEqual(branches, before)
        for label, expected in (("B−", '<td>No</td><td>No</td><td>FAIL</td>'),
                                ("B+", '<td>Sí</td><td>Sí</td><td>PASS</td>')):
            table = web.fact_table(self.note, branches[label]["draft"])
            self.assertIn(table, html)
            self.assertIn(expected, table)

    def test_comparison_legend_explains_colors_omissions_and_checker_boundary(self):
        html = web.comparison_html(self.note, self.store.compare(self.note))
        for text in ('Leyenda del diff:', 'Verde: texto agregado en B+',
                     'Rojo: texto de B− eliminado o sustituido en B+',
                     'Si B− solo omite un dato', 'no hay texto que marcar en rojo en B−',
                     'diff de texto del borrador, no un juicio del checker'):
            self.assertIn(text, html)

    def test_comparison_identical_drafts_have_no_marks_for_proposed_or_rejected(self):
        lesson = self.propose()
        for state in ("proposed", "rejected"):
            with self.subTest(state=state):
                if state == "rejected":
                    self.store.transition(lesson["lesson_id"], state)
                branches = self.store.compare(self.note)
                parsed = ComparisonText(web.comparison_html(self.note, branches))
                self.assertEqual(parsed.drafts[0], parsed.drafts[1])
                self.assertEqual(parsed.marks, {"diff-add": [], "diff-del": []})

    def test_comparison_replacements_and_deletions_mark_only_original_text(self):
        branches = self.store.compare(self.note)
        for minus, plus, deleted, added in (
                ("El piloto fue breve.", "El piloto duró 4 semanas.", "fue breve.", "duró 4 semanas."),
                ("Texto común. Sobra.", "Texto común.", " Sobra.", ""),
                ("Inicio.\nFinal.", "Inicio.\nDato nuevo.\nFinal.", "", "Dato nuevo.")):
            with self.subTest(minus=minus, plus=plus):
                for label, text in (("B−", minus), ("B+", plus)):
                    branches[label]["draft"]["text"] = text
                    branches[label]["check"] = web.ed.check_draft(self.note, branches[label]["draft"])
                parsed = ComparisonText(web.comparison_html(self.note, branches))
                self.assertEqual(parsed.drafts, [minus, plus])
                for kind, expected in (("diff-del", deleted), ("diff-add", added)):
                    if expected:
                        marked = ' '.join(' '.join(parsed.marks[kind]).split())
                        self.assertIn(' '.join(expected.split()), marked)
                    else:
                        self.assertEqual(parsed.marks[kind], [])

    def test_comparison_escapes_dangerous_drafts_and_comments(self):
        document = self.store.generate(self.note)
        comment = '</textarea><script>alert("comment")</script>'
        self.store.feedback(self.note, document["draft_id"], "fixture_simulated", 2, comment, ["f1"])
        branches = self.store.compare(self.note)
        common = '<img src=x onerror="alert(1)"> & "común" '
        minus = common + '</p><script>alert("minus")</script>'
        plus = common + '</mark><script>alert("plus")</script>'
        for label, text in (("B−", minus), ("B+", plus)):
            branches[label]["draft"]["text"] = text
        html = web.page(self.store, self.note, "csrf", branches=branches,
                        feedback_form={"comment": [comment]}, script_nonce="test-nonce")
        parsed = ComparisonText(html)
        self.assertEqual(parsed.drafts, [minus, plus])
        self.assertEqual(set(parsed.draft_tags), {"mark"})
        for raw in ('<script>', '<img ', '</textarea><script>', '</mark><script>'):
            self.assertNotIn(raw, html)
        for escaped in (web.h(common), web.h(comment), web.h(minus[len(common):]), web.h(plus[len(common):])):
            self.assertIn(escaped, html)
        self.assertEqual(parsed.marks["diff-del"], [minus[len(common):]])
        self.assertEqual(parsed.marks["diff-add"], [plus[len(common):]])


class Inputs(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hidden = {}
        self.forms = {}
        self.current_form = None
        self.textarea = None
        self.script_nonce = None
        self.script = ""
        self.in_script = False
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "form":
            self.current_form = {"inputs": [], "comment": ""}
            self.forms.setdefault(attributes["action"], []).append(self.current_form)
        if tag == "input" and self.current_form is not None:
            self.current_form["inputs"].append(attributes)
        if tag == "input" and attributes.get("type") == "hidden":
            self.hidden[attributes["name"]] = attributes.get("value", "")
        if tag == "textarea" and self.current_form is not None:
            self.textarea = self.current_form
        if tag == "script":
            self.script_nonce = attributes.get("nonce")
            self.in_script = True

    def handle_endtag(self, tag):
        if tag == "form":
            self.current_form = None
        elif tag == "textarea":
            self.textarea = None
        elif tag == "script":
            self.in_script = False

    def handle_data(self, data):
        if self.textarea is not None:
            self.textarea["comment"] += data
        if self.in_script:
            self.script += data

    def field(self, action, name):
        return next(field for field in self.forms["/action/" + action][0]["inputs"]
                    if field.get("name") == name)


class HTTPTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-web-http-")
        self.addCleanup(temporary.cleanup)
        self.store = web.Store(Path(temporary.name) / "demo.db")
        try:
            self.server = web.make_server(self.store, 0)
        except PermissionError as exc:
            self.skipTest(f"Sandbox sin sockets loopback: {exc}")
        self.thread = Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.01})
        self.thread.start()
        self.addCleanup(self.stop_server)
        status, html = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.csrf = Inputs(html).hidden["csrf"]

    def stop_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.assertFalse(self.thread.is_alive())

    def request(self, method, path, fields=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        try:
            body = urlencode(fields, doseq=True) if fields is not None else None
            request_headers = {"Host": f"127.0.0.1:{self.server.server_port}",
                               "Content-Type": "application/x-www-form-urlencoded"}
            request_headers.update(headers or {})
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            self.response_headers = dict(response.getheaders())
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def post(self, action, **fields):
        return self.request("POST", "/action/" + action, dict(csrf=self.csrf, **fields))

    def test_host_validation_uses_assigned_port(self):
        port = self.server.server_port
        self.assertEqual(port, self.server.server_address[1])
        self.assertEqual(self.request("GET", "/", headers={"Host": f"localhost:{port}"})[0], 200)
        other_port = (port + 1) % 65536
        self.assertEqual(self.request("GET", "/", headers={"Host": f"127.0.0.1:{other_port}"})[0], 400)

    def test_feedback_invalid_csrf_does_not_preserve_untrusted_fields(self):
        self.assertEqual(self.post("draft")[0], 200)
        document = self.store.read("draft.v1")[-1]
        before = self.store.history()
        for csrf in (None, "incorrecto", "ñ", [self.csrf, "incorrecto"]):
            with self.subTest(csrf=csrf):
                fields = dict(draft_id="attacker-draft", reviewer="attacker-reviewer",
                              rating="5", comment="attacker-comment", target=["f1", "f2"])
                if csrf is not None:
                    fields["csrf"] = csrf
                status, html = self.request("POST", "/action/feedback", fields)
                self.assertEqual(status, 400)
                parsed = Inputs(html)
                form = parsed.forms["/action/feedback"][0]
                self.assertEqual(form["comment"], "")
                for name, value in (("draft_id", document["draft_id"]), ("reviewer", "carlos"), ("rating", "2")):
                    self.assertEqual(parsed.field("feedback", name)["value"], value)
                self.assertFalse(any("checked" in field for field in form["inputs"]
                                     if field.get("name") == "target"))
                self.assertNotIn("attacker-", html)
                self.assertEqual(self.store.history(), before)

    def test_feedback_400_preserves_fields_and_can_be_corrected(self):
        self.assertEqual(self.post("draft")[0], 200)
        document = self.store.read("draft.v1")[-1]
        before = self.store.history()
        comment = '  Falta duración & fuente.\n</textarea><script>alert("x")</script>  '
        reviewer = 'carlos "editor" <review>'
        for targets, rating in (([], "4"), (["f2"], "3"), (["f1", "f2"], "6")):
            with self.subTest(targets=targets, rating=rating):
                status, html = self.post("feedback", draft_id=document["draft_id"],
                                         reviewer=reviewer, rating=rating, comment=comment, target=targets)
                self.assertEqual(status, 400)
                parsed = Inputs(html)
                self.assertEqual(parsed.forms["/action/feedback"][0]["comment"], comment)
                for name, value in (("reviewer", reviewer), ("rating", rating), ("draft_id", document["draft_id"])):
                    self.assertEqual(parsed.field("feedback", name)["value"], value)
                checked = [field["value"] for field in parsed.forms["/action/feedback"][0]["inputs"]
                           if field.get("name") == "target" and "checked" in field]
                self.assertEqual(checked, targets)
                self.assertNotIn('<script>alert(', html)
                self.assertIn('&lt;/textarea&gt;&lt;script&gt;', html)
                self.assertEqual(self.store.history(), before)
        status, _ = self.post("feedback", draft_id=document["draft_id"], reviewer=reviewer,
                              rating="4", comment=comment, target=["f1"])
        self.assertEqual(status, 200)
        self.assertEqual(self.store.read("feedback.v1")[-1]["comment"], comment)

    def test_feedback_sqlite_error_preserves_comment(self):
        self.post("draft")
        document = self.store.read("draft.v1")[-1]
        with patch.object(self.store, "feedback", side_effect=sqlite3.OperationalError("test")):
            status, html = self.post("feedback", draft_id=document["draft_id"], reviewer="carlos",
                                     rating="5", comment="Mi corrección sigue aquí", target=["f1"])
        self.assertEqual(status, 400)
        self.assertEqual(Inputs(html).forms["/action/feedback"][0]["comment"], "Mi corrección sigue aquí")

    def test_feedback_client_validation_targets_only_must_keep_and_csp_allows_script(self):
        status, html = self.post("draft")
        self.assertEqual(status, 200)
        parsed = Inputs(html)
        targets = [field for field in parsed.forms["/action/feedback"][0]["inputs"]
                   if field.get("name") == "target"]
        self.assertEqual([field["value"] for field in targets if "data-must-keep" in field], ["f1"])
        self.assertTrue(all("required" not in field for field in targets))
        self.assertIn('Marca al menos un hecho crítico (must_keep)', html)
        for code in ('input[name="target"][data-must-keep]', 'criticalFacts.some(input => input.checked)',
                     'setCustomValidity', "addEventListener('change', validateTargets)",
                     "addEventListener('submit'", 'event.preventDefault()', 'feedbackForm.reportValidity()'):
            self.assertIn(code, parsed.script)
        self.assertTrue(parsed.script_nonce)
        csp = self.response_headers["Content-Security-Policy"]
        self.assertIn(f"script-src 'nonce-{parsed.script_nonce}'", csp)
        self.assertIn("default-src 'none'", csp)
        self.assertNotIn("script-src 'unsafe-inline'", csp)
        self.request("GET", "/")
        self.assertNotEqual(csp, self.response_headers["Content-Security-Policy"])

    def test_approval_prefills_latest_reviewer_but_requires_explicit_reference(self):
        self.post("draft")
        document = self.store.read("draft.v1")[-1]
        for reviewer, reference in (("carlos", "decision-l4:test"), ('editor "L4" <human>', "decision-l4:test"),
                                    ("fixture_simulated", "fixture:web-test")):
            with self.subTest(reviewer=reviewer):
                status, _ = self.post("feedback", draft_id=document["draft_id"], reviewer=reviewer,
                                      rating="2", comment="Falta duración", target=["f1"])
                self.assertEqual(status, 200)
                before = self.store.history()
                status, html = self.request("GET", "/")
                self.assertEqual(status, 200)
                parsed = Inputs(html)
                self.assertEqual(parsed.field("feedback", "reviewer")["value"], reviewer)
                for form in parsed.forms["/action/approve"]:
                    inputs = {field["name"]: field for field in form["inputs"]}
                    self.assertEqual(inputs["approved_by"]["value"], reviewer)
                    self.assertEqual(inputs["approval_ref"]["value"], "")
                    self.assertEqual(inputs["approval_ref"]["placeholder"], "decision-l4:demo")
                    self.assertIn("required", inputs["approved_by"])
                    self.assertIn("required", inputs["approval_ref"])
                self.assertEqual(self.store.history(), before)
                lesson = self.store.read("lesson.v1")[-1]
                self.assertEqual(lesson["state"], "proposed")
                for missing in ("approved_by", "approval_ref"):
                    fields = dict(lesson_id=lesson["lesson_id"], approved_by=reviewer, approval_ref=reference)
                    fields[missing] = ""
                    self.assertEqual(self.post("approve", **fields)[0], 400)
                    self.assertEqual(self.store.history(), before)
                self.assertEqual(self.post("approve", lesson_id=lesson["lesson_id"],
                                           approved_by=reviewer, approval_ref=reference)[0], 200)
                self.assertEqual(self.store.read("lesson.v1")[-1]["state"], "approved")

    def test_full_loop_and_revocation(self):
        self.assertEqual(self.server.server_address[0], "127.0.0.1")
        status, html = self.post("draft")
        self.assertEqual(status, 200)
        document = self.store.read("draft.v1")[-1]
        status, html = self.post("feedback", draft_id=document["draft_id"], reviewer="fixture_simulated",
                                 rating="2", comment="Falta la duración <script>alert(1)</script>", target=["f1"])
        self.assertEqual(status, 200)
        self.assertIn("Lección propuesta — aún no se aplica", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)
        self.assertEqual(self.store.read("feedback.v1")[0]["draft_id"], document["draft_id"])
        lesson = self.store.read("lesson.v1")[0]
        status, html = self.post("compare")
        self.assertEqual(status, 200)
        self.assertIn("B+ · FAIL", html)
        self.assertNotIn('<mark class="diff-add">', html)
        before = self.store.history()
        status, html = self.post("approve", lesson_id=lesson["lesson_id"], approval_ref="", approved_by="fixture_simulated")
        self.assertEqual(status, 400)
        self.assertIn("approved exige approved_by y approval_ref", html)
        self.assertEqual(self.store.history(), before)
        status, html = self.post("approve", lesson_id=lesson["lesson_id"], approval_ref="fixture:http-test", approved_by="fixture_simulated")
        self.assertEqual(status, 200)
        status, html = self.post("compare")
        self.assertEqual(status, 200)
        for text in ("B− · FAIL", "B+ · PASS", "<th>dato literal</th>", "<th>cita</th>", "0/1 (0%)", "1/1 (100%)", lesson["lesson_id"] + "@v2"):
            self.assertIn(text, html)
        self.assertIn('<mark class="diff-add">', html)
        self.assertNotIn('<mark class="diff-del">', html)
        self.assertIn('Leyenda del diff:', html)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertEqual(self.post("reject", lesson_id=lesson["lesson_id"])[0], 200)
        status, html = self.post("compare")
        self.assertEqual(status, 200)
        self.assertIn("B+ · FAIL", html)
        self.assertNotIn('<mark class="diff-add">', html)
        self.assertEqual([d["version"] for d in self.store.read("lesson.v1")], [1, 2, 3])
        # Reabrir la DB mantiene todos los eventos y sus IDs.
        self.assertEqual(web.Store(self.store.path).history(), self.store.history())

    def test_bad_requests_are_readable_and_do_not_write(self):
        for action, fields in (("feedback", {}), ("approve", {"lesson_id": "missing"}),
                               ("unknown", {}), ("feedback", {"draft_id": "missing", "reviewer": "x", "rating": "bad", "comment": "x"})):
            with self.subTest(action=action):
                status, html = self.post(action, **fields)
                self.assertEqual(status, 400)
                self.assertIn('<html lang="es">', html)
        for fields in ({}, {"csrf": "incorrecto"}, {"csrf": "ñ"}):
            self.assertEqual(self.request("POST", "/action/draft", fields)[0], 400)
        self.assertEqual(self.request("POST", "/action/draft", {"csrf": self.csrf}, {"Host": "evil.example"})[0], 400)
        self.assertEqual(self.request("GET", "/missing")[0], 404)
        self.assertEqual(self.store.history(), [])


class MemoryHTTPTests(HTTPTests):
    """Mismo flujo por el parser HTTP real, sin abrir sockets en el sandbox."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-web-memory-http-")
        self.addCleanup(temporary.cleanup)
        self.store = web.Store(Path(temporary.name) / "demo.db")
        self.csrf = "test-form-token"
        self.server = SimpleNamespace(store=self.store, note=web.ed.load(web.FIXTURE, "research_note.v1"),
                                      csrf=self.csrf, server_port=0,
                                      server_address=("127.0.0.1", 0))

    def request(self, method, path, fields=None, headers=None):
        body = urlencode(fields, doseq=True).encode("utf-8") if fields is not None else b""
        request_headers = {"Host": f"127.0.0.1:{self.server.server_port}", "Content-Type": "application/x-www-form-urlencoded",
                           "Content-Length": str(len(body))}
        request_headers.update(headers or {})
        raw = (f"{method} {path} HTTP/1.0\r\n" + ''.join(
            f"{key}: {value}\r\n" for key, value in request_headers.items()) + "\r\n").encode("ascii") + body

        class Connection:
            def __init__(self, content):
                self.input = BytesIO(content)
                self.output = BytesIO()

            def makefile(self, *args):
                return self.input

            def sendall(self, content):
                self.output.write(content)

        connection = Connection(raw)
        web.Handler(connection, ("127.0.0.1", 12345), self.server)
        response = http.client.HTTPResponse(Connection(connection.output.getvalue()))
        try:
            response.begin()
            self.response_headers = dict(response.getheaders())
            return response.status, response.read().decode("utf-8")
        finally:
            response.close()


if __name__ == "__main__":
    unittest.main()
