import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from extraction import extract_document
from validation import validate
BASE=Path(__file__).resolve().parents[2]
def d(name):return extract_document(name,(BASE/name).read_bytes())
def test_cases():
    e=validate([d('input 1.PDF'),d('input 2.PDF'),d('input 3.pdf'),d('input 4.pdf')],{})
    assert len(e)==2, e
    assert any(r['id']=='2115930/GBF' and r['decision']=='REJECT' for r in e)
    z=validate([d('input 1(1).pdf'),d('input 2(1).pdf')],{})
    assert len(z)==1 and z[0]['decision']=='REJECT',z
if __name__=='__main__':test_cases();print('Tests passed')
