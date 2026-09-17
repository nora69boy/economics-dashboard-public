import sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import macro_core as c
import macro_fetch as fetch

class WtiFallbackTests(unittest.TestCase):
 def test_recent_eia_daily_table_parser(self):
  raw=b'''<table><tr><th>Product by Area</th><th>09/08/26</th><th>09/09/26</th><th>09/10/26</th><th>09/11/26</th><th>09/14/26</th><th>09/15/26</th></tr><tr><td>WTI - Cushing, Oklahoma</td><td>94.21</td><td>97.26</td><td>103.57</td><td>101.27</td><td>102.42</td><td>107.02</td></tr></table>'''
  self.assertEqual(c.parse_wti_recent(raw),{'2026-09-08':94.21,'2026-09-09':97.26,'2026-09-10':103.57,'2026-09-11':101.27,'2026-09-14':102.42,'2026-09-15':107.02})
 def test_recent_parser_rejects_misalignment(self):
  raw=b'<table><tr><th>09/14/26</th><th>09/15/26</th></tr><tr><td>WTI - Cushing, Oklahoma</td><td>102.42</td></tr></table>'
  with self.assertRaises(ValueError):c.parse_wti_recent(raw)
 def test_recent_endpoint_is_allowlisted(self):
  self.assertIn(c.WTI_RECENT,fetch.ENDPOINTS);self.assertEqual(c.WTI_RECENT,'https://www.eia.gov/dnav/pet/PET_PRI_SPT_S1_D.htm')
 def test_fallback_code_requires_prior_validated_history(self):
  source=(ROOT/'scripts/macro_fetch.py').read_text()
  self.assertIn("require(prior is not None and prior['observations'],'WTI fallback requires validated history')",source)
  self.assertIn("merged=dict(prior['observations']);merged.update(parse_wti_recent(raw))",source)
  self.assertIn("ensure_continuity(s,old.get(ident))",source)

if __name__=='__main__':unittest.main()
