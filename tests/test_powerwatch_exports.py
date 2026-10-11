import importlib.util
import csv
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location("pipeline", Path(__file__).resolve().parents[1] / "src/audit_powerwatch_exports.py")
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


class MeasurementSemantics(unittest.TestCase):
    def test_zero_is_observed_and_blank_is_missing(self):
        self.assertEqual(pipeline.parse_value("0"), (0.0, "numeric_observation"))
        self.assertEqual(pipeline.parse_value(""), (None, "missing_measurement"))
        self.assertEqual(pipeline.parse_value("broken"), (None, "invalid_value"))
        self.assertEqual(pipeline.parse_value("inf"), (None, "invalid_value"))

    def test_observed_source_zone_to_utc(self):
        self.assertEqual(pipeline.parse_time("2025-01-25 00:00:00", "Africa/Kigali", "local_string"),
                         datetime(2025, 1, 24, 22, tzinfo=timezone.utc))

    def test_epoch_units_must_be_explicit(self):
        self.assertEqual(pipeline.parse_time("1737756000000", "Africa/Kigali", "unix_ms"),
                         datetime(2025, 1, 24, 22, tzinfo=timezone.utc))
        with self.assertRaises(ValueError):
            pipeline.parse_time("1737756000000", "Africa/Kigali", "guess")

    def test_missing_runs_are_not_outage_events(self):
        start = datetime(2025, 1, 25, tzinfo=timezone.utc)
        slots = [start + timedelta(minutes=2 * i) for i in range(6)]
        self.assertEqual(pipeline.longest_missing_run(slots, {slots[0], slots[4]}), 3)

    def test_frequency_under_low_voltage_gets_distinct_flag(self):
        screen = {"low_voltage_candidate_below_V": 23, "frequency_review_below_Hz": 45,
                  "frequency_review_above_Hz": 65}
        flags = pipeline.observation_flags("frequency", 7813, 0.3, screen)
        self.assertIn("frequency_with_low_voltage_not_interpretable", flags)
        self.assertIn("frequency_outside_screen_review", flags)
        self.assertEqual(pipeline.observation_flags("voltage", 0, None, screen),
                         ["low_voltage_candidate_not_verified_outage"])


class SourceIntegrityAndConflicts(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).resolve().parents[1]
        self.root.joinpath("outputs/private").mkdir(parents=True,exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=self.root / "outputs/private")
        self.work = Path(self.temp.name)
        self.source = self.work / "synthetic.csv"
        self.source.write_text('Time,Voltage ABCDEF12 (Synthetic Test),Frequency ABCDEF12 (Synthetic Test)\n'
            '2025-01-25 00:00:00,0,7813\n2025-01-25 00:02:00,230,50\n'
            '2025-01-25 00:02:00,220,50\n2025-01-25 00:04:00,,broken\n')
        self.manifest = self.work / "manifest.json"
        self.registry = self.work / "registry.json"
        self.data = {"exports": [{"export_id": "SYNTHETIC", "active_for_pipeline": True,
            "relative_path": str(self.source.relative_to(self.root)), "sha256": pipeline.sha256(self.source),
            "query_start_local": "2025-01-25T00:00:00", "query_end_exclusive_local": "2025-01-25T00:06:00",
            "timestamp_format": "local_string", "selected_site_ids": ["S999", "S998"], "formatted_data": False}]}
        self.manifest.write_text(json.dumps(self.data))
        self.registry.write_text(json.dumps({"sensors": [{"dashboard_aliases": ["Synthetic Test"],
            "source_sensor_serial": "ABCDEF12", "site_id": "S999", "sensor_id": "M999",
            "circuit_id": "unresolved", "mapping_status": "synthetic"}]}))

    def tearDown(self):
        self.temp.cleanup()

    def test_conflicting_duplicate_excluded_and_missing_preserved(self):
        out = self.work / "out"
        report = pipeline.build(self.manifest, self.registry, out)
        with (out / "coverage.csv").open() as stream:
            rows = list(csv.DictReader(stream))
        voltage = next(row for row in rows if row["metric"] == "voltage")
        self.assertEqual(voltage["expected_slots"], "3")
        self.assertEqual(voltage["unambiguous_numeric_slots"], "1")
        self.assertEqual(voltage["missing_measurement_slots"], "1")
        self.assertEqual(voltage["conflicting_slots"], "1")
        self.assertEqual(report["record_count"], 8)
        with (out / "selected_site_returns.csv").open() as stream:
            returns = list(csv.DictReader(stream))
        self.assertEqual(returns[1]["interpretation"], "no_series_returned_not_outage_evidence")

    def test_changed_source_hash_blocks_processing(self):
        self.source.write_text(self.source.read_text() + "2025-01-25 00:06:00,230,50\n")
        with self.assertRaisesRegex(ValueError, "Source hash mismatch"):
            pipeline.build(self.manifest, self.registry, self.work / "out")

    def test_unknown_sensor_blocks_silent_misattribution(self):
        self.registry.write_text(json.dumps({"sensors": []}))
        with self.assertRaisesRegex(ValueError, "Unmapped sensor"):
            pipeline.build(self.manifest, self.registry, self.work / "out")


if __name__ == "__main__":
    unittest.main()
