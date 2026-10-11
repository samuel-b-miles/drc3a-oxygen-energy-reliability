import csv,gzip,importlib.util,json,sys,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from preserve_source_workbook import cell_signature, build as preserve
from audit_drc2_failure_coding import matches,normalize,CONCENTRATOR_PATTERNS
from train_reviewed_equipment_model import load_reviewed
from release_powerwatch_derivatives import release
from datetime import datetime,timezone

class ReleaseIntegrity(unittest.TestCase):
    def test_snapshot_preserves_source_formulas_cached_values_and_errors(self):
        raw=ROOT/'data/raw/private/ndosho/historical/source.xlsx'
        public=ROOT/'data/collections/ndosho/historical/charlie_kwh_snapshot_deidentified.xlsx'
        audit=json.loads(public.with_name('preservation_audit.json').read_text())
        with zipfile.ZipFile(public) as z:
            signature,counts=cell_signature(z)
            self.assertEqual(signature,audit['preserved_cell_signature_sha256'])
            self.assertEqual(counts['formula_cells'],144147);self.assertEqual(counts['existing_error_cells'],13)
            self.assertIn('xl/charts/chart1.xml',z.namelist())
            self.assertNotIn('xl/media/image1.png',z.namelist())
        if raw.exists():
            with zipfile.ZipFile(raw) as z:self.assertEqual(cell_signature(z,{'saidi_ndosho':'saidi_N001'})[0],signature)

    def test_released_measurements_have_no_source_sensor_identifiers(self):
        p=ROOT/'data/collections/goma/powerwatch/readings.csv.gz'
        with gzip.open(p,'rt') as f:
            rows=csv.DictReader(f);self.assertNotIn('source_sensor_serial',rows.fieldnames)
            count=0
            for row in rows:
                self.assertRegex(row['site_id'],r'^S\d{3}$');self.assertRegex(row['sensor_id'],r'^M\d{3}$');count+=1
            self.assertEqual(count,430560)

    def test_current_export_denominator_stops_at_acquisition(self):
        p=ROOT/'data/collections/ndosho/powerwatch/current_week/export_manifest.json'
        item=json.loads(p.read_text())['exports'][0]
        end=datetime.fromisoformat(item['query_end_exclusive_local']).replace(tzinfo=timezone.utc)
        acquisition=datetime.fromisoformat(item['acquired_at_utc'])
        self.assertAlmostEqual(end.timestamp()-acquisition.timestamp(),7200,places=3)
        self.assertLess(item['query_end_exclusive_local'],item['actual_ui_query_end_local'])

    def test_release_rejects_unexpected_private_reading_fields(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'readings.csv').write_text('core_id,voltage\nprivate,230\n')
            (root/'manifest.json').write_text('{"exports":[]}')
            (root/'registry.json').write_text('{"sites":[],"sensors":[]}')
            with self.assertRaisesRegex(ValueError,'Unexpected public reading fields'):
                release(root,root/'manifest.json',root/'registry.json',root/'public')

class ClaimBoundaries(unittest.TestCase):
    def test_unspecified_oxygen_and_oximetry_do_not_become_concentrators(self):
        self.assertFalse(matches(normalize('oxygène et oxymètre'),CONCENTRATOR_PATTERNS))
        self.assertTrue(matches(normalize("Concentrateurs d’oxygène"),CONCENTRATOR_PATTERNS))

    def test_unreviewed_rule_labels_cannot_train_a_supervised_model(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'labels.csv';p.write_text('human_reviewed,reviewer_id,reviewed_labels_json,answer_id\nFalse,,[],A1\n')
            with self.assertRaisesRegex(ValueError,'adjudication is incomplete'):load_reviewed(p,['Oxygen concentrator'])

    def test_frequency_denominators_and_rank_are_explicit(self):
        p=ROOT/'outputs/drc2_failure_audit/audited_device_mentions.csv'
        with p.open() as f: rows=list(csv.DictReader(f))
        self.assertEqual(rows[0]['category'],'Oxygen concentrator');self.assertEqual(rows[0]['facilities_mentioning'],'65')
        for r in rows:
            self.assertEqual(r['all_facilities_denominator'],'491')
            self.assertLessEqual(int(r['facilities_mentioning_and_reporting_damage']),int(r['damage_reporting_facilities_denominator']))

if __name__=='__main__':unittest.main()
