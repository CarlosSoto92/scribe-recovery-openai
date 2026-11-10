"""Demo reproducible: V1 falla, Scribe observa y V2 consume una lección."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "src" / "scribe_recovery.py"
FIXTURE = ROOT / "experiments" / "fixtures" / "inventory.csv"


def execute(version, ledger, run_id):
    command = [sys.executable, str(CLI), version, "--input", str(FIXTURE),
               "--ledger", str(ledger), "--run-id", run_id]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10)
    print(f"{version.upper()} ({run_id}) exit={result.returncode}")
    print(result.stdout.strip())
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result.returncode, json.loads(result.stdout)


def demonstrate(directory):
    ledger = directory / "ledger.jsonl"
    negative = directory / "without-lesson.jsonl"
    v1_code, v1 = execute("v1", ledger, "demo")
    prefix = ledger.read_bytes()
    v2_code, v2 = execute("v2", ledger, "demo")
    negative_code, control = execute("v2", negative, "control")
    checks = {
        "v1_fails_csv_schema": v1_code == 1 and (v1.get("error") or {}).get("code") == "CSV_SCHEMA",
        "scribe_records_lesson": (v1.get("lesson") or {}).get("delimiter") == ";",
        "v2_recovers_total_6": v2_code == 0 and (v2.get("result") or {}).get("total") == 6,
        "v2_consumes_lesson": v2.get("evidence", {}).get("lesson_source_attempt") == 1,
        "negative_fails_without_lesson": negative_code == 1 and control.get("outcome") == "failed"
            and control.get("evidence", {}).get("lesson_source_attempt") is None,
        "append_only_two_attempts": ledger.read_bytes().startswith(prefix)
            and [json.loads(line)["attempt"] for line in ledger.read_text().splitlines()] == [1, 2],
    }
    print(json.dumps({"checks": checks, "passed": all(checks.values())}, ensure_ascii=False))
    return all(checks.values())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, help="carpeta existente donde crear una corrida nueva")
    args = parser.parse_args(argv)
    started = time.perf_counter()
    try:
        if args.output_dir:
            # Cada ejecución reserva una carpeta nueva; nunca sobrescribe evidencia.
            directory = Path(tempfile.mkdtemp(prefix="scribe-recovery-", dir=args.output_dir))
            print(f"Evidencia conservada: {directory}")
            passed = demonstrate(directory)
        else:
            with tempfile.TemporaryDirectory(prefix="scribe-recovery-") as temporary:
                print(f"Evidencia temporal: {temporary} (se elimina al terminar)")
                passed = demonstrate(Path(temporary))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"DEMO FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"Duración: {time.perf_counter() - started:.3f} s; API del producto: 0 llamadas / USD 0.")
    print("Consumo de suscripción Codex: no disponible; no se infieren créditos restantes.")
    print("DEMO PASS" if passed else "DEMO FAILED")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
