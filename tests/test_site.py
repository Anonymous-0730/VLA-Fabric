import json
import re
import unittest
from zipfile import ZipFile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class SiteTests(unittest.TestCase):
    def test_hero_leads_with_organization_not_profiles(self):
        html = (ROOT / "index.html").read_text()
        hero = re.search(r'<section[^>]+class="hero".*?</section>', html, re.S).group()
        self.assertIn("VLA agents", hero)
        self.assertNotRegex(hero, r"\b(?:Raw|NSPR|MiB|88\.96)\b")
        self.assertIn('<canvas', hero)

    def test_local_links_and_assets_exist(self):
        for page in [ROOT / "index.html", ROOT / "code/index.html"]:
            self.assertTrue(page.is_file(), str(page))
            elements = Elements(page.read_text()).elements
            ids = [attrs['id'] for _, attrs in elements if 'id' in attrs]
            self.assertEqual(len(ids), len(set(ids)), "duplicate IDs")
            for tag, attrs in elements:
                for key in ['href', 'src', 'poster']:
                    value = attrs.get(key, '')
                    url = urlsplit(value)
                    if not value or url.scheme or url.netloc:
                        continue
                    if value.startswith('#'):
                        self.assertIn(value[1:], ids)
                    elif url.path:
                        self.assertTrue((page.parent / unquote(url.path)).exists(), value)

    def test_code_links_open_the_same_anonymous_repository(self):
        html = (ROOT / 'index.html').read_text()
        target = 'https://github.com/Anonymous-0730/VLA-Fabric/tree/main/code'
        self.assertEqual(html.count(f'href="{target}"'), 3)
        self.assertNotIn('Release pending', html)
        self.assertNotRegex(html, r'/data/private|/home/|file://')

    def test_hugging_face_is_a_non_navigating_resource_notice(self):
        html = (ROOT / 'index.html').read_text()
        elements = Elements(html).elements
        buttons = [attrs for tag, attrs in elements
                   if tag == 'button' and attrs.get('id') == 'huggingface-button']
        self.assertEqual(len(buttons), 1)
        self.assertEqual(buttons[0]['type'], 'button')
        self.assertNotIn('href', buttons[0])
        self.assertEqual(buttons[0]['aria-describedby'], 'huggingface-tooltip')
        tooltip = next(attrs for _, attrs in elements
                       if attrs.get('id') == 'huggingface-tooltip')
        self.assertIn('hidden', tooltip)
        self.assertIn('Hugging Face', html)
        self.assertIn('Full models and related resources will be uploaded progressively.', html)

    def test_behavior_assets_have_a_cache_version(self):
        elements = Elements((ROOT / 'index.html').read_text()).elements
        for name, attribute in [('styles.css', 'href'), ('site.js', 'src')]:
            asset = next(attrs[attribute] for _, attrs in elements
                         if urlsplit(attrs.get(attribute, '')).path == name)
            self.assertTrue(urlsplit(asset).query, f'{name} must bypass old cached assets')

    def test_homepage_is_a_research_narrative_not_an_evaluation_dashboard(self):
        html = (ROOT / 'index.html').read_text()
        elements = Elements(html).elements
        sections = [attrs['id'] for tag, attrs in elements
                    if tag == 'section' and 'id' in attrs]
        self.assertEqual(sections, [
            'overview', 'architecture', 'communication', 'demos', 'resources'])
        tables = [attrs for tag, attrs in elements if tag == 'table']
        self.assertEqual([table.get('id') for table in tables], ['task-success-table'])
        self.assertLess(html.index('id="task-success-table"'), html.index('id="communication"'))
        self.assertNotIn('#evaluation', html)
        self.assertNotIn('>Results</', html)

    def test_task_capability_uses_the_published_full_results(self):
        html = (ROOT / 'index.html').read_text()
        rows = [attrs for tag, attrs in Elements(html).elements
                if tag == 'tr' and 'data-task' in attrs]
        self.assertEqual([row['data-task'] for row in rows], [
            'Handover Box', 'Shoes Table', 'Handover Mic',
            'Camera Alignment', 'Stack Cube', 'Take Photo'])
        self.assertIn('150 demonstrations', html)

    def test_evaluation_details_are_available_with_the_code(self):
        document = ROOT / 'code/EVALUATION.md'
        self.assertTrue(document.is_file())
        notes = document.read_text()
        for phrase in ['LIBERO', 'TwinVLA', 'Random Private K/V', 'paired-200',
                       'timing-50', 'Take Photo', '77.5', '96.5', '97.5']:
            self.assertIn(phrase, notes)
        self.assertIn('EVALUATION.md', (ROOT / 'code/README.md').read_text())
        data = json.loads((ROOT / 'code/data/results.json').read_text())
        for row in data['cross_task']:
            values = [row['task'], row['profile'], f"{row['traffic_mib']:.3f}",
                      f"{row['critical_mean_ms']:.3f}", f"{row['critical_p95_ms']:.3f}",
                      f"{row['success_pct']:.1f}"]
            self.assertIn('| ' + ' | '.join(values) + ' |', notes)

    def test_paper_protocols_are_separate(self):
        data = json.loads((ROOT / 'code/data/results.json').read_text())
        self.assertEqual(data['protocol']['success_trials'], 200)
        self.assertEqual(data['protocol']['timing_trials'], 50)
        rows = data['cross_task']
        self.assertEqual(len(rows), 12)
        photo = {r['profile']: r for r in rows if r['task'] == 'Take Photo'}
        self.assertEqual(photo['Raw']['success_pct'], 77.5)
        self.assertEqual(photo['Full']['success_pct'], 96.5)
        self.assertEqual(photo['NSPR-8']['success_pct'], 97.5)

    def test_browser_data_matches_download(self):
        source = json.loads((ROOT / 'code/data/results.json').read_text())
        generated = (ROOT / 'assets/results.js').read_text().split('window.FABRIC_RESULTS = ', 1)[1]
        self.assertEqual(source, json.loads(generated.strip().removesuffix(';')))

    def test_code_archive_is_an_allowlisted_release(self):
        with ZipFile(ROOT / 'assets/downloads/vla-fabric-tools.zip') as archive:
            self.assertEqual(set(archive.namelist()), {
                'analysis.py', 'plot_results.py', 'README.md', 'LICENSE',
                'EVALUATION.md', 'data/results.json', 'tests/test_analysis.py'})
            for relative in archive.namelist():
                self.assertEqual(archive.read(relative), (ROOT / 'code' / relative).read_bytes())


if __name__ == '__main__':
    unittest.main()
