import importlib.util, pathlib, unittest
spec=importlib.util.spec_from_file_location('pipeline',pathlib.Path(__file__).resolve().parents[1]/'src/analyze_original_surveys.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
class ConservativeDedup(unittest.TestCase):
 def test_exact_duplicate(self):
  kept,audit=p.deduplicate([(2,[1,'x']),(3,[1,'x',''])]);self.assertEqual(len(kept),1);self.assertEqual(audit[0]['retained_source_row'],2)
 def test_distinct_responses_retained(self):
  self.assertEqual(len(p.deduplicate([(2,[1,'same facility','yes']),(3,[1,'same facility','no'])])[0]),2)
 def test_unicode(self): self.assertEqual(p.norm(' 𝐑𝐞𝐬𝐮𝐬𝐜𝐢𝐭𝐚𝐭𝐢𝐨𝐧 '),'resuscitation')
 def test_missing_not_zero(self):self.assertNotEqual(p.fingerprint([1,'']),p.fingerprint([1,0]))
 def test_composite_not_split(self):
  text='Resuscitation (oxygen concentrators, defibrillators, medical aspirators)'
  self.assertIn('oxygen concentrators, defibrillators',p.norm(text))
if __name__=='__main__':unittest.main()
