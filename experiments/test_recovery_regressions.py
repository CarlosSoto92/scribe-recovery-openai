"""Regresión del mecanismo causal de Fase 0; solo archivos sintéticos temporales."""

from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import scribe_recovery as recovery


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="scribe-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.input = self.directory / "inventory.csv"
        self.ledger = self.directory / "ledger.jsonl"
        self.input.write_text("producto;cantidad\nuno;2\ndos;4\n", encoding="utf-8")

    def attempt(self, version, run_id="test"):
        return recovery.run_attempt(version, self.input, self.ledger, run_id)

    def replace_event(self, event):
        # Alteración deliberada de una fixture de prueba, no operación del producto.
        self.ledger.write_text(json.dumps(event) + "\n", encoding="utf-8")

    def cli(self, version, ledger=None):
        return subprocess.run(
            [sys.executable, str(ROOT / "src" / "scribe_recovery.py"), version,
             "--input", str(self.input), "--ledger", str(ledger or self.ledger),
             "--run-id", "cli"], capture_output=True, text=True, timeout=10,
        )

    def test_v1_preserves_failure_and_structured_lesson(self):
        event = self.attempt("v1")
        self.assertEqual(event["outcome"], "failed")
        self.assertEqual(event["error"]["code"], "CSV_SCHEMA")
        self.assertIn("producto;cantidad", event["error"]["message"])
        self.assertEqual(event["lesson"], {
            "kind": "csv_delimiter", "delimiter": ";",
            "observed_header": "producto;cantidad",
        })
        self.assertEqual(event["run_id"], "test")
        self.assertEqual(event["attempt"], 1)
        self.assertEqual(event["task_id"], recovery.TASK_ID)
        self.assertEqual(event["input_sha256"], hashlib.sha256(self.input.read_bytes()).hexdigest())
        self.assertEqual(datetime.fromisoformat(event["timestamp"]).utcoffset(), timedelta(0))
        self.assertIsNone(event["result"])
        self.assertEqual(recovery.read_ledger(self.ledger), [event])

    def test_v2_reads_lesson_and_preserves_prefix(self):
        first = self.attempt("v1")
        prefix = self.ledger.read_bytes()
        second = self.attempt("v2")
        self.assertEqual(second["outcome"], "success")
        self.assertEqual(second["result"], {"total": 6, "rows": 2})
        self.assertEqual(second["evidence"], {"delimiter_used": ";", "lesson_source_attempt": 1})
        self.assertIsNone(second["error"])
        self.assertTrue(self.ledger.read_bytes().startswith(prefix))
        self.assertEqual(recovery.read_ledger(self.ledger), [first, second])

    def test_without_lesson_v2_really_executes_and_fails(self):
        with patch.object(recovery, "sum_inventory", wraps=recovery.sum_inventory) as task:
            event = self.attempt("v2")
        self.assertEqual(task.call_count, 1)
        self.assertEqual(event["attempt"], 2)
        self.assertEqual(event["outcome"], "failed")
        self.assertEqual(event["error"]["code"], "CSV_SCHEMA")
        self.assertEqual(event["evidence"], {"delimiter_used": ",", "lesson_source_attempt": None})

    def test_lesson_removed_from_v1_prevents_recovery(self):
        event = self.attempt("v1")
        event["lesson"] = None
        self.replace_event(event)
        self.assertEqual(self.attempt("v2")["outcome"], "failed")

    def test_other_run_lesson_is_not_consumed(self):
        self.attempt("v1", "other")
        event = self.attempt("v2")
        self.assertEqual(event["outcome"], "failed")
        self.assertIsNone(event["evidence"]["lesson_source_attempt"])

    def test_other_input_lesson_is_not_consumed(self):
        self.attempt("v1")
        self.input.write_text("producto;cantidad\nuno;99\n", encoding="utf-8")
        event = self.attempt("v2")
        self.assertEqual(event["outcome"], "failed")
        self.assertIsNone(event["evidence"]["lesson_source_attempt"])

    def test_other_task_lesson_is_not_consumed(self):
        event = self.attempt("v1")
        event["task_id"] = "different_task"
        self.replace_event(event)
        event = self.attempt("v2")
        self.assertEqual(event["outcome"], "failed")
        self.assertIsNone(event["evidence"]["lesson_source_attempt"])

    def test_exactly_one_task_execution_per_attempt_and_one_retry(self):
        with patch.object(recovery, "sum_inventory", wraps=recovery.sum_inventory) as task:
            self.attempt("v1")
            self.assertEqual(task.call_count, 1)
            prefix = self.ledger.read_bytes()
            with self.assertRaisesRegex(recovery.DemoError, "ATTEMPT_ALREADY_RECORDED"):
                self.attempt("v1")
            self.assertEqual(self.ledger.read_bytes(), prefix)
            self.attempt("v2")
            self.assertEqual(task.call_count, 2)
            completed = self.ledger.read_bytes()
            for version in ("v1", "v2"):
                with self.assertRaisesRegex(recovery.DemoError, "ATTEMPT_ALREADY_RECORDED"):
                    self.attempt(version)
            self.assertEqual(task.call_count, 2)
            self.assertEqual(self.ledger.read_bytes(), completed)
        self.assertEqual([e["attempt"] for e in recovery.read_ledger(self.ledger)], [1, 2])

    def test_failed_retry_cannot_be_repeated(self):
        self.attempt("v2")
        prefix = self.ledger.read_bytes()
        with self.assertRaisesRegex(recovery.DemoError, "ATTEMPT_ALREADY_RECORDED"):
            self.attempt("v2")
        self.assertEqual(self.ledger.read_bytes(), prefix)

    def test_derived_delimiters_and_actual_arithmetic(self):
        for delimiter in ("|", "\t"):
            with self.subTest(delimiter=delimiter):
                self.input.write_text(
                    f"producto{delimiter}cantidad\nuno{delimiter}13\ndos{delimiter}8\n",
                    encoding="utf-8",
                )
                first = self.attempt("v1")
                self.assertEqual(first["lesson"]["delimiter"], delimiter)
                second = self.attempt("v2")
                self.assertEqual(second["result"], {"total": 21, "rows": 2})
                self.assertEqual(second["evidence"]["delimiter_used"], delimiter)

    def test_malformed_ledgers_are_not_repaired_or_appended(self):
        for raw in (b"{truncated", b"not-json\n", b"{}\n", b"[]\n", b"\n"):
            with self.subTest(raw=raw):
                self.ledger.write_bytes(raw)
                with patch.object(recovery, "sum_inventory") as task:
                    with self.assertRaisesRegex(recovery.DemoError, "LEDGER_INVALID"):
                        self.attempt("v2")
                    task.assert_not_called()
                self.assertEqual(self.ledger.read_bytes(), raw)

    def test_incompatible_lesson_rejected_before_task(self):
        event = self.attempt("v1")
        for field, value in (("kind", "unknown"), ("delimiter", "xx"),
                             ("delimiter", "\n"), ("observed_header", "different")):
            with self.subTest(field=field, value=value):
                broken = dict(event, lesson=dict(event["lesson"], **{field: value}))
                self.replace_event(broken)
                prefix = self.ledger.read_bytes()
                with patch.object(recovery, "sum_inventory") as task:
                    with self.assertRaisesRegex(recovery.DemoError, "LESSON_INCOMPATIBLE"):
                        self.attempt("v2")
                    task.assert_not_called()
                self.assertEqual(self.ledger.read_bytes(), prefix)

    def test_input_cannot_be_ledger_even_through_hardlink(self):
        original = self.input.read_bytes()
        self.ledger.hardlink_to(self.input)
        for ledger in (self.input, self.ledger):
            with self.subTest(ledger=ledger):
                with self.assertRaisesRegex(recovery.DemoError, "INPUT_LEDGER_CONFLICT"):
                    recovery.run_attempt("v1", self.input, ledger, "test")
        self.assertEqual(self.input.read_bytes(), original)

    def test_allowed_delimiter_incompatible_with_header_is_rejected(self):
        event = self.attempt("v1")
        event["lesson"]["delimiter"] = ","
        self.replace_event(event)
        prefix = self.ledger.read_bytes()
        with patch.object(recovery, "sum_inventory", wraps=recovery.sum_inventory) as task:
            with self.assertRaisesRegex(recovery.DemoError, "LESSON_INCOMPATIBLE"):
                self.attempt("v2")
            task.assert_not_called()
        self.assertEqual(self.ledger.read_bytes(), prefix)

    def test_cli_exit_codes_and_persisted_result(self):
        first = self.cli("v1")
        self.assertEqual(first.returncode, 1, first.stderr)
        self.assertEqual(json.loads(first.stdout)["error"]["code"], "CSV_SCHEMA")
        second = self.cli("v2")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(json.loads(second.stdout)["result"]["total"], 6)
        invalid = self.cli("v2")
        self.assertEqual(invalid.returncode, 2, invalid.stderr)
        self.assertEqual(json.loads(invalid.stdout)["outcome"], "invalid")
        negative = self.cli("v2", self.directory / "negative.jsonl")
        self.assertEqual(negative.returncode, 1, negative.stderr)

    def test_demo_default_and_repeated_preserved_evidence(self):
        command = [sys.executable, str(ROOT / "experiments" / "demo.py")]
        default = subprocess.run(command, capture_output=True, text=True, timeout=10)
        self.assertEqual(default.returncode, 0, default.stdout + default.stderr)
        temporary_path = Path(default.stdout.splitlines()[0].split(": ", 1)[1].split(" (", 1)[0])
        self.assertFalse(temporary_path.exists())
        previous = {}
        for _ in range(2):
            result = subprocess.run(command + ["--output-dir", str(self.directory)],
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            summary = next(json.loads(line) for line in result.stdout.splitlines()
                           if line.startswith('{"checks":'))
            self.assertEqual(len(summary["checks"]), 6)
            self.assertTrue(all(summary["checks"].values()))
            self.assertTrue(summary["passed"])
            self.assertIn("API del producto: 0 llamadas / USD 0", result.stdout)
            for path, raw in previous.items():
                self.assertEqual(path.read_bytes(), raw)
            directories = list(self.directory.glob("scribe-recovery-*"))
            self.assertEqual(len(directories), _ + 1)
            for directory in directories:
                self.assertEqual([e["attempt"] for e in recovery.read_ledger(directory / "ledger.jsonl")], [1, 2])
                self.assertEqual(recovery.read_ledger(directory / "without-lesson.jsonl")[0]["outcome"], "failed")
            previous = {p: p.read_bytes() for d in directories for p in d.glob("*.jsonl")}


if __name__ == "__main__":
    unittest.main()
