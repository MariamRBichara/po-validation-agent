import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from compliance import matrix, coverage

class ComplianceTests(unittest.TestCase):
 def test_partial_rule_pass_does_not_pretend_all_subrequirements_pass(self):
  r={'findings':[{'rule':'R01','status':'PASS','reason':'In allowed list','source':'order.pdf'}]}
  rows=matrix(r)
  self.assertEqual(next(x for x in rows if x['check']=='G01')['status'],'PASS')
  self.assertEqual(next(x for x in rows if x['check']=='G00')['status'],'NOT VERIFIED')
  self.assertEqual(next(x for x in rows if x['check']=='G08')['status'],'NOT VERIFIED')
 def test_new_guideline_demands_remapping(self):
  r={'findings':[{'rule':'R03','status':'PASS','reason':'Date passes'}]}
  self.assertEqual(next(x for x in matrix(r,'guideline_2027.docx') if x['check']=='G17')['status'],'NOT VERIFIED')
 def test_coverage(self):
  self.assertEqual(coverage(matrix({'findings':[]}))['total'],18)
if __name__=='__main__': unittest.main()
