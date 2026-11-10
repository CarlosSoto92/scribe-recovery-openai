"""Enlaces internos, números del README y nombres que no deben colarse."""

from pathlib import Path
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
        for number in re.findall(r"\d+(?:[.,]\d+)?", section):
            self.assertIn(number, raw, number)
        for phrase in ("0/15", "15/15", "0.0 %", "100.0 %", "0.0 % – 20.4 %", "79.6 % – 100.0 %",
                       "pendiente: corridas de Codex por grabar"):
            self.assertIn(phrase, section)
            self.assertIn(phrase, raw)

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
