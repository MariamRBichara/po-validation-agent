"""Run with: python -m unittest discover -s tests -v
Uses synthetic records so restricted source documents are not committed.
"""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from validation import validate

def doc(name,kind,text):
    return {'name':name,'kind':kind,'text':text,'pages':[{'page':1,'text':text}]}

class ValidationTests(unittest.TestCase):
    def test_expiry_rejection(self):
        a=doc('order.pdf','purchase_order','Purchase Order Number 9999999/GBF\nOrder Date 16-JUN-26\nFPC S79\nOTC EUR 250.00\nQuote Reference: Q-99999-1\nTOTAL 250.00\nAll prices expressed in Euro')
        b=doc('quote.pdf','quotation','Quote Number: Q-99999-1\nExpires On: 8/05/2026\nGrand Total: EUR 250.00')
        r=validate([a,b],{})[0]
        self.assertEqual(r['decision'],'REJECT')
        self.assertEqual(next(x for x in r['findings'] if x['rule']=='R03')['status'],'FAIL')
        self.assertEqual(next(x for x in r['findings'] if x['rule']=='R02')['status'],'PASS')
    def test_disputed_validity_and_consulting(self):
        a=doc('req.pdf','requisition','Requisitioning BU 0872_01\nRequisition Amount 100 GBP\nFPC F35\nOTC GBP 100\nQ-99999-1\nORANGE CYBERDEFENSE UK LTD')
        b=doc('quote.pdf','quotation','Quote Number Q-99999-1\nExpires On: 30/09/2026\nPS-UK-PMG-SENSTD Project Manager (PM)\nTech-based Consulting\nGrand Total: GBP 100\nTerms & Conditions\nThis proposal is valid until 26/08/2026')
        r=validate([a,b],{})[0]
        self.assertEqual(r['decision'],'REJECT')
        self.assertEqual(next(x for x in r['findings'] if x['rule']=='R08')['status'],'REVIEW')
    def test_terms_boilerplate_not_recurring_evidence(self):
        a=doc('order.pdf','purchase_order','FPC S79\nOTC EUR 100\nQ-99999-1')
        b=doc('quote.pdf','quotation','Quote Number Q-99999-1\nSetting up privileges\nGrand Total: EUR 100\nTerms & Conditions\nManaged Services start as specified')
        r=validate([a,b],{})[0]
        self.assertIn('staged invoicing' if False else 'Billing-period',next(x for x in r['findings'] if x['rule']=='R05')['reason'])
        self.assertEqual(next(x for x in r['findings'] if x['rule']=='R08')['status'],'REVIEW')

if __name__=='__main__':unittest.main()
