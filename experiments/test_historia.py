"""Datos, seguridad y contrato editorial del cartel estático."""

from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

import export_historia as cartel

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.tags = []
        self.content = []
        self.visible_content = []
        self.hidden_depth = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))
        if tag in ('title', 'desc', 'style', 'script'):
            self.hidden_depth += 1

    def handle_endtag(self, tag):
        if tag in ('title', 'desc', 'style', 'script'):
            self.hidden_depth -= 1

    def handle_data(self, data):
        self.content.append(data)
        if not self.hidden_depth:
            self.visible_content.append(data)


class HistoriaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(cartel.SOURCE.read_text(encoding='utf-8'))
        cls.recorded = cls.report['codex_recorded']
        cls.source = cartel.OUT.read_text(encoding='utf-8')
        cls.page = Page(cls.source)
        cls.visible = ' '.join(cls.page.content)

    def test_export_is_byte_identical_in_two_fresh_processes(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / 'index.html'
            program = ('import export_historia as c; import sys; '
                       'c.export(output=sys.argv[1])')
            runs = []
            for _ in range(2):
                subprocess.run([sys.executable, '-B', '-c', program, str(output)],
                               cwd=ROOT / 'experiments', check=True,
                               capture_output=True, timeout=10)
                runs.append(output.read_bytes())
            self.assertEqual(runs[0], runs[1])
            self.assertEqual(runs[0], cartel.OUT.read_bytes())

    def test_every_fraction_and_wilson_is_present_for_both_reviewers(self):
        for block in (self.recorded, self.recorded['tolerant']):
            for group in (block, *block['by_type']):
                for key in cartel.CONDITIONS:
                    metric = group[key]
                    with self.subTest(group=group.get('label', 'Todos'), condition=key):
                        self.assertIn(metric['fraction'], self.visible)
                        self.assertIn(metric['wilson95']['display'], self.visible)

    def test_every_data_table_row_matches_the_json(self):
        table = self.source.split('<caption>Fracciones e intervalos', 1)[1].split('</table>', 1)[0]
        pairs = [('Todos', self.recorded, self.recorded['tolerant'])]
        pairs += [(a['label'], a, b) for a, b in zip(
            self.recorded['by_type'], self.recorded['tolerant']['by_type'])]
        rows = re.findall(r'<tr><th scope="row">(.*?)</tr>', table, re.S)
        self.assertEqual(len(rows), len(pairs) * len(cartel.CONDITIONS))
        for row, (label, a, b, key) in zip(rows, (
                (label, a, b, key) for label, a, b in pairs for key in cartel.CONDITIONS)):
            parsed = ' '.join(Page(row).content)
            for value in (label, key, a[key]['fraction'], b[key]['fraction'],
                          a[key]['wilson95']['display'], b[key]['wilson95']['display']):
                self.assertIn(value, parsed)

    def test_total_signs_and_p_values_come_from_recorded_data(self):
        total = sum(self.recorded[k]['n'] for k in cartel.CONDITIONS)
        self.assertIn(f'{total} corridas', self.visible)
        self.assertIn(f'con {total} documentos', self.visible)
        for block in (self.recorded, self.recorded['tolerant']):
            signs = block['sign_test']
            self.assertIn(f"{signs['improved']} mejoraron, {signs['worsened']} empeoraron", self.visible)
            self.assertIn(f"{signs['ties']} quedaron igual", self.visible)
            self.assertIn(f"n = {signs['n']} sin empates; p = {signs['p_two_sided']}", self.visible)

    def test_changed_json_drives_total_metrics_intervals_and_signs(self):
        report = deepcopy(self.report)
        r = report['codex_recorded']
        for i, block in enumerate((r, r['tolerant'])):
            block['sign_test'].update(improved=41 + i, worsened=21 + i, ties=31 + i,
                                      n=62 + i, p_two_sided=f'0.12345678{i}')
            for j, group in enumerate((block, *block['by_type'])):
                for z, key in enumerate(cartel.CONDITIONS):
                    metric = group[key]
                    metric.update(k=100 + i + j + z, n=200 + i + j + z,
                                  fraction=f'{100 + i + j + z}/{200 + i + j + z}')
                    metric['wilson95']['display'] = f'{12 + i + j + z}.345 % – 98.765 %'
        text = ' '.join(Page(cartel.build_html(report)).content)
        self.assertIn(f"{sum(r[k]['n'] for k in cartel.CONDITIONS)} corridas", text)
        for block in (r, r['tolerant']):
            self.assertIn(cartel.sign_sentence(block), text)
            for group in (block, *block['by_type']):
                for key in cartel.CONDITIONS:
                    self.assertIn(group[key]['fraction'], text)
                    self.assertIn(group[key]['wilson95']['display'], text)

    def test_no_network_resources_scripts_or_css_imports(self):
        for tag, attrs in self.page.tags:
            self.assertNotIn(tag, ('script', 'iframe', 'object', 'embed', 'base'))
            for name, value in attrs.items():
                self.assertFalse(name.startswith('on'), (tag, name))
                if name in ('src', 'href', 'srcset', 'poster', 'action', 'data'):
                    if tag == 'a' and name == 'href':
                        self.assertRegex(value, r'^(?:#|https://(?:github\.com/|[a-z0-9-]+\.github\.io/))')
                    else:
                        self.assertNotRegex(value, r'(?i)(?:https?:)?//')
        css = self.source.split('<style>', 1)[1].split('</style>', 1)[0]
        self.assertNotRegex(css, r'(?i)@import|url\s*\(')

    def test_csp_and_escaped_json_text(self):
        policies = [attrs['content'] for tag, attrs in self.page.tags
                    if tag == 'meta' and attrs.get('http-equiv') == 'Content-Security-Policy']
        self.assertEqual(policies, [cartel.CSP])
        report = deepcopy(self.report)
        payload = '<img src=x onerror="alert(1)"> & <script>oops</script>'
        report['codex_recorded']['by_type'][0]['label'] = payload
        report['codex_recorded']['sign_test']['p_two_sided'] = payload
        report['codex_recorded']['codex_version'] = payload
        page = cartel.build_html(report)
        self.assertNotIn(payload, page)
        self.assertIn(cartel.esc(payload), page)
        self.assertFalse(any(tag in ('img', 'script') for tag, _ in Page(page).tags))

    def test_fiction_post_hoc_and_optimistic_ceiling_are_explicit(self):
        for phrase in ('FICTICIA', 'persona ficticia', 'aprobación fue', 'simulada',
                       'post hoc', 'techo optimista', 'Ficha técnica empeoró',
                       'No prueba ahorro de tiempo ni dinero'):
            self.assertIn(phrase, self.visible)
        self.assertIn('Válvulas y Bombas Ejemplo del Bajío, S.A. de C.V. (FICTICIA)', self.visible)

    def test_private_names_and_real_contact_details_are_absent(self):
        # Split literals keep restricted names out of added source lines too.
        forbidden = ('diime' + 'net', 'sher' + 'lock', 'lá' + 'zaro', 'la' + 'zaro',
                     'system' + ' card', 'qu' + 'ark', 'lanza' + 'pyme', 'plan' + ' z',
                     'radar' + ' stack', 'evidencia' + ' ia', 'ws' + '01', 'an' + 'ton')
        low = self.source.casefold()
        for name in forbidden:
            self.assertNotIn(name, low)
        self.assertNotRegex(low, r'(?<![a-záéíóúüñ])' + 'da' + 'li' + r'(?![a-záéíóúüñ])')
        for row in low.splitlines():
            if 'ka' + 'vak' in row:
                self.assertIn('hackathon', row)
        self.assertNotRegex(self.visible, r'[\w.+-]+@[\w.-]+\.[a-z]{2,}')
        self.assertNotRegex(low, r'/home/|/tmp/|file://')

    def test_accessible_document_and_svg_text_alternatives(self):
        self.assertIn(('html', {'lang': 'es'}), self.page.tags)
        self.assertRegex(self.source, r'<title>[^<]+</title>')
        self.assertIn('width=device-width', self.source)
        self.assertLess(len(self.source.encode('utf-8')), 200_000)
        diagrams = re.findall(r'<svg\b.*?</svg>', self.source, re.S)
        self.assertEqual(len(diagrams), 5)
        ids = []
        ns = {'s': 'http://www.w3.org/2000/svg'}
        for diagram in diagrams:
            tree = ET.fromstring(diagram)
            self.assertEqual(tree.attrib['role'], 'img')
            for name in ('title', 'desc'):
                element = tree.find(f's:{name}', ns)
                self.assertIsNotNone(element)
                self.assertTrue(element.text.strip())
                ids.append(element.attrib['id'])
                self.assertIn(element.attrib['id'], tree.attrib['aria-labelledby'].split())
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIn('@media(max-width:650px)', self.source)
        self.assertIn('overflow-x:auto', self.source)

    def test_design_squares_equal_each_condition_sample_size(self):
        counts = {key: 0 for key in cartel.CONDITIONS}
        for tag, attrs in self.page.tags:
            if tag == 'rect' and attrs.get('data-document') == 'true':
                counts[attrs['data-condition']] += 1
        self.assertEqual(counts, {key: self.recorded[key]['n'] for key in cartel.CONDITIONS})

    def test_unchanged_fractions_never_say_paso_de(self):
        self.assertNotRegex(self.visible, r'pasó de (\d+/\d+) a \1(?![\d/])')
        by = {row['doc_type']: row for row in self.recorded['by_type']}
        for key, label in (('respuesta_soporte', 'Soporte'),
                           ('reporte_cliente', 'Reporte a cliente')):
            self.assertIn(f"{label} se quedó en {by[key]['B+']['fraction']}.", self.visible)

    def test_prose_tracks_equal_rising_and_falling_data_for_both_reviewers(self):
        row = next(r for r in self.recorded['by_type'] if r['doc_type'] == 'cotizacion')
        low, high = row['B-'], row['B+']
        for before, after, phrase in (
                (high, high, f"se quedó en {high['fraction']}"),
                (low, high, f"pasó de {low['fraction']} a {high['fraction']}"),
                (high, low, f"empeoró: de {high['fraction']} a {low['fraction']}")):
            with self.subTest(phrase=phrase):
                report = deepcopy(self.report)
                r = report['codex_recorded']
                for block, key in ((r, 'respuesta_soporte'), (r['tolerant'], 'ficha_tecnica')):
                    target = next(v for v in block['by_type'] if v['doc_type'] == key)
                    target['B-'], target['B+'] = deepcopy(before), deepcopy(after)
                visible = ' '.join(Page(cartel.build_html(report)).visible_content)
                self.assertIn(f'Soporte {phrase}.', visible)
                self.assertIn(f'la ficha técnica {phrase},', visible)
                self.assertNotRegex(visible, r'pasó de (\d+/\d+) a \1(?![\d/])')

    def test_problem_caption_is_visible_exactly_once(self):
        phrase = 'La corrección se queda en el documento, no en la herramienta.'
        self.assertEqual(' '.join(self.page.visible_content).count(phrase), 1)

    def test_design_description_uses_singular_and_plural(self):
        self.assertNotRegex(self.visible, r'\b1 documentos\b')
        for count, noun in ((1, 'documento'), (6, 'documentos')):
            recorded = deepcopy(self.recorded)
            recorded['by_type'][0]['C3']['n'] = count
            tree = ET.fromstring(cartel.design_svg(recorded))
            desc = tree.find('{http://www.w3.org/2000/svg}desc').text
            self.assertIn(f'C3 {count} {noun}', desc)
            self.assertNotRegex(desc, r'\b1 documentos\b')

    def test_wilson_whiskers_center_on_strict_bars_and_labels_clear_them(self):
        ns = {'s': 'http://www.w3.org/2000/svg'}
        tree = ET.fromstring(cartel.results_svg(self.recorded))
        groups = tree.findall('s:g[@class="result-condition"]', ns)
        self.assertEqual(len(groups), len(cartel.CONDITIONS))
        for group, key in zip(groups, cartel.CONDITIONS):
            with self.subTest(condition=key):
                m = self.recorded[key]
                bars = group.findall('s:rect', ns)
                strict = next(b for b in bars if b.attrib['fill'] != 'none')
                center = float(strict.attrib['x']) + float(strict.attrib['width']) / 2
                tolerant = next(b for b in bars if b.attrib['fill'] == 'none')
                self.assertEqual(tolerant.attrib['stroke-dasharray'], '6 5')
                self.assertAlmostEqual(float(tolerant.attrib['y']),
                                       390 - float(self.recorded['tolerant'][key]['rate']) * 280)
                low = 390 - float(m['wilson95']['low']) * 280
                high = 390 - float(m['wilson95']['high']) * 280
                strokes = group.findall('s:g[@class="wilson-interval"]/s:line', ns)
                self.assertEqual(len(strokes), 6)
                for outline, foreground in zip(strokes[:3], strokes[3:]):
                    for coordinate in ('x1', 'y1', 'x2', 'y2'):
                        self.assertEqual(outline.attrib[coordinate], foreground.attrib[coordinate])
                    self.assertEqual(outline.attrib['stroke'], '#fff')
                    self.assertEqual(foreground.attrib['stroke'], '#182637')
                    self.assertGreater(float(outline.attrib['stroke-width']),
                                       float(foreground.attrib['stroke-width']))
                stem, upper, lower = strokes[3:]
                self.assertEqual(float(stem.attrib['x1']), center)
                self.assertEqual(float(stem.attrib['x2']), center)
                self.assertAlmostEqual(float(stem.attrib['y1']), high)
                self.assertAlmostEqual(float(stem.attrib['y2']), low)
                for cap, endpoint in ((upper, high), (lower, low)):
                    self.assertAlmostEqual(float(cap.attrib['y1']), endpoint)
                    self.assertAlmostEqual(float(cap.attrib['y2']), endpoint)
                    self.assertLess(float(cap.attrib['x1']), center)
                    self.assertGreater(float(cap.attrib['x2']), center)
                    self.assertEqual((float(cap.attrib['x1']) + float(cap.attrib['x2'])) / 2, center)
                texts = group.findall('s:text', ns)
                label = next(t for t in texts if t.text == m['fraction'])
                tolerant_label = next(t for t in texts if t.text.startswith('tol. '))
                self.assertEqual(float(label.attrib['x']), center)
                self.assertLessEqual(float(label.attrib['y']), high - 12)
                self.assertLessEqual(float(tolerant_label.attrib['y']), float(label.attrib['y']) - 30)

    def test_section_order_and_readme_link(self):
        labels = re.findall(r'<p class="section-label">(.*?)</p>', self.source)
        self.assertEqual(labels, ['El problema real', 'Cómo lo desarmamos', 'El loop',
                                 'El experimento', 'Resultados', 'Lo que esto NO prueba',
                                 'Qué significa para un negocio como el tuyo', 'Pruébalo'])
        readme = (ROOT / 'README.md').read_text(encoding='utf-8')
        heading = '## La historia, en un cartel'
        self.assertLess(readme.index('## En 30 segundos'), readme.index(heading))
        self.assertLess(readme.index(heading), readme.index('## Resultados'))
        section = readme.split(heading, 1)[1].split('## ', 1)[0].strip()
        self.assertEqual(len(section.splitlines()), 2)
        self.assertIn('](docs/historia/index.html)', section)
        self.assertNotRegex(section, r'\d')


if __name__ == '__main__':
    unittest.main()
