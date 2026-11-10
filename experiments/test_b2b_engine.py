"""Motor B2B: 20 notas ficticias, lesson.v2 por tipo y writer con la falla a propósito."""

from copy import deepcopy
from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import scribe_b2b as b2b
import scribe_editorial as ed

CLI = ROOT / "src" / "scribe_b2b.py"
FIX = ROOT / "experiments" / "fixtures" / "b2b"
BANNED = (
    "diimenet", "kavak", "sherlock", "lázaro", "lazaro", "system card",
    "gmail", "hotmail", "outlook", "yahoo", "protonmail", "icloud",
)
DALI = re.compile(r"(?<![a-záéíóúüñ])dali(?![a-záéíóúüñ])", re.IGNORECASE)
REAL_DOMAIN = re.compile(
    r"https?://|(?<![a-z0-9.-])(?:[a-z0-9-]+\.)+(?:com|mx|io|ai|org|net|co|app|dev)\b",
    re.IGNORECASE,
)


def repo_files():
    skip = {"__pycache__", ".git"}
    found = []
    for path in ROOT.rglob("*"):
        if any(part in skip for part in path.parts) or path.suffix == ".pyc":
            continue
        if path.is_file():
            found.append(path.relative_to(ROOT).as_posix())
    return sorted(found)


class B2BEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.loaded = b2b.iter_fixtures(FIX)
        cls.by_type = {}
        for path, note in cls.loaded:
            cls.by_type.setdefault(note["doc_type"], []).append((path, note))

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-b2b-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def origin(self, doc_type):
        return next(note for _path, note in self.by_type[doc_type] if b2b.case_number(note) == 1)

    def held(self, doc_type):
        return [note for _path, note in self.by_type[doc_type] if b2b.case_number(note) > 1]

    def approved(self, note):
        return b2b.simulate_approval(note, f"fixture:b2b-{note['doc_type']}")

    def test_twenty_fixtures_are_synthetic_and_shaped(self):
        self.assertEqual(set(self.by_type), set(b2b.DOC_TYPES))
        seen = set()
        for path, note in self.loaded:
            self.assertEqual(path.parent.name, note["doc_type"])
            self.assertEqual(path.name, f"case-{note['note_id'][-2:]}.json")
            self.assertTrue(note["synthetic"])
            self.assertIn("FICTICIA", path.read_text(encoding="utf-8"))
            self.assertEqual(note["company"]["email"].split("@")[1], "valvulas-ejemplo.example")
            self.assertTrue(note["customer"]["name"].startswith("Cliente Demo "))
            seen.add((note["doc_type"], b2b.case_number(note)))
        self.assertEqual(seen, {(kind, number) for kind in b2b.DOC_TYPES for number in range(1, 5)})

    def test_malformed_notes_are_rejected(self):
        note = deepcopy(self.origin("cotizacion"))
        note["synthetic"] = False
        with self.assertRaises(ed.Invalid):
            b2b.validate_note(note)
        note = deepcopy(self.origin("cotizacion"))
        note["customer"]["email"] = "compras@cliente-demo-01.com"
        with self.assertRaises(ed.Invalid):
            b2b.validate_note(note)
        note = deepcopy(self.origin("cotizacion"))
        note["facts"] = [fact for fact in note["facts"] if fact["fact_id"] != "vigencia"]
        with self.assertRaises(ed.Invalid):
            b2b.validate_note(note)
        note = deepcopy(self.origin("cotizacion"))
        note["extra"] = "no"
        with self.assertRaises(ed.Invalid):
            b2b.validate_note(note)

    def test_without_lesson_every_document_fails_its_critical_rule(self):
        for _path, note in self.loaded:
            document = b2b.draft(note, [])
            self.assertEqual(document["applied_lesson_ids"], [])
            self.assertNotIn("<", document["text"])
            self.assertIn("FICTICIA", document["text"])
            self.assertIn(note["customer"]["name"], document["text"])
            check = b2b.check_document(note, document["text"])
            self.assertFalse(check["compliant"], check)
            self.assertGreater(len(check["failures"]), 0)

    def test_case_one_lesson_fixes_later_cases_of_the_same_type_only(self):
        for doc_type in b2b.DOC_TYPES:
            pack = self.approved(self.origin(doc_type))
            lesson = pack["lesson"]
            self.assertEqual(lesson["evidence"]["note_id"], self.origin(doc_type)["note_id"])
            self.assertEqual(lesson["scope"]["doc_type"], doc_type)
            for note in self.held(doc_type):
                document = b2b.draft(note, pack["events"])
                check = b2b.check_document(note, document["text"])
                self.assertTrue(check["compliant"], (note["note_id"], check["failures"]))
                self.assertEqual(document["applied_lesson_ids"], [f"{lesson['lesson_id']}@v2"])
                self.assertNotEqual(lesson["evidence"]["note_id"], note["note_id"])
                bare = b2b.draft(note, [])
                self.assertTrue(b2b.regression(note, bare["text"], document["text"])["ok"])
            for other, rows in self.by_type.items():
                if other == doc_type:
                    continue
                for _path, note in rows:
                    bare = b2b.draft(note, [])
                    crossed = b2b.draft(note, pack["events"])
                    self.assertEqual(crossed["text"], bare["text"])
                    self.assertEqual(crossed["applied_lesson_ids"], [])
                    self.assertFalse(b2b.check_document(note, crossed["text"])["compliant"])

    def test_writer_uses_the_current_note_and_does_not_invent_numbers(self):
        expectations = {
            "propuesta_tecnica": ("FT-210", "FT-101"),
            "ficha_tecnica": ("16 bar (232 psi)", "10 bar (145 psi)"),
            "reporte_cliente": ("2026-11-23", "2026-11-16"),
            "respuesta_soporte": ("SOP-1904", "SOP-1842"),
        }
        for doc_type, (present, absent) in expectations.items():
            pack = self.approved(self.origin(doc_type))
            note = self.held(doc_type)[0]
            text = b2b.draft(note, pack["events"])["text"]
            self.assertIn(present, text)
            self.assertNotIn(absent, text)
            self.assertNotIn(b2b.WEAK_CLAIM, text)
        for _path, note in self.loaded:
            pack = self.approved(self.origin(note["doc_type"]))
            haystack = json.dumps(note, ensure_ascii=False)
            for lessons in ([], pack["events"]):
                text = b2b.draft(note, lessons)["text"]
                for number in re.findall(r"\d+", text):
                    self.assertIn(number, haystack, note["note_id"])

    def test_proposed_rejected_and_retired_do_not_change_the_text(self):
        note = self.held("cotizacion")[0]
        pack = self.approved(self.origin("cotizacion"))
        bare = b2b.draft(note, [])
        proposed = pack["events"][0]
        self.assertEqual(b2b.draft(note, [proposed])["text"], bare["text"])
        rejected = b2b.transition_event([proposed], proposed["lesson_id"], "rejected",
                                         created_at=b2b.FIXED_CLOCK)
        self.assertEqual(b2b.draft(note, [proposed, rejected])["text"], bare["text"])
        retired = b2b.transition_event(pack["events"], pack["lesson"]["lesson_id"], "rejected",
                                        created_at=b2b.FIXED_CLOCK)
        self.assertEqual(retired["state"], "rejected")
        self.assertEqual(b2b.draft(note, pack["events"] + [retired])["text"], bare["text"])

    def test_fixture_approval_without_prefix_is_rejected(self):
        proposed = self.approved(self.origin("cotizacion"))["events"][0]
        with self.assertRaises(ed.Invalid):
            b2b.transition_event([proposed], proposed["lesson_id"], "approved",
                                 "ticket-1", "fixture_simulated", b2b.FIXED_CLOCK)
        with self.assertRaises(ed.Invalid):
            b2b.transition_event([proposed], proposed["lesson_id"], "approved",
                                 "fixture:b2b", "Revisor Demo", b2b.FIXED_CLOCK)
        accepted = b2b.transition_event([proposed], proposed["lesson_id"], "approved",
                                         "acta-demo-01", "Revisor Demo", b2b.FIXED_CLOCK)
        self.assertEqual(accepted["approved_by"], "Revisor Demo")
        log = self.directory / "lessons.jsonl"
        b2b.append_lesson(log, proposed)
        before = log.read_bytes()
        with self.assertRaises(ed.Invalid):
            b2b.append_lesson(log, {**accepted, "approval_ref": "ticket-1", "approved_by": "fixture_simulated"})
        self.assertEqual(log.read_bytes(), before)

    def test_checker_normalizes_case_space_and_dashes(self):
        self.assertEqual(b2b.normalize("Línea — siguiente"), b2b.normalize("línea - siguiente"))
        self.assertEqual(b2b.normalize("  Pago:  50 %   anticipo "), b2b.normalize("pago: 50 % anticipo"))
        note = self.origin("cotizacion")
        text = b2b.draft(note, self.approved(note)["events"])["text"]
        mutated = text.replace(b2b.CLAUSE_VIGENCIA, "VIGENCIA:  15   DÍAS   NATURALES")
        vigencia = next(item for item in b2b.check_document(note, mutated)["requirements"]
                        if item["id"] == "vigencia")
        self.assertTrue(vigencia["ok"])
        support = self.origin("respuesta_soporte")
        weak = b2b.draft(support, [])["text"].replace(b2b.WEAK_CLAIM, "SOLUCIÓN—DEFINITIVA. Garantizamos.")
        forbidden = [item for item in b2b.check_document(support, weak)["requirements"] if not item["ok"]]
        self.assertTrue(any("prohibida" in item["detail"] for item in forbidden))

    def test_blocklist_and_real_domains_stay_out_of_fixtures(self):
        for path, _note in self.loaded:
            raw = path.read_text(encoding="utf-8").casefold()
            for banned in BANNED:
                self.assertNotIn(banned, raw, path.name)
            self.assertIsNone(DALI.search(raw), path.name)
            self.assertIsNone(REAL_DOMAIN.search(raw), path.name)
            self.assertNotIn("@gmail", raw)

    def test_drafts_are_deterministic_and_do_not_write_the_repo(self):
        before = repo_files()
        note = self.held("ficha_tecnica")[0]
        events = self.approved(self.origin("ficha_tecnica"))["events"]
        self.assertEqual(b2b.draft(note, events), b2b.draft(note, events))
        rendered = b2b.render_document(note, "Cuerpo de prueba ficticio, sin cifras nuevas.")
        self.assertIn("FICTICIA", rendered)
        self.assertNotIn("<", rendered)
        log = self.directory / "lessons.jsonl"
        for event in events:
            b2b.append_lesson(log, event)
        broken = self.directory / "broken.jsonl"
        broken.write_bytes(ed.encoded(events[0]).encode("utf-8"))
        before_broken = broken.read_bytes()
        with self.assertRaises(ed.Invalid):
            b2b.append_lesson(broken, events[1])
        self.assertEqual(broken.read_bytes(), before_broken)
        self.assertEqual(repo_files(), before)

    def test_cli_exit_codes_stay_in_temp(self):
        note = self.held("reporte_cliente")[0]
        events = self.approved(self.origin("reporte_cliente"))["events"]
        note_path = self.directory / "note.json"
        note_path.write_text(json.dumps(note, ensure_ascii=False) + "\n", encoding="utf-8")
        log = self.directory / "lessons.jsonl"
        empty = self.directory / "empty.jsonl"
        empty.write_text("", encoding="utf-8")
        for event in events:
            b2b.append_lesson(log, event)
        out = self.directory / "draft.json"
        env = os.environ | {"PYTHONDONTWRITEBYTECODE": "1"}
        first = self.cli("draft", "--note", note_path, "--lessons", empty, "--out", out, code=0, env=env)
        self.assertEqual(first["applied_lesson_ids"], [])
        self.cli("draft", "--note", note_path, "--lessons", empty, "--out", out, code=2, env=env)
        text = self.directory / "body.txt"
        text.write_text(first["text"], encoding="utf-8")
        failed = self.cli("check", "--note", note_path, "--text", text, code=1, env=env)
        self.assertFalse(failed["compliant"])
        passed = self.cli("draft", "--note", note_path, "--lessons", log, code=0, env=env)
        text.write_text(passed["text"], encoding="utf-8")
        ok = self.cli("check", "--note", note_path, "--text", text, code=0, env=env)
        self.assertTrue(ok["compliant"])
        again = self.cli("draft", "--note", note_path, "--lessons", log, code=0, env=env)
        self.assertEqual(again, passed)
        invalid = self.cli("check", "--note", self.directory / "missing.json", "--text", text, code=2, env=env)
        self.assertEqual(invalid["outcome"], "invalid")

    def cli(self, *arguments, code, env):
        result = subprocess.run([sys.executable, str(CLI), *map(str, arguments)],
                                capture_output=True, encoding="utf-8", timeout=20, env=env)
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, code, combined)
        self.assertNotIn("Traceback", combined)
        return json.loads(result.stdout)


if __name__ == "__main__":
    unittest.main()
