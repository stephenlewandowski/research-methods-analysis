"""Regression checks for displayed observations, statistics, and lesson timing."""
from pathlib import Path
import csv
import importlib.util
import json
import re
import unittest
import xml.etree.ElementTree as ET

import numpy as np
from scipy import stats


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lesson_renderer', ROOT / 'source' / 'render_ttest.py')
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class PackageRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        renderer.configure(ROOT)

    def test_chapter_seven_points_match_statistics_at_start_and_during_hold(self):
        """A paused chapter must show the same sample used by its statistics."""
        scenario = renderer.S['size']
        for elapsed in [0, 0.5, 1.2, 2.4, 4]:
            with self.subTest(elapsed=elapsed):
                renderer.draw(6, elapsed)
                collections = renderer.fig.axes[0].collections
                self.assertEqual(len(collections), 2)
                a, b = [np.asarray(c.get_offsets())[:, 0] for c in collections]
                self.assertEqual(len(a), 80)
                self.assertEqual(len(b), 80)
                np.testing.assert_allclose(a, scenario['a'], rtol=0, atol=1e-12)
                np.testing.assert_allclose(b, scenario['b'], rtol=0, atol=1e-12)
                # Check statistics from the rendered data, not from label constants.
                actual = stats.ttest_ind(a, b, equal_var=False)
                text = '\n'.join(t.get_text() for t in renderer.fig.texts)
                self.assertIn('n = 80 per group', text)
                self.assertIn(f't = {actual.statistic:.2f}', text)
                self.assertIn('p ' + renderer.pstr(actual.pvalue), text)
                se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
                self.assertIn(f'{se:.2f} seconds', text)
                for collection in collections:
                    self.assertNotEqual(collection.get_alpha(), 0)

    def test_all_stored_scenarios_agree_with_independent_scipy_analysis(self):
        for name, scenario in renderer.S.items():
            with self.subTest(scenario=name):
                result = stats.ttest_ind(scenario['a'], scenario['b'], equal_var=False)
                interval = result.confidence_interval(confidence_level=0.95)
                self.assertAlmostEqual(result.statistic, scenario['t'], places=11)
                self.assertAlmostEqual(result.pvalue, scenario['p'], places=11)
                self.assertAlmostEqual(result.df, scenario['df'], places=10)
                np.testing.assert_allclose(interval, scenario['ci'], rtol=0, atol=1e-10)

    def test_exported_baseline_csv_retains_verified_teaching_result(self):
        with (ROOT / 'ramp_hazard_training.csv').open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 40)
        self.assertEqual(len({row['worker_id'] for row in rows}), 40)
        a = [float(row['report_seconds']) for row in rows if row['training'] == '1']
        b = [float(row['report_seconds']) for row in rows if row['training'] == '2']
        self.assertEqual((len(a), len(b)), (20, 20))
        result = stats.ttest_ind(a, b, equal_var=False)
        self.assertAlmostEqual(result.statistic, 2.371708245126282, places=8)
        self.assertAlmostEqual(result.pvalue, 0.022875801799123525, places=8)

    def test_chapters_timeline_and_caption_files_remain_aligned(self):
        timeline = json.loads((ROOT / 'source' / 'timeline.json').read_text(encoding='utf-8'))
        self.assertEqual(timeline, renderer.SCENES)
        starts = [scene['start'] for scene in timeline]
        template = (ROOT / 'source' / 'classroom_template.html').read_text(encoding='utf-8')
        self.assertEqual([int(value) for value in re.findall(r'data-start="(\d+)"', template)], starts)
        self.assertEqual(timeline[0]['start'], 0)
        self.assertEqual(timeline[-1]['end'], 126)
        for previous, following in zip(timeline, timeline[1:]):
            self.assertEqual(previous['end'], following['start'])
        for name in ['RSCH650_T_Test_Captions.srt', 'RSCH650_T_Test_Captions.vtt']:
            captions = (ROOT / name).read_text(encoding='utf-8')
            self.assertEqual(captions.count(' --> '), len(timeline))
            for scene in timeline:
                self.assertIn(scene['caption'], captions)

    def test_paired_example_agrees_with_scipy(self):
        folder = ROOT / 'spss-worked-example'
        with (folder / 'ramp_hazard_paired.csv').open(encoding='utf-8', newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 20)
        a = [float(row['before_seconds']) for row in rows]
        b = [float(row['after_seconds']) for row in rows]
        result = stats.ttest_rel(a, b)
        expected = json.loads((folder / 'expected_results.json').read_text(encoding='utf-8'))['paired']['test']
        self.assertAlmostEqual(result.statistic, expected['t'], places=10)
        self.assertAlmostEqual(result.pvalue, expected['p_two_sided'], places=12)
        np.testing.assert_allclose(result.confidence_interval(), [expected['ci95_lower'], expected['ci95_upper']], rtol=0, atol=1e-10)

    def test_native_spss_tables_match_independent_references(self):
        validation_spec = importlib.util.spec_from_file_location('native_validation', ROOT / 'source' / 'validate_spss.py')
        validation = importlib.util.module_from_spec(validation_spec)
        validation_spec.loader.exec_module(validation)
        folder = ROOT / 'spss-worked-example'
        expected = json.loads((folder / 'expected_results.json').read_text(encoding='utf-8'))
        for name in ['independent', 'paired']:
            with self.subTest(analysis=name):
                validation.compare_native(ET.parse(folder / 'native-output' / (name + '.xml')), name, expected)


if __name__ == '__main__':
    unittest.main()
