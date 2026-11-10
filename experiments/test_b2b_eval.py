"""Evaluación B2B: stub, controles, Wilson, signos y replay sin Codex."""

from io import StringIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from contextlib import redirect_stdout
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "experiments"))
import eval_b2b as ev
import record_codex_runs as rec
import scribe_b2b as b2b
import scribe_editorial as ed

RESULTS = ROOT / "experiments" / "results" / "eval_b2b.json"
EVAL = ROOT / "docs" / "EVAL.md"


class EvalTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="scribe-b2b-eval-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)

    def test_wilson_and_sign_test_match_known_values(self):
        # Cifras calculadas aparte con decimal, z = 1.959963984540054.
        self.assertEqual(ev.bound(ev.wilson(0, 10)[0]), "0.0000000000")
        self.assertEqual(ev.bound(ev.wilson(0, 10)[1]), "0.2775327999")
        self.assertEqual(ev.bound(ev.wilson(81, 100)[0]), "0.7222115462")
        self.assertEqual(ev.bound(ev.wilson(81, 100)[1]), "0.8748524849")
        self.assertEqual(ev.interval(0, 15)["display"], "0.0 % – 20.4 %")
        self.assertEqual(ev.interval(15, 15)["display"], "79.6 % – 100.0 %")
        self.assertEqual(ev.sign_test(15, 0)["p_two_sided"], "0.00006103515625")
        self.assertEqual(ev.sign_test(3, 1)["p_two_sided"], "0.625")
        self.assertEqual(ev.sign_test(2, 2)["p_two_sided"], "1")

    def test_stub_is_a_mechanism_check_not_a_model_score(self):
        report = json.loads(RESULTS.read_text(encoding="utf-8"))
        self.assertEqual(report["writer"], "stub")
        self.assertEqual(report["held_out"]["n"], 15)
        self.assertEqual(report["held_out"]["B-"]["fraction"], "0/15")
        self.assertEqual(report["held_out"]["B+"]["fraction"], "15/15")
        self.assertEqual(report["held_out"]["sign_test"]["improved"], 15)
        self.assertEqual(report["held_out"]["sign_test"]["worsened"], 0)
        self.assertTrue(report["held_out"]["regression"]["ok"])
        for name in ("C1", "C2", "C3", "C4"):
            self.assertTrue(report["controls"][name]["pass"], name)
        self.assertEqual(report["train_case_1"]["B-"]["n"], 5)
        self.assertEqual(report["codex_recorded"]["status"], "grabado")
        self.assertEqual(len(report["codex_recorded"]["runs"]), 65)
        quote = next(row for row in report["cases"] if row["note_id"] == "b2b-cotizacion-02")
        self.assertNotIn(b2b.CLAUSE_VIGENCIA, quote["conditions"]["B-"]["text"])
        self.assertIn(b2b.CLAUSE_PAGO, quote["conditions"]["B+"]["text"])
        self.assertNotIn("Cliente Demo 01", quote["conditions"]["B+"]["text"])
        self.assertEqual(len(report["lessons"]), 5)
        self.assertTrue(all(lesson["applied_held_out"] == 3 for lesson in report["lessons"]))

    def test_second_run_matches_the_report_byte_for_byte(self):
        before = (RESULTS.read_bytes(), EVAL.read_bytes())
        with redirect_stdout(StringIO()):
            self.assertEqual(ev.main(["--writer", "stub"]), 0)
        self.assertEqual(before, (RESULTS.read_bytes(), EVAL.read_bytes()))
        report = json.loads(before[0].decode("utf-8"))
        markdown = before[1].decode("utf-8")
        self.assertIn(report["held_out"]["B-"]["fraction"], markdown)
        self.assertIn(report["held_out"]["B+"]["wilson95"]["display"], markdown)
        self.assertIn(report["held_out"]["sign_test"]["p_two_sided"], markdown)
        recorded = report["codex_recorded"]
        self.assertNotIn(ev.PENDING, markdown)
        self.assertIn(recorded["label"], markdown)
        for key in ("B-", "B+", "C3"):
            for value in (recorded[key]["fraction"], recorded[key]["rate_display"], recorded[key]["wilson95"]["display"]):
                self.assertIn(value, markdown)
        self.assertIn(recorded["sign_test"]["p_two_sided"], markdown)
        self.assertIn("prueba de mecanismo", markdown)
        held = next(row for row in report["cases"] if row["held_out"])
        self.assertIn(held["conditions"]["B-"]["failures"][0], markdown)
        self.assertIn(held["conditions"]["B-"]["text"].splitlines()[0], markdown)

    def test_recorded_counts_each_rep_and_matches_exact_statistics(self):
        directory = ROOT / "experiments" / "recorded" / "codex-20261110"
        manifest = json.loads((directory / "MANIFEST.json").read_text(encoding="utf-8"))
        recorded = ev.replay(directory)["codex_recorded"]
        saved = json.loads(RESULTS.read_text(encoding="utf-8"))["codex_recorded"]
        self.assertEqual(recorded, saved)
        self.assertEqual(recorded["label"], "Codex (codex-cli 0.167, suscripción ChatGPT)")
        self.assertEqual(recorded["source"], directory.name)
        self.assertEqual(recorded["n"], 65)
        self.assertEqual(recorded["codex_version"], "0.167.0")
        for field in ("operator", "date_utc", "codex_version"):
            self.assertEqual(recorded[field], manifest[field])
        for key, k, n, rate, display in (
            ("B-", 10, 30, "33.3 %", "19.2 % – 51.2 %"),
            ("B+", 19, 30, "63.3 %", "45.5 % – 78.1 %"),
            ("C3", 2, 5, "40.0 %", "11.8 % – 76.9 %"),
        ):
            rows = [{"conditions": {key: run}} for run in recorded["runs"] if run["condition"] == key]
            self.assertEqual(recorded[key], ev.rate_block(rows, key))
            self.assertEqual(recorded[key]["fraction"], f"{k}/{n}")
            self.assertEqual(recorded[key]["rate_display"], rate)
            self.assertEqual(recorded[key]["wilson95"], ev.interval(k, n))
            self.assertEqual(recorded[key]["wilson95"]["display"], display)
        self.assertEqual(recorded["sign_test"], {**ev.sign_test(11, 2), "ties": 17})
        self.assertEqual(recorded["sign_test"]["p_two_sided"], "0.0224609375")
        self.assertTrue(recorded["worse_than_stub"])
        self.assertIn("Codex sale peor", recorded["comparison"])
        ficha = next(row for row in recorded["by_type"] if row["doc_type"] == "ficha_tecnica")
        self.assertEqual((ficha["B-"]["fraction"], ficha["B+"]["fraction"]), ("1/6", "0/6"))
        self.assertIn("skill de OTRO tipo", recorded["control_note"])

    def test_tolerant_scores_and_classification_are_derived_from_each_recording(self):
        directory = ROOT / "experiments/recorded/codex-20261110"
        with patch("record_codex_runs.subprocess.run", side_effect=AssertionError("no modelo")):
            recorded = ev.replay(directory)["codex_recorded"]
        tolerant = recorded["tolerant"]
        self.assertEqual(tolerant["sign_test"], {**ev.sign_test(6, 0), "ties": 24})
        for key, fraction in (("B-", "24/30"), ("B+", "30/30"), ("C3", "4/5")):
            rows = [run for run in recorded["runs"] if run["condition"] == key]
            expected = ev.rate_block([{"conditions": {key: run["tolerant"]}} for run in rows], key)
            self.assertEqual(tolerant[key], expected)
            self.assertEqual(tolerant[key]["fraction"], fraction)
            for block in (recorded, tolerant):
                rate = block[key]
                self.assertEqual(rate["wilson95"], ev.interval(rate["k"], rate["n"]))
        for row in tolerant["by_type"]:
            for key in ("B-", "B+", "C3"):
                rows = [run for run in recorded["runs"] if run["condition"] == key and run["doc_type"] == row["doc_type"]]
                self.assertEqual(row[key], ev.rate_block([{"conditions": {key: run["tolerant"]}} for run in rows], key))
        failures = recorded["failure_classification"]
        self.assertEqual(len(failures), sum(not run["compliant"] for run in recorded["runs"]))
        self.assertEqual(recorded["classification_counts"]["B+"], {"falso negativo del checker": 11, "fallo del modelo": 0})
        for run in recorded["runs"]:
            note = b2b.load_note(rec.fixture_path(run["doc_type"], run["case"]))
            text = (directory / run["file"]).read_text(encoding="utf-8")
            self.assertEqual(run["tolerant"], b2b.check_document_tolerant(note, text))
            strict = b2b.check_document(note, text)
            self.assertEqual({key: run[key] for key in strict}, strict)
            classification = None if run["compliant"] else (
                "falso negativo del checker" if run["tolerant"]["compliant"] else "fallo del modelo")
            self.assertEqual(run["classification"], classification)
            if classification:
                row = next(row for row in failures if row["file"] == run["file"])
                self.assertEqual(row["classification"], classification)
                self.assertEqual(row["tolerant_failures"], run["tolerant"]["failures"])
        markdown = ev.recorded_markdown(recorded)
        rendered = "\n".join(markdown)
        for block in (recorded, tolerant):
            for key in ("B-", "B+", "C3"):
                for value in (block[key]["fraction"], block[key]["rate_display"], block[key]["wilson95"]["display"]):
                    self.assertIn(value, rendered)
            self.assertIn(block["sign_test"]["p_two_sided"], rendered)
        for row in failures:
            self.assertIn(row["file"], rendered)
            self.assertIn(row["classification"], rendered)

    def test_sign_pairs_use_doc_type_case_and_rep_not_run_order(self):
        # En el orden dado, emparejar por posición convertiría los dos empates en cambios.
        rows = []
        for kind, case, rep, condition, ok in (
            ("cotizacion", 2, 1, "B-", False),
            ("cotizacion", 2, 2, "B-", True),
            ("cotizacion", 3, 1, "B-", True),
            ("propuesta_tecnica", 2, 1, "B-", False),
            ("cotizacion", 2, 2, "B+", True),
            ("propuesta_tecnica", 2, 1, "B+", True),
            ("cotizacion", 3, 1, "B+", False),
            ("cotizacion", 2, 1, "B+", False),
        ):
            rows.append({"doc_type": kind, "case": case, "rep": rep, "condition": condition,
                         "compliant": ok, "met": int(ok), "total": 1})
        replayed = {"runs": rows, "codex_version": "test", "source": "test",
                    "date_utc": "2026-11-10T15:00:00Z", "operator": "test"}
        self.assertEqual(ev.summarize_recorded(replayed)["sign_test"], {**ev.sign_test(1, 1), "ties": 2})
        replayed["runs"] = rows[:-1]
        self.assertIsNone(ev.summarize_recorded(replayed)["sign_test"])
        self.assertEqual(ev.summarize_recorded(replayed)["status"], "incompleto")

    def test_replay_cli_persists_statistics_and_stub_preserves_them(self):
        results, markdown = self.directory / "eval.json", self.directory / "EVAL.md"
        with patch.object(ev, "RESULTS", results), patch.object(ev, "EVAL_MD", markdown), redirect_stdout(StringIO()) as output:
            self.assertEqual(ev.main(["--replay", str(ROOT / "experiments/recorded/codex-20261110")]), 0)
            printed = json.loads(output.getvalue())
            persisted = json.loads(results.read_text(encoding="utf-8"))
            self.assertEqual(printed["codex_recorded"], persisted["codex_recorded"])
            before = (results.read_bytes(), markdown.read_bytes())
            ev.write_stub()
            self.assertEqual(before, (results.read_bytes(), markdown.read_bytes()))

    def test_stub_without_recorded_runs_still_renders_pending(self):
        with patch.object(ev, "RESULTS", self.directory / "eval.json"), \
                patch.object(ev, "EVAL_MD", self.directory / "EVAL.md"):
            report = ev.write_stub()
            self.assertEqual(report["codex_recorded"]["status"], ev.PENDING)
            self.assertIsNone(report["codex_recorded"]["runs"])
            self.assertIn(ev.PENDING, ev.render_markdown(report))

    def test_replay_checks_hashes_and_scores_without_a_model(self):
        note_path = rec.fixture_path("cotizacion", 2)
        note = b2b.load_note(note_path)
        text = b2b.draft(note, rec.origin_pack("cotizacion")["events"])["text"]
        folder = self.directory / "codex-test"
        folder.mkdir()
        target = folder / rec.output_name("cotizacion", 2, "B+", 1)
        target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
        job = {
            "doc_type": "cotizacion", "case": 2, "path": note_path,
            "condition": "B+", "rep": 1, "skill_doc_type": "cotizacion",
        }
        manifest = rec.manifest_for(
            [job],
            [{"file": target, "command": "codex exec --sandbox workspace-write -C <workspace>"}],
            "no-ejecutado", "test", "2026-11-10T15:00:00Z",
        )
        (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        scored = ev.replay(folder)
        self.assertTrue(scored["runs"][0]["compliant"])
        self.assertEqual(scored["codex_version"], "no-ejecutado")
        self.assertEqual(scored["codex_recorded"]["status"], "incompleto")
        before = (RESULTS.read_bytes(), EVAL.read_bytes())
        with redirect_stdout(StringIO()):
            self.assertEqual(ev.main(["--replay", str(folder)]), 0)
        self.assertEqual(before, (RESULTS.read_bytes(), EVAL.read_bytes()))
        manifest["runs"].append(dict(manifest["runs"][0]))
        (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ed.Invalid, "duplicado"):
            ev.replay(folder)
        manifest["runs"].pop()
        manifest["runs"][0]["skill_sha256"] = "0" * 64
        (folder / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaises(ed.Invalid):
            ev.replay(folder)
        with redirect_stdout(StringIO()):
            self.assertEqual(ev.main(["--replay", str(folder)]), 2)
        self.assertEqual(before, (RESULTS.read_bytes(), EVAL.read_bytes()))
        example = json.loads((ROOT / "experiments" / "recorded" / "MANIFEST.example.json").read_text(encoding="utf-8"))
        self.assertTrue(example["example_only"])
        self.assertEqual(example["runs"], [])
        (folder / "MANIFEST.json").write_text(json.dumps(example), encoding="utf-8")
        with self.assertRaises(ed.Invalid):
            ev.replay(folder)
        result = subprocess.run(
            [sys.executable, str(ROOT / "experiments" / "eval_b2b.py"), "--replay", str(folder)],
            capture_output=True, encoding="utf-8", timeout=20,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_dry_run_plans_and_does_not_invoke_codex(self):
        self.assertEqual(len(rec.plan_jobs(reps=1, controls=True)), 35)
        self.assertEqual(len(rec.plan_jobs(reps=2)), 60)
        self.assertEqual(len(rec.plan_jobs(limit=1)), 2)
        home = str(Path.home())
        self.assertNotIn(home, rec.sanitize(home + "/notas"))
        self.assertNotIn("/home/", rec.sanitize("/home/alguien/notas"))
        before = sorted(rec.RECORDED.glob("codex-*"))
        buffer = StringIO()
        with patch("record_codex_runs.subprocess.run", side_effect=AssertionError("proceso")), \
                patch("record_codex_runs.record", side_effect=AssertionError("grabó")), \
                redirect_stdout(buffer):
            code = rec.main(["--dry-run", "--limit", "1", "--reps", "1"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertTrue(payload["dry_run"])
        self.assertFalse(payload["codex_executed"])
        self.assertEqual(payload["jobs"], 2)
        self.assertFalse(payload["network"])
        self.assertEqual(sorted(rec.RECORDED.glob("codex-*")), before)
        lesson = rec.origin_pack("ficha_tecnica")["lesson"]
        workspace = self.directory / "workspace"
        workspace.mkdir()
        rec.prepare_workspace(workspace, {
            "path": rec.fixture_path("ficha_tecnica", 2),
            "skill_doc_type": "ficha_tecnica",
        })
        skill = next((workspace / ".agents" / "skills").glob("*/SKILL.md")).read_text(encoding="utf-8")
        agents = (workspace / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(skill + "\n" + agents, rec.skill_bundle(lesson))
        bare = self.directory / "bare"
        bare.mkdir()
        rec.prepare_workspace(bare, {"path": rec.fixture_path("ficha_tecnica", 2), "skill_doc_type": None})
        self.assertFalse((bare / "AGENTS.md").exists())
        self.assertEqual((bare / "note.json").read_bytes(), rec.fixture_path("ficha_tecnica", 2).read_bytes())


if __name__ == "__main__":
    unittest.main()
