"""M2d offline: gate, aislamiento, checker y frontera de ejecución Codex."""

from contextlib import redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import demo_codex_writer as demo

ed = demo.editorial


class CodexWriterTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-m2d-test-", dir="/tmp")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.note = ed.load(demo.FIXTURE, "research_note.v1")
        self.log = demo.prepare_lessons(self.note, self.directory)

    def workspace(self):
        return Path(tempfile.mkdtemp(prefix="workspace-", dir=self.directory))

    def test_only_plus_has_skill_and_agents_from_approved_disk_lesson(self):
        minus, plus, lesson = demo.prepare_workspaces(self.note, self.log, self.directory)
        self.assertNotEqual(minus, plus)
        self.assertFalse((minus / ".agents").exists())
        self.assertFalse((minus / "AGENTS.md").exists())
        for workspace in (minus, plus):
            self.assertEqual(ed.load(workspace / "note.json", "research_note.v1"), self.note)
        skills = list((plus / ".agents/skills").iterdir())
        self.assertEqual([p.name for p in skills], ["scribe-lesson-" + lesson["lesson_id"]])
        body = (skills[0] / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(body.startswith("---\nname: " + skills[0].name + "\ndescription: "))
        self.assertIn("\n---\n", body)
        for field in ("rule", "trigger"):
            self.assertIn(field + ": " + lesson[field], body)
        for value in ("evidence:", "fact_ids", "f1", self.note["note_id"],
                      "fixture_simulated", "fixture:m2d-control", f"@v{lesson['version']}"):
            self.assertIn(value, body)
        self.assertIn(".agents/skills/", (plus / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertEqual([x["state"] for x in ed.read_log(self.log, "lesson.v1")],
                         ["proposed", "approved"])

    def test_gate_refuses_proposed_rejected_revoked_and_empty_without_writes(self):
        events = ed.read_log(self.log, "lesson.v1")
        rejected = deepcopy(events[0])
        rejected.update(version=2, state="rejected")
        revoked = deepcopy(events[-1])
        revoked.update(version=3, state="rejected", approved_by=None, approval_ref=None)
        histories = {"empty": [], "proposed": events[:1],
                     "rejected": [events[0], rejected], "revoked": events + [revoked]}
        for name, history in histories.items():
            with self.subTest(name=name):
                log = self.directory / (name + ".jsonl")
                for event in history:
                    ed.append_log(log, event)
                workspace = self.workspace()
                self.assertEqual(ed.approved_for(self.note, ed.read_log(log, "lesson.v1")), [])
                with self.assertRaisesRegex(ed.Invalid, "no hay lección APPROVED"):
                    demo.materialize_skill(workspace, self.note, log)
                self.assertEqual(list(workspace.iterdir()), [])

    def test_scope_and_note_gate_and_unknown_evidence_fail_closed(self):
        approved = ed.read_log(self.log, "lesson.v1")[-1]
        for field in ("task", "note_id", "fact_ids"):
            with self.subTest(field=field):
                lesson = deepcopy(approved)
                if field == "task":
                    lesson["scope"]["task"] = "other_task"
                elif field == "note_id":
                    lesson["evidence"]["note_id"] = "other-note"
                else:
                    lesson["evidence"]["fact_ids"] = ["unknown"]
                log = self.directory / (field + ".jsonl")
                ed.append_log(log, lesson)
                workspace = self.workspace()
                with self.assertRaises(ed.Invalid):
                    demo.materialize_skill(workspace, self.note, log)
                self.assertFalse((workspace / ".agents").exists())

    def test_repo_and_symlink_destinations_are_refused(self):
        with self.assertRaisesRegex(ed.Invalid, "/tmp"):
            demo.materialize_skill(demo.ROOT, self.note, self.log)
        link = self.directory / "linked"
        link.symlink_to(self.workspace(), target_is_directory=True)
        with self.assertRaisesRegex(ed.Invalid, "sin enlaces"):
            demo.materialize_skill(link, self.note, self.log)

    def test_checker_requires_literal_fact_and_correct_citation_for_every_branch(self):
        fact = self.note["facts"][0]["text"]
        cases = [(demo.DRY_MINUS, False), (fact, False),
                 ("[synthetic-note-001:f1]", False),
                 (fact + " [other-note:f1]", False),
                 (fact + " [synthetic-note-001:f2]", False),
                 ("Duró cuatro semanas [synthetic-note-001:f1]", False),
                 (demo.DRY_PLUS, True)]
        for text, passed in cases:
            for session in ("minus", "plus"):
                with self.subTest(text=text, session=session):
                    result = demo.evaluate_text(self.note, text, session)
                    self.assertEqual(result["passed"], passed)
                    self.assertEqual(result["draft"]["fact_refs"], ["f1"] if passed else [])
                    self.assertEqual(result["draft"]["applied_lesson_ids"], [])
                    self.assertEqual(result["check"], ed.check_draft(self.note, result["draft"]))

    def test_dry_run_panel_evidence_and_no_codex_writer_calls(self):
        output = io.StringIO()
        # Un CLI ausente no impide esta demo offline; tampoco se invoca exec --help.
        with patch.object(demo.subprocess, "run", side_effect=FileNotFoundError) as run, \
                redirect_stdout(output):
            result = demo.demonstrate(self.workspace(), dry_run=True)
        self.assertEqual([call.args[0] for call in run.call_args_list], [["codex", "--version"]])
        self.assertFalse(result["B−"]["passed"])
        self.assertTrue(result["B+"]["passed"])
        for excerpt in ("DRY-RUN", "B−: f1 SIN MATCH LITERAL · check FAIL",
                        "B+: f1 PRESENTE + cita · check PASS", "N=1", "fixture_simulated"):
            self.assertIn(excerpt, output.getvalue())
        manifest_path = next(self.directory.glob("workspace-*/run.json"))
        manifest = json.loads(manifest_path.read_text())
        self.assertEqual(manifest["lesson_read_by_model"], "unverified")
        self.assertEqual(manifest["materialized_lesson"]["state"], "approved")
        for branch in ("B−", "B+"):
            workspace = Path(manifest[branch])
            execution = json.loads((workspace / "execution.json").read_text())
            self.assertFalse(execution["codex_executed"])
            self.assertIsNone(execution["exit_code"])
            self.assertTrue((workspace / "out.txt").exists())
            self.assertTrue((workspace / "check.json").exists())
            self.assertFalse((workspace / "codex-events.jsonl").exists())

    def test_cli_dry_run_keeps_real_repo_agents_untouched(self):
        def snapshot():
            base = demo.ROOT / ".agents"
            return {"exists": base.exists(), "files": {
                str(p.relative_to(base)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in base.rglob("*") if p.is_file()
            }, "AGENTS.md": (demo.ROOT / "AGENTS.md").read_bytes()}
        before = snapshot()
        result = subprocess.run([sys.executable, str(Path(demo.__file__)), "--dry-run"],
                                capture_output=True, encoding="utf-8", timeout=20,
                                env=dict(os.environ, PATH="/nonexistent"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("B−: f1 SIN MATCH LITERAL · check FAIL", result.stdout)
        self.assertIn("B+: f1 PRESENTE + cita · check PASS", result.stdout)
        self.assertEqual(snapshot(), before)
        # Limpiar solo la corrida aislada que este test creó.
        path = result.stdout.splitlines()[0].removeprefix("Evidencia conservada: ")
        self.addCleanup(shutil.rmtree, demo.temporary_path(path))

    def test_real_boundary_reads_outfile_and_captures_native_events_without_llm(self):
        workspace = self.workspace()

        def fake_codex(command, **kwargs):
            self.assertEqual(command[:7], ["codex", "exec", "--ephemeral", "--skip-git-repo-check",
                                          "--sandbox", "read-only", "-C"])
            self.assertEqual(command[7], str(workspace))
            self.assertEqual(command[command.index("-o") + 1], str(workspace / "out.txt"))
            self.assertIn("--json", command)
            self.assertEqual(command[-1], demo.PROMPT)
            self.assertEqual(kwargs["cwd"], workspace)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            kwargs["stdout"].write('{"type":"turn.completed"}\n')
            (workspace / "out.txt").write_text(demo.DRY_PLUS, encoding="utf-8")
            return subprocess.CompletedProcess(command, 0)

        with patch.object(demo.subprocess, "run", side_effect=fake_codex):
            self.assertEqual(demo.run_writer(workspace), demo.DRY_PLUS)
        execution = json.loads((workspace / "execution.json").read_text())
        self.assertEqual(execution["exit_code"], 0)
        self.assertTrue(execution["codex_executed"])
        self.assertEqual(json.loads((workspace / "codex-events.jsonl").read_text())["type"],
                         "turn.completed")

    def test_failed_missing_empty_and_timeout_outputs_do_not_pass_as_drafts(self):
        for mode in ("nonzero", "missing", "empty", "timeout"):
            workspace = self.workspace()

            def fail(command, **kwargs):
                if mode == "timeout":
                    raise subprocess.TimeoutExpired(command, 300)
                if mode in ("empty", "nonzero"):
                    (workspace / "out.txt").write_text(demo.DRY_PLUS if mode == "nonzero" else "")
                return subprocess.CompletedProcess(command, 7 if mode == "nonzero" else 0)

            with self.subTest(mode=mode), patch.object(demo.subprocess, "run", side_effect=fail):
                with self.assertRaisesRegex(ed.Invalid, "STOP"):
                    demo.run_writer(workspace)
            self.assertTrue((workspace / "execution.json").exists())
            if mode == "nonzero":
                self.assertEqual(json.loads((workspace / "execution.json").read_text())["exit_code"], 7)


if __name__ == "__main__":
    unittest.main()
