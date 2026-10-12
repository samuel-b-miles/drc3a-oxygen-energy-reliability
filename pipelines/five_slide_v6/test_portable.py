import copy, unittest
from portable import validate, synthetic_bundle, ecdf, device_rate
class Contracts(unittest.TestCase):
    def test_synthetic_is_valid(self):validate(synthetic_bundle())
    def test_missing_uptime_excluded_zero_capacity_retained(self):
        b=synthetic_bundle()['distribution'];self.assertEqual(ecdf([r['uptime_pct'] for r in b]),([20,80],[.5,1.]));self.assertEqual(ecdf([r['capacity_lpm'] for r in b]),([0,0,10],[1/3,2/3,1.]))
    def test_duplicate_time_rejected(self):
        b=synthetic_bundle();b['voltage'].append(copy.deepcopy(b['voltage'][0]));self.assertRaises(ValueError,validate,b)
    def test_null_voltage_remains_null(self):
        b=synthetic_bundle();validate(b);self.assertIsNone(b['voltage'][1]['volts'])
    def test_impossible_damage_rejected(self):
        b=synthetic_bundle();b['damage'][0]['exposed_yes']=11;self.assertRaises(ValueError,validate,b)
    def test_missing_cadence_slot_rejected(self):
        b=synthetic_bundle();b['voltage'].pop(1);self.assertRaises(ValueError,validate,b)
    def test_zero_bed_rate_is_undefined(self):self.assertIsNone(device_rate(0,0));self.assertEqual(device_rate(2,20),10)
    def test_unresolved_zero_beds_rejected(self):
        b=synthetic_bundle();b['devices'][1]['concentrators']=1;self.assertRaises(ValueError,validate,b)
if __name__=='__main__':unittest.main()
