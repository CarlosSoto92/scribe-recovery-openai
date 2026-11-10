"""La demo Corrige una vez sale del JSON y no pide nada a la red."""

from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments"))
import export_static_demo as exporter

PAGE = ROOT / "docs" / "corrige" / "index.html"
LEGACY = ROOT / "docs" / "demo" / "index.html"
RESULTS = ROOT / "experiments" / "results" / "eval_b2b.json"
DALI = re.compile(r"(?<![a-záéíóúüñ])dali(?![a-záéíóúüñ])", re.IGNORECASE)
BANNED = ("diimenet", "kavak", "sherlock", "lázaro", "lazaro", "system card", "gmail", "hotmail")


class StaticDemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy_before = LEGACY.read_bytes()
        cls.index_before = (ROOT / "docs" / "index.html").read_bytes()
        first = exporter.export_corrige()
        cls.page = PAGE.read_bytes()
        second = exporter.export_corrige()
        assert first == 0 and second == 0
        assert cls.page == PAGE.read_bytes()
        cls.html = cls.page.decode("utf-8")
        cls.results = RESULTS.read_text(encoding="utf-8")

    def test_legacy_demo_url_stays_byte_for_byte(self):
        self.assertEqual(LEGACY.read_bytes(), self.legacy_before)
        self.assertEqual((ROOT / "docs" / "index.html").read_bytes(), self.index_before)
        self.assertIn('url=demo/', (ROOT / "docs" / "index.html").read_text(encoding="utf-8"))

    def test_page_is_local_light_and_labeled(self):
        self.assertLess(len(self.page), 300 * 1024)
        self.assertIn("FICTICIA", self.html)
        self.assertIn("Datos 100 % ficticios", self.html)
        self.assertIn("Writer de demostración (determinista)", self.html)
        self.assertIn("pendiente: corridas de Codex por grabar", self.html)
        self.assertIn("Sin tu aprobación, la IA no la usa.", self.html)
        self.assertEqual(self.html.count('<article class="lesson"'), 5)
        self.assertIn("Convertir en lección", self.html)
        self.assertIn("Retirar lección", self.html)
        self.assertIn("Ver sin la lección", self.html)
        self.assertIn("Ver con la lección", self.html)
        self.assertIn("aprobación simulada · fixture", self.html)
        for word in BANNED:
            self.assertNotIn(word, self.html.casefold(), word)
        self.assertIsNone(DALI.search(self.html))

    def test_no_network_and_unique_anchors(self):
        self.assertNotIn("fetch(", self.html)
        self.assertNotIn("XMLHttpRequest", self.html)
        self.assertNotIn("@import", self.html)
        self.assertNotIn("<img", self.html.casefold())
        urls = re.findall(r"https?://[^\"'\s)]+", self.html)
        for url in urls:
            self.assertTrue(
                url.startswith("https://github.com/CarlosSoto92/scribe-recovery-openai"),
                url,
            )
        ids = re.findall(r'\sid="([^"]+)"', self.html)
        self.assertEqual(len(ids), len(set(ids)))
        for anchor in re.findall(r'href="#([^"]+)"', self.html):
            self.assertIn(anchor, ids)

    def test_visible_figures_come_from_results(self):
        for figure in re.findall(r'data-figure="([^"]+)"', self.html):
            self.assertIn(figure, self.results, figure)
        for token in ("0/15", "15/15", "0/3", "3/3", "0.0 %", "100.0 %", "0.0 % – 20.4 %", "79.6 % – 100.0 %"):
            self.assertIn(token, self.html)
            self.assertIn(token, self.results)
        self.assertIn("Vigencia: 15 días naturales", self.html)
        self.assertIn("Pago: 50 % anticipo, 50 % contra entrega", self.html)

    def test_cli_regenerates_without_touching_the_old_demo(self):
        before = LEGACY.read_bytes()
        result = subprocess.run(
            [sys.executable, str(ROOT / "experiments" / "export_static_demo.py")],
            capture_output=True, encoding="utf-8", timeout=20, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(PAGE.read_bytes(), self.page)
        self.assertEqual(LEGACY.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
