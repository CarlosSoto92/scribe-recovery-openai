"""Enlaces internos, números del README y nombres que no deben colarse."""

from pathlib import Path
import json
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments" / "results" / "eval_b2b.json"
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)|!\[[^\]]*\]\(([^)\s]+)\)")
DALI = re.compile(r"(?<![a-záéíóúüñ])dali(?![a-záéíóúüñ])")


def strip_code(text):
    return re.sub(r"```.*?```", "", text, flags=re.S)


def _diff_base():
    """Ancestro común remoto, con refs directas como respaldo."""
    result = subprocess.run(
        ["git", "merge-base", "HEAD", "origin/main"],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()
    for ref in ("origin/main", "main"):
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"{ref}^{{commit}}"],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            return ref
    raise AssertionError(
        "No hay base Git usable para added_lines(): falló merge-base HEAD "
        "origin/main y no se pudo resolver origin/main ni main como commit. "
        f"Último error de Git: {result.stderr.strip()}"
    )


def added_lines():
    """Líneas nuevas, salvo los tests que nombran la lista para poder vigilarla."""
    diff = subprocess.run(
        ["git", "-c", "diff.mnemonicprefix=false", "-c", "diff.noprefix=false",
         "diff", _diff_base(), "--unified=0", "--", ".", ":(exclude)*.png"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    current = ""
    found = []
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current = line[6:]
        elif line.startswith("+") and not line.startswith("+++") and not current.startswith("experiments/test_"):
            found.append(line[1:])
    return found


class DocsTests(unittest.TestCase):
    def test_relative_links_resolve(self):
        pages = [ROOT / "README.md", ROOT / "CONTRIBUTING.md", *ROOT.glob("docs/**/*.md")]
        for path in pages:
            text = strip_code(path.read_text(encoding="utf-8"))
            for match in LINK.finditer(text):
                target = match.group(1) or match.group(2)
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                file_part = target.split("#", 1)[0]
                if not file_part:
                    continue
                resolved = (path.parent / file_part).resolve()
                self.assertTrue(resolved.exists(), f"{path.relative_to(ROOT)} → {target}")

    def test_result_numbers_come_from_the_eval_json(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        section = readme.split("## Resultados", 1)[1].split("## ", 1)[0]
        raw = RESULTS.read_text(encoding="utf-8")
        report = json.loads(raw)
        for number in re.findall(r"\d+(?:[.,]\d+)?", section):
            self.assertIn(number, raw, number)
        phrases = []
        for block, keys in ((report["held_out"], ("B-", "B+")), (report["codex_recorded"], ("B-", "B+", "C3"))):
            for key in keys:
                phrases += [block[key]["fraction"], block[key]["rate_display"], block[key]["wilson95"]["display"]]
        for phrase in phrases:
            self.assertIn(phrase, section)
            self.assertIn(phrase, raw)
        self.assertEqual(report["held_out"]["B-"]["fraction"], "0/15")
        self.assertEqual(report["held_out"]["B+"]["fraction"], "15/15")
        recorded = report["codex_recorded"]
        for phrase in (recorded["label"], recorded["operator"], recorded["date_utc"],
                       recorded["sign_test"]["p_two_sided"], recorded["comparison"], *recorded["observations"]):
            self.assertIn(phrase, section)
        self.assertIn(f"N = {recorded['n']}", section)

    def test_docs_acknowledge_recorded_runs_and_their_limits(self):
        report = json.loads(RESULTS.read_text(encoding="utf-8"))
        recorded = report["codex_recorded"]
        for name in ("README.md", "docs/EVAL.md", "docs/ARCHITECTURE.md", "docs/LIMITATIONS.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            for phrase in (recorded["source"], recorded["date_utc"], recorded["operator"], "regex"):
                self.assertIn(phrase, text, name)
            self.assertRegex(text, r"no (?:es )?determinista", name)
            for stale in ("pendiente: corridas de Codex por grabar", "no grabado aún", "no hay salidas grabadas",
                          "no está hecha", "Hoy esa carpeta no existe"):
                self.assertNotIn(stale, text, name)

    def test_new_lines_keep_private_names_inside_the_frontier_notice(self):
        problems = []
        for line in added_lines():
            low = line.casefold()
            if "diimenet" in low:
                problems.append(line)
            if DALI.search(low):
                problems.append(line)
            if "sherlock" in low or "lázaro" in low or "lazaro" in low:
                problems.append(line)
            if "kavak" in low and "hackathon" not in low:
                problems.append(line)
            if "system card" in low and "frontera" not in low and "no incluye" not in low:
                problems.append(line)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
