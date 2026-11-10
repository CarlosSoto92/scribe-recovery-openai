"""Contratos y controles causales del loop editorial, con archivos sintéticos."""

from copy import deepcopy
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import scribe_editorial as ed

CLI = ROOT / "src" / "scribe_editorial.py"
FIXTURE = ROOT / "experiments" / "fixtures" / "synthetic_note_001.json"


class EditorialTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-editorial-test-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.log = self.directory / "lessons.jsonl"
        self.feedback_log = self.directory / "feedback.jsonl"
        self.draft_path = self.directory / "draft.json"
        self.note = ed.load(FIXTURE, "research_note.v1")
        self.first = ed.draft(self.note, [], "test-v1")
        self.feedback = ed.make_feedback(self.note, self.first, "fixture_simulated", 2,
                                         "Omitiste 4 semanas.", ["f1"], "Conservar y citar f1.")
        self.lesson = ed.propose_candidate(self.note, self.first, self.feedback)

    def cli(self, *arguments, code=0):
        result = subprocess.run([sys.executable, str(CLI), *map(str, arguments)],
                                capture_output=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, code, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stderr + result.stdout)
        document = json.loads(result.stdout)
        if code == 2:
            self.assertEqual(document["outcome"], "invalid")
        return document

    def approved(self):
        ed.append_log(self.log, self.lesson)
        return ed.transition(self.log, self.lesson["lesson_id"], "approved",
                             "fixture:test", "fixture_simulated")

    def cli_feedback(self):
        self.cli("draft", "--note", FIXTURE, "--lessons", self.log,
                 "--session-id", "cli-v1", "--out", self.draft_path)
        return self.cli("feedback", "--draft", self.draft_path, "--reviewer", "carlos",
                        "--rating", "2", "--comment", "Falta el hecho sintético.",
                        "--target-facts", "f1", "--feedback-log", self.feedback_log)

    def test_exact_schema_roundtrips(self):
        for document in (self.note, self.first, self.feedback, self.lesson):
            self.assertEqual(ed.validate(json.loads(ed.encoded(document))), document)
            for key in document:
                broken = deepcopy(document)
                del broken[key]
                with self.subTest(schema=document["schema_version"], key=key):
                    with self.assertRaises(ed.Invalid):
                        ed.validate(broken)
            broken = dict(document, unexpected=True)
            with self.assertRaises(ed.Invalid):
                ed.validate(broken)

    def test_rejects_malformed_documents(self):
        for value in (None, [], 1, "string", {}, {"schema_version": "unknown"}):
            with self.subTest(value=value), self.assertRaises(ed.Invalid):
                ed.validate(value)
        for document, key, values in (
            (self.note, "facts", [[], {}, [None]]),
            (self.note, "limits", ["text", [], [3]]),
            (self.note, "note_id", ["", "../escape", "id\nnext"]),
            (self.first, "status", ["published", None]),
            (self.first, "fact_refs", [["f1", "f1"], "f1", [3]]),
            (self.first, "applied_lesson_ids", [["unversioned"]]),
            (self.feedback, "rating", [0, 6, True, 2.5, "2"]),
            (self.feedback, "rating_scale", ["0-10"]),
            (self.feedback, "target_fact_ids", [[], ["f1", "f1"]]),
            (self.feedback, "reviewer", ["", None]),
            (self.lesson, "version", [0, True, "1"]),
            (self.lesson, "state", ["active", None]),
        ):
            for value in values:
                with self.subTest(key=key, value=value), self.assertRaises(ed.Invalid):
                    ed.validate(dict(document, **{key: value}))

    def test_nested_schema_and_synthetic_source_enforced(self):
        for source in ({"type": "public", "url": "https://example.org", "retrieved_at": ed.now()},
                       {"type": "synthetic", "url": "https://example.org", "retrieved_at": ed.now()},
                       {"type": "synthetic", "url": None}):
            with self.assertRaises(ed.Invalid):
                ed.validate(dict(self.note, source=source))
        for value in (1, "true", None):
            note = deepcopy(self.note)
            note["facts"][0]["must_keep"] = value
            with self.assertRaises(ed.Invalid):
                ed.validate(note)
        note = deepcopy(self.note)
        note["facts"].append(note["facts"][0])
        with self.assertRaises(ed.Invalid):
            ed.validate(note)
        lesson = deepcopy(self.lesson)
        lesson["evidence"]["fact_ids"] = []
        with self.assertRaises(ed.Invalid):
            ed.validate(lesson)

    def test_utc_timestamps_reject_naive_offsets_and_invalid_dates(self):
        for value in ("2026-11-09T21:00:00", "2026-11-09T21:00:00-06:00", "bad",
                      "2026-02-30T21:00:00Z", None):
            with self.subTest(value=value), self.assertRaises(ed.Invalid):
                ed.validate(dict(self.feedback, created_at=value))
        for value in ("2026-11-09T21:00:00Z", "2026-11-09T21:00:00+00:00"):
            ed.validate(dict(self.feedback, created_at=value))

    def test_json_duplicate_keys_and_nonfinite_numbers_rejected(self):
        for raw in ('{"rating":1,"rating":2}', '{"x":NaN}', '{"x":Infinity}', '{'):
            with self.subTest(raw=raw), self.assertRaises(ed.Invalid):
                ed.parse_json(raw)

    def test_jsonl_unicode_separators_are_data_not_lines(self):
        feedback = dict(self.feedback, comment="ñ 雪 😀 uno\u2028dos\u2029tres\u0085fin\ntexto")
        ed.append_log(self.feedback_log, feedback)
        prefix = self.feedback_log.read_bytes()
        self.assertIn("\u2028".encode("utf-8"), prefix)
        self.assertEqual(ed.read_log(self.feedback_log, "feedback.v1"), [feedback])
        second = dict(feedback, feedback_id="fb-next")
        ed.append_log(self.feedback_log, second)
        self.assertTrue(self.feedback_log.read_bytes().startswith(prefix))
        self.assertEqual(ed.read_log(self.feedback_log, "feedback.v1"), [feedback, second])

    def test_malformed_log_never_repaired_or_appended(self):
        for raw in (b"{truncated", b"{}\n", b"\n", b"[]\n", b"\xff\n",
                    ed.encoded(self.lesson).encode("utf-8"),
                    (ed.encoded(self.lesson) + "\n\n").encode("utf-8")):
            self.log.write_bytes(raw)  # Corrupción intencional de fixture.
            with self.subTest(raw=raw):
                with self.assertRaises((ed.Invalid, UnicodeError)):
                    ed.append_log(self.log, self.lesson)
                self.assertEqual(self.log.read_bytes(), raw)

    def test_writer_is_deterministic_and_baseline_omits_all_critical_facts(self):
        self.assertEqual(self.first, ed.draft(self.note, [], "test-v1"))
        self.assertEqual(self.first["fact_refs"], [])
        for fact in self.note["facts"]:
            if fact["must_keep"]:
                self.assertNotIn(fact["text"], self.first["text"])
        self.assertEqual(ed.check_draft(self.note, self.first)["retención de hechos críticos"], 0)

    def test_proposed_control_does_not_change_complete_draft(self):
        ed.append_log(self.log, self.lesson)
        selected = ed.approved_for(self.note, ed.read_log(self.log, "lesson.v1"))
        self.assertEqual(selected, [])
        self.assertEqual(ed.draft(self.note, selected, "test-v1"), self.first)
        with self.assertRaises(ed.Invalid):
            ed.draft(self.note, [self.lesson])

    def test_rejected_never_applies(self):
        ed.append_log(self.log, self.lesson)
        rejected = ed.transition(self.log, self.lesson["lesson_id"], "rejected")
        self.assertEqual(rejected["state"], "rejected")
        self.assertEqual(ed.approved_for(self.note, ed.read_log(self.log, "lesson.v1")), [])
        with self.assertRaises(ed.Invalid):
            ed.draft(self.note, [rejected])

    def test_approved_requires_reference_and_actor_before_append(self):
        ed.append_log(self.log, self.lesson)
        prefix = self.log.read_bytes()
        for ref, actor in ((None, "fixture_simulated"), ("", "fixture_simulated"),
                           ("  ", "fixture_simulated"), ("fixture:test", None),
                           ("fixture:test", "carlos"), ("PR:7", "fixture_simulated")):
            with self.subTest(ref=ref, actor=actor), self.assertRaises(ed.Invalid):
                ed.transition(self.log, self.lesson["lesson_id"], "approved", ref, actor)
            self.assertEqual(self.log.read_bytes(), prefix)

    def test_fixture_approved_applies_with_id_version_and_provenance(self):
        approved = self.approved()
        selected = ed.approved_for(self.note, ed.read_log(self.log, "lesson.v1"))
        result = ed.draft(self.note, selected, "test-v2")
        self.assertEqual(result["applied_lesson_ids"], [approved["lesson_id"] + "@v2"])
        self.assertEqual(result["fact_refs"], ["f1"])
        self.assertIn("[synthetic-note-001:f1]", result["text"])
        self.assertEqual(ed.check_draft(self.note, result)["retención de hechos críticos"], 1.0)
        self.assertEqual(result, ed.draft(self.note, selected, "test-v2"))

    def test_other_scope_or_note_not_selected(self):
        for field, value in (("task", "other_task"), ("rule_type", "other_rule"),
                             ("note_id", "other-note")):
            lesson = deepcopy(self.lesson)
            lesson["lesson_id"] += "-" + field
            lesson["evidence" if field == "note_id" else "scope"][field] = value
            ed.append_log(self.log, lesson)
            ed.transition(self.log, lesson["lesson_id"], "approved", "fixture:test", "fixture_simulated")
        self.assertEqual(ed.approved_for(self.note, ed.read_log(self.log, "lesson.v1")), [])

    def test_revocation_suppresses_historical_approval(self):
        self.approved()
        prefix = self.log.read_bytes()
        ed.transition(self.log, self.lesson["lesson_id"], "rejected")
        self.assertTrue(self.log.read_bytes().startswith(prefix))
        self.assertEqual(ed.approved_for(self.note, ed.read_log(self.log, "lesson.v1")), [])

    def test_invalid_history_versions_transitions_and_provenance(self):
        ed.append_log(self.log, self.lesson)
        prefix = self.log.read_bytes()
        for event in (self.lesson, dict(self.lesson, version=3, state="rejected"),
                      dict(self.lesson, version=2),
                      dict(self.lesson, version=2, state="rejected", source_feedback_id="fb-other"),
                      dict(self.lesson, version=2, state="rejected", created_at="2000-01-01T00:00:00Z")):
            with self.assertRaises(ed.Invalid):
                ed.append_log(self.log, event)
            self.assertEqual(self.log.read_bytes(), prefix)

    def test_approved_snapshot_with_provenance_is_readable_from_disk(self):
        ed.append_log(self.log, self.approved_event())
        child = self.cli("draft", "--note", FIXTURE, "--lessons", self.log, "--session-id", "snapshot")
        self.assertEqual(child["fact_refs"], ["f1"])

    def approved_event(self):
        return dict(self.lesson, version=2, state="approved", approved_by="fixture_simulated",
                    approval_ref="fixture:test", created_at=ed.now())

    def test_feedback_provenance_targets_and_real_reviewer(self):
        feedback = ed.make_feedback(self.note, self.first, "carlos", 1, "Falta f1", ["f1"])
        proposed = ed.propose_candidate(self.note, self.first, feedback)
        self.assertEqual(proposed["source_feedback_id"], feedback["feedback_id"])
        self.assertEqual(proposed["state"], "proposed")
        self.assertIsNone(proposed["approved_by"])
        for altered in (dict(feedback, draft_id="unknown"), dict(feedback, target_fact_ids=["missing"]),
                        dict(feedback, target_fact_ids=["f2"])):
            with self.assertRaises(ed.Invalid):
                ed.propose_candidate(self.note, self.first, altered)

    def test_writer_rejects_wrong_fact_evidence(self):
        for target in ("unknown", "f2"):
            lesson = self.approved_event()
            lesson["evidence"] = {"note_id": self.note["note_id"], "fact_ids": [target]}
            with self.assertRaises(ed.Invalid):
                ed.draft(self.note, [lesson])

    def test_metric_requires_both_text_and_verifiable_citation(self):
        approved = self.approved()
        good = ed.draft(self.note, [approved])
        for bad in (dict(good, fact_refs=[]), dict(good, text="Solo [synthetic-note-001:f1]"),
                    dict(good, text=self.note["facts"][0]["text"])):
            self.assertEqual(ed.check_draft(self.note, bad)["retención de hechos críticos"], 0)
        with self.assertRaises(ed.Invalid):
            ed.check_draft(self.note, dict(good, note_id="wrong"))
        with self.assertRaises(ed.Invalid):
            ed.check_draft(self.note, dict(good, fact_refs=["missing"]))

    def test_two_fresh_processes_read_parent_approved_lesson_from_disk(self):
        self.approved()
        drafts = [self.cli("draft", "--note", FIXTURE, "--lessons", self.log,
                           "--session-id", "child-" + str(index)) for index in (1, 2)]
        self.assertNotEqual(drafts[0]["session_id"], drafts[1]["session_id"])
        for document in drafts:
            self.assertEqual(document["fact_refs"], ["f1"])
            self.assertEqual(document["applied_lesson_ids"], [self.lesson["lesson_id"] + "@v2"])

    def test_compare_metric_same_checker_fresh_processes(self):
        self.approved()
        with patch.object(ed, "fresh_draft", wraps=ed.fresh_draft) as fresh:
            result = ed.compare(FIXTURE, self.log, "comparison")
        self.assertEqual(fresh.call_count, 2)
        self.assertEqual(result["outcome"], "success")
        self.assertEqual(result["B−"]["check"]["retención de hechos críticos"], 0)
        self.assertEqual(result["B+"]["check"]["retención de hechos críticos"], 1.0)
        self.assertEqual(self.cli("compare", "--note", FIXTURE, "--lessons", self.log,
                                  "--session-prefix", "cli-comparison")["outcome"], "success")

    def test_compare_with_only_proposed_is_failed_check_exit_one(self):
        ed.append_log(self.log, self.lesson)
        result = self.cli("compare", "--note", FIXTURE, "--lessons", self.log,
                          "--session-prefix", "negative", code=1)
        self.assertEqual(result["B−"]["draft"]["text"], result["B+"]["draft"]["text"])
        self.assertEqual(result["lessons_used"], [])

    def test_cli_full_loop_propose_by_id_and_reject(self):
        feedback = self.cli_feedback()
        candidate = self.cli("propose", "--feedback", feedback["feedback_id"],
                              "--feedback-log", self.feedback_log, "--lessons", self.log)
        self.assertEqual(candidate["state"], "proposed")
        self.cli("approve", "--lesson-id", candidate["lesson_id"], "--approval-ref", "fixture:test",
                 "--approved-by", "fixture_simulated", "--lessons", self.log)
        self.cli("reject", "--lesson-id", candidate["lesson_id"], "--lessons", self.log)
        result = self.cli("draft", "--note", FIXTURE, "--lessons", self.log, "--session-id", "rejected")
        self.assertEqual(result["applied_lesson_ids"], [])

    def test_cli_propose_by_feedback_path_requires_registered_context(self):
        feedback = self.cli_feedback()
        feedback_path = self.directory / "feedback.json"
        ed.save_new(feedback_path, feedback)
        proposed = self.cli("propose", "--feedback", feedback_path,
                            "--feedback-log", self.feedback_log, "--lessons", self.log)
        self.assertEqual(proposed["source_feedback_id"], feedback["feedback_id"])
        self.cli("propose", "--feedback", feedback_path,
                 "--feedback-log", self.feedback_log, "--lessons", self.log, code=2)

    def test_cli_invalid_inputs_are_json_without_traceback(self):
        for arguments in ([], ["unknown"], ["draft"], ["approve", "--lesson-id", "absent",
                           "--lessons", self.log, "--approval-ref", ""],
                          ["feedback", "--draft", self.draft_path, "--reviewer", "carlos",
                           "--rating", "bad", "--comment", "test", "--target-facts", "f1"],
                          ["draft", "--note", FIXTURE, "--lessons", self.log, "--session-id", "bad/id"]):
            with self.subTest(arguments=arguments):
                self.cli(*arguments, code=2)

    def test_cli_refuses_overwrite_or_input_log_alias(self):
        original = FIXTURE.read_bytes()
        self.cli("draft", "--note", FIXTURE, "--lessons", FIXTURE, "--session-id", "alias", code=2)
        self.assertEqual(FIXTURE.read_bytes(), original)
        note_copy = self.directory / "note.json"
        note_copy.write_bytes(original)
        alias = self.directory / "alias.json"
        alias.hardlink_to(note_copy)
        self.cli("draft", "--note", note_copy, "--lessons", alias, "--session-id", "alias", code=2)
        arguments = ("draft", "--note", FIXTURE, "--lessons", self.log,
                     "--session-id", "out", "--out", self.draft_path)
        self.cli(*arguments)
        prefix = self.draft_path.read_bytes()
        self.cli(*arguments, code=2)
        self.assertEqual(self.draft_path.read_bytes(), prefix)

    def test_cli_symlink_loop_returns_invalid_without_traceback(self):
        loop = self.directory / "loop"
        loop.symlink_to(loop)
        self.cli("draft", "--note", FIXTURE, "--lessons", loop, "--session-id", "loop", code=2)

    def test_duplicate_feedback_never_appended(self):
        ed.append_log(self.feedback_log, self.feedback)
        prefix = self.feedback_log.read_bytes()
        with self.assertRaises(ed.Invalid):
            ed.append_log(self.feedback_log, self.feedback)
        self.assertEqual(self.feedback_log.read_bytes(), prefix)

    def test_multiple_critical_facts_partial_and_full_retention(self):
        self.note["facts"][1]["must_keep"] = True
        approved = self.approved()
        partial = ed.draft(self.note, [approved])
        self.assertEqual(ed.check_draft(self.note, partial)["retención de hechos críticos"], 0.5)
        approved["evidence"]["fact_ids"] = ["f1", "f2"]
        full = ed.draft(self.note, [approved])
        self.assertEqual(ed.check_draft(self.note, full)["retención de hechos críticos"], 1.0)

    def test_no_critical_facts_metric_is_undefined_compare_invalid(self):
        for fact in self.note["facts"]:
            fact["must_keep"] = False
        result = ed.draft(self.note, [])
        self.assertIsNone(ed.check_draft(self.note, result)["retención de hechos críticos"])
        note_path = self.directory / "noncritical.json"
        ed.save_new(note_path, self.note)
        self.cli("compare", "--note", note_path, "--lessons", self.log,
                 "--session-prefix", "empty", code=2)

    def test_demo_pass_cleanup_and_preserved_output(self):
        script = ROOT / "experiments" / "demo_editorial.py"
        result = subprocess.run([sys.executable, str(script)], capture_output=True,
                                encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("DEMO EDITORIAL PASS", result.stdout)
        line = result.stdout.split("\n")[0]
        temporary = line.split(": ", 1)[1].split(" (", 1)[0]
        self.assertFalse(Path(temporary).exists())
        result = subprocess.run([sys.executable, str(script), "--output-dir", str(self.directory)],
                                capture_output=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        kept = list(self.directory.glob("scribe-editorial-*"))
        self.assertEqual(len(kept), 1)
        self.assertTrue((kept[0] / "lessons.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
