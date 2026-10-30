import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from summary import rationale, actions, message_to_requester
from validation import validate

def doc(name,kind,text):return {'name':name,'kind':kind,'text':text,'pages':[{'page':1,'text':text}]}
class SummaryTests(unittest.TestCase):
 def test_no_generic_r10_blocker(self):
  a=doc('po.pdf','purchase_order','Purchase Order Number 9999999/GBF\nOrder Date 16-JUN-26\nFPC S79\nOTC EUR 250.00\nQuote Reference: Q-99999-1\nTOTAL 250.00\nAll prices expressed in Euro')
  b=doc('quote.pdf','quotation','Quote Number: Q-99999-1\nExpires On: 8/05/2026\nGrand Total: EUR 250.00')
  r=validate([a,b],{})[0]
  self.assertEqual(next(f for f in r['findings'] if f['rule']=='R10')['status'],'NOT APPLICABLE')
  self.assertIn('expired',rationale(r))
  self.assertIn('Subject:',message_to_requester(r))
  self.assertTrue(actions(r))
if __name__=='__main__':unittest.main()
