import importlib.util
import unittest
import tempfile
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / 'analysis.py'


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if MODULE.exists():
            spec = importlib.util.spec_from_file_location('analysis', MODULE)
            cls.analysis = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.analysis)

    def test_module_available(self):
        self.assertTrue(MODULE.is_file(), 'The analysis utility must be available')

    def test_reduction_uses_same_task_raw_reference(self):
        self.assertTrue(MODULE.is_file())
        data = {'cross_task': [
            {'task': 'A', 'profile': 'Raw', 'traffic_mib': 100, 'critical_mean_ms': 40, 'success_pct': 80},
            {'task': 'A', 'profile': 'NSPR-8', 'traffic_mib': 10, 'critical_mean_ms': 20, 'success_pct': 78},
        ]}
        row = self.analysis.compare_profiles(data)[0]
        self.assertEqual(row['traffic_reduction_pct'], 90)
        self.assertEqual(row['critical_path_reduction_pct'], 50)
        self.assertEqual(row['success_change_pp'], -2)

    def test_paired_ids_must_match(self):
        self.assertTrue(MODULE.is_file())
        with self.assertRaises(ValueError):
            self.analysis.paired_summary({'1': True}, {'2': True})

    def test_pairing_is_order_independent(self):
        self.assertTrue(MODULE.is_file())
        result = self.analysis.paired_summary({'1': True, '2': False, '3': True}, {'3': False, '2': True, '1': True})
        self.assertEqual(result['both_success'], 1)
        self.assertEqual(result['reference_only'], 1)
        self.assertEqual(result['candidate_only'], 1)
        self.assertEqual(result['both_fail'], 0)

    def test_duplicate_profiles_are_rejected(self):
        self.assertTrue(MODULE.is_file())
        row = {'task': 'A', 'profile': 'Raw', 'traffic_mib': 100, 'critical_mean_ms': 40, 'success_pct': 80}
        with self.assertRaises(ValueError):
            self.analysis.compare_profiles({'cross_task': [row, row]})

    def test_missing_csv_outcome_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / 'outcomes.csv'
            csv.write_text('condition_id,success\na\n')
            with self.assertRaises(ValueError):
                self.analysis.read_outcomes(csv)

    def test_duplicate_csv_condition_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            csv = Path(directory) / 'outcomes.csv'
            csv.write_text('condition_id,success\na,1\na,0\n')
            with self.assertRaises(ValueError):
                self.analysis.read_outcomes(csv)

    def test_invalid_numbers_are_rejected(self):
        for value in [True, float('nan'), -1, '12']:
            row = {'task': 'A', 'profile': 'Raw', 'traffic_mib': value,
                   'critical_mean_ms': 40, 'success_pct': 80}
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.analysis.compare_profiles({'cross_task': [row]}, candidate='Raw')


if __name__ == '__main__':
    unittest.main()
