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

import webapp as web


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


class Inputs(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.hidden = {}
        self.feed(html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == "input" and attributes.get("type") == "hidden":
            self.hidden[attributes["name"]] = attributes.get("value", "")


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
            request_headers = {"Content-Type": "application/x-www-form-urlencoded"}
            request_headers.update(headers or {})
            connection.request(method, path, body=body, headers=request_headers)
            response = connection.getresponse()
            return response.status, response.read().decode("utf-8")
        finally:
            connection.close()

    def post(self, action, **fields):
        return self.request("POST", "/action/" + action, dict(csrf=self.csrf, **fields))

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
        self.assertEqual(self.post("reject", lesson_id=lesson["lesson_id"])[0], 200)
        status, html = self.post("compare")
        self.assertEqual(status, 200)
        self.assertIn("B+ · FAIL", html)
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
                                      csrf=self.csrf, server_port=8765,
                                      server_address=("127.0.0.1", 8765))

    def request(self, method, path, fields=None, headers=None):
        body = urlencode(fields, doseq=True).encode("utf-8") if fields is not None else b""
        request_headers = {"Host": "127.0.0.1:8765", "Content-Type": "application/x-www-form-urlencoded",
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
            return response.status, response.read().decode("utf-8")
        finally:
            response.close()


if __name__ == "__main__":
    unittest.main()
