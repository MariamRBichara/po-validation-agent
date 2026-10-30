"""Conservative, auditable checks. Unknowns must never turn into 'pass'."""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from extraction import identify_refs

RULES = [
('R01','Supported FPC and one-FPC-per-line'),('R02','Quote amount and currency'),
('R03','Quotation validity'),('R04','Gold Order corroboration'),
('R05','OTC/MRC structure'),('R06','Entity local-to-local'),
('R07','MC/CDR and margins'),('R08','Product category consistency'),
('R09','GL account / Capex-Opex'),('R10','Approvals and exceptions')]

def money(v):
    v=v.replace(' ','').replace('\u00a0','')
    if ',' in v and '.' in v:
        v=v.replace(',','') if v.rfind('.')>v.rfind(',') else v.replace('.','').replace(',','.')
    elif ',' in v:
        v=v.replace(',','.') if len(v.split(',')[-1])==2 else v.replace(',','')
    try:return Decimal(v)
    except InvalidOperation:return None

def extract_amounts(text):
    patterns=[r'(?:Grand\s+Total|TOTAL\s*:|Requisition Amount|Approval Amount)\s*:?\s*(?:(EUR|GBP|USD)\s*)?([\d][\d ,.]*)\s*(EUR|GBP|USD)?',
              r'(?:EUR|GBP|USD)\s+[\d][\d ,.]*(?=\s*(?:\n|$))']
    found=[]
    for m in re.finditer(patterns[0],text,re.I):
        val=money(m.group(2).strip()); c=(m.group(1) or m.group(3) or '').upper()
        if val is not None and c:found.append((val,c,m.group(0)))
    # Purchase orders from Oracle frequently show the final total without currency on the line.
    if not found:
        m=re.search(r'\bTOTAL\s+([\d][\d ,.]*)',text,re.I)
        currency='EUR' if re.search(r'(?:expressed in Euro|\bEUR\b)',text,re.I) else ('GBP' if re.search(r'\bGBP\b',text,re.I) else '')
        if m and currency:
            v=money(m.group(1).strip())
            if v is not None:found.append((v,currency,m.group(0)))
    return found

def dates(text):
    vals=[]
    for label,pat in [('quote_expiry',r'Expires On\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})'),
                      ('tc_expiry',r'(?:proposal is valid until|valid until)\s*(\d{1,2}/\d{1,2}/\d{4})'),
                      ('po_date',r'Order Date[\s\S]{0,100}?(\d{1,2}-[A-Za-z]{3}-\d{2,4})')]:
        m=re.search(pat,text,re.I)
        if m:
            for fmt in ('%d/%m/%Y','%d-%b-%y','%d-%b-%Y'):
                try:vals.append((label,datetime.strptime(m.group(1),fmt).date()));break
                except ValueError:pass
    return dict(vals)

def finding(rule,status,reason,evidence='',source='',severity='medium'):
    return dict(rule=rule,status=status,reason=reason,evidence=evidence,source=source,severity=severity)

def validate(docs, guideline, llm_findings=None):
    """One group decision per linked PO/PR; deterministic checks always precede AI suggestions."""
    orders=[d for d in docs if d['kind'] in ('purchase_order','requisition')]
    quotes=[d for d in docs if d['kind']=='quotation']
    gold=[d for d in docs if d['kind']=='gold_order']
    results=[]
    for d in orders:
        refs=identify_refs(d['text']); qids=refs['quote'];
        match=[q for q in quotes if any(x.lower() in q['text'].lower() for x in qids)]
        q=match[0] if len(match)==1 else None
        key=(refs['po'] or refs['requisition'] or [d['name']])[0]
        f=[]
        if q is None:
            f.append(finding('R02','NOT VERIFIED','Matching quotation is not identifiable from the uploaded evidence.',', '.join(qids),d['name'],'high'))
        else:
            oa=extract_amounts(d['text']);qa=extract_amounts(q['text']);
            equivalent=any(a==b and ca==cb for a,ca,_ in oa for b,cb,_ in qa)
            if oa and qa:
                f.append(finding('R02','PASS' if equivalent else 'FAIL', 'PO/PR total matches quote total.' if equivalent else 'PO/PR and quotation totals/currencies do not match; verify extracted values.','PO/PR: '+', '.join(f'{a} {c}' for a,c,_ in oa[:3])+'; Quote: '+', '.join(f'{a} {c}' for a,c,_ in qa[:3]),d['name']+' / '+q['name'],'high'))
            else:f.append(finding('R02','NOT VERIFIED','Could not reliably extract totals for both documents.','',d['name']+' / '+q['name'],'high'))
            dd=dates(d['text']);qd=dates(q['text']);ex=[x for x in ('quote_expiry','tc_expiry') if x in qd]
            if len(ex)>1 and qd[ex[0]] != qd[ex[1]]:
                f.append(finding('R03','FAIL','Quotation contains conflicting expiration dates. Written clarification required.',str(qd),q['name'],'high'))
            elif 'po_date' in dd and ex:
                expired=dd['po_date']>qd[ex[0]]
                f.append(finding('R03','FAIL' if expired else 'PASS','PO date is after quotation expiry.' if expired else 'PO date is within quotation validity.',str(dd)+' / '+str(qd),d['name']+' / '+q['name'],'high'))
            else:f.append(finding('R03','NOT VERIFIED','Missing PO date or valid-until date; cannot establish quote validity.',str(dd)+' / '+str(qd),d['name']+' / '+q['name'],'high'))
        goldrefs=refs['gold']; found=[x for x in gold if any(z.replace(' ','') in x['text'].replace(' ','') for z in goldrefs)]
        f.append(finding('R04','NOT VERIFIED' if not found else 'REVIEW','Gold Order screenshot/data absent.' if not found else 'Gold Order file found; amount, FPC and OTC/MRC must be checked.',', '.join(goldrefs),d['name'],'high'))
        for code,label in RULES:
            if code not in {x['rule'] for x in f}:
                f.append(finding(code,'NOT VERIFIED','Needs evidence-based assessment against the confirmed guideline; do not infer compliance from absence of errors.','',d['name']))
        if llm_findings:
            for item in llm_findings.get(key,[]):
                if item.get('rule') in dict(RULES):
                    prev=next((x for x in f if x['rule']==item['rule']),None)
                    if prev and prev['status']=='NOT VERIFIED' and item.get('status') in ('PASS','FAIL','REVIEW'):
                        candidates=[z for z in docs if z['name']==item.get('source','').split(' | ')[0].split(' (page')[0]]
                        snippet=item.get('evidence','').strip()
                        valid=bool(snippet) and any(' '.join(snippet.split()).lower() in ' '.join(z['text'].split()).lower() for z in candidates)
                        if valid:
                            f[f.index(prev)]=finding(item['rule'],item['status'],item.get('reason',''),item['evidence'],item['source'],item.get('severity','medium'))
        decision='REJECT' if any(x['status']=='FAIL' for x in f) else ('PENDING REVIEW' if any(x['status']!='PASS' for x in f) else 'APPROVE')
        results.append(dict(id=key,decision=decision,findings=f,quote=q['name'] if q else None,source=d['name']))
    return results
