"""V1.2 auditable rule-based validation; no external model or network calls.

Business heuristics are never promoted to a confirmed violation without
explicit policy evidence. Each PO/PR is evaluated independently.
"""
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from extraction import identify_refs

RULES = [
('R01','Supported FPC and one-FPC-per-line'),('R02','Quote amount and currency'),
('R03','Quotation validity'),('R04','Gold Order corroboration'),
('R05','OTC/MRC and milestone structure'),('R06','Entity local-to-local'),
('R07','MC/CDR and margins'),('R08','Product classification consistency'),
('R09','GL account / Capex-Opex'),('R10','Approvals and exceptions')]
ALLOWED={'S79','S77','F35','F19','S60','S12','S13','S14','S17','S18','F98'}


def money(v):
    v=str(v).replace(' ','').replace('\u00a0','')
    if ',' in v and '.' in v:
        v=v.replace(',','') if v.rfind('.')>v.rfind(',') else v.replace('.','').replace(',','.')
    elif ',' in v:
        v=v.replace(',','.') if len(v.split(',')[-1])==2 else v.replace(',','')
    try:return Decimal(v)
    except InvalidOperation:return None


def extract_amounts(text):
    found=[]
    pats=[
      r'\b(?:Grand\s+Total|TOTAL\s*:|Requisition Amount|Approval Amount)\s*:?\s*(?:(EUR|GBP|USD)\s*)?([\d][\d ,.]*?)\s*(EUR|GBP|USD)?(?=\s*(?:\n|\||\[Page|$))',
      r'\b(?:TOTAL|Grand Total)\s*:?\s*(EUR|GBP|USD)\s+([\d][\d ,.]*)'
    ]
    for p in pats:
        for m in re.finditer(p,text,re.I):
            if len(m.groups())==3: raw,c=m.group(2),m.group(1) or m.group(3)
            else: c,raw=m.group(1),m.group(2)
            v=money(raw.strip());c=(c or '').upper()
            if v is not None and c:found.append((v,c,m.group(0)))
    if not found:
        m=re.search(r'\bTOTAL\s+([\d][\d ,.]*\d)',text,re.I)
        currency='EUR' if re.search(r'expressed in Euro|\bEUR\b',text,re.I) else ('GBP' if re.search(r'\bGBP\b',text,re.I) else '')
        if m and currency:
            v=money(m.group(1).strip())
            if v is not None: found.append((v,currency,m.group(0)))
    return list(dict.fromkeys(found))


def dates(text):
    vals=[]
    patterns=[('quote_expiry',r'Expires On\s*:?\s*(\d{1,2}/\d{1,2}/\d{4})'),
      ('tc_expiry',r'(?:proposal is valid until|valid until)\s*(\d{1,2}/\d{1,2}/\d{4})'),
      ('po_date',r'Order Date[\s\S]{0,110}?(\d{1,2}-[A-Za-z]{3}-\d{2,4})')]
    for label,pat in patterns:
        m=re.search(pat,text,re.I)
        if m:
            for fmt in ('%d/%m/%Y','%d-%b-%y','%d-%b-%Y'):
                try: vals.append((label,datetime.strptime(m.group(1),fmt).date()));break
                except ValueError:pass
    return dict(vals)


def finding(rule,status,reason,evidence='',source='',severity='medium'):
    return dict(rule=rule,status=status,reason=reason,evidence=evidence,source=source,severity=severity)


def fpc(text):
    return list(dict.fromkeys(re.findall(r'\bFPC\s*[:\s]+(S\d{2}|F\d{2})\b',text,re.I)))


def page_ref(doc, term):
    for p in doc.get('pages',[]):
        if term.lower() in p.get('text','').lower(): return f"{doc['name']} — page {p['page']}"
    return doc['name']


def from_quote_amount(q):
    amounts=extract_amounts(q['text'])
    # Prefer explicit Grand Total rather than section totals
    explicit=[x for x in amounts if re.search(r'grand\s+total',x[2],re.I)]
    return (explicit or amounts)[:1]


def validate(docs,guideline,llm_findings=None):
    orders=[d for d in docs if d['kind'] in ('purchase_order','requisition')]
    quotes=[d for d in docs if d['kind']=='quotation']
    gold=[d for d in docs if d['kind']=='gold_order']
    results=[]
    for d in orders:
        refs=identify_refs(d['text']); qids=refs['quote']
        matches=[q for q in quotes if any(x.lower() in q['text'].lower() for x in qids)]
        q=matches[0] if len(matches)==1 else None
        key=(refs['po'] or refs['requisition'] or [d['name']])[0]
        tt=d['text']; qt=q['text'] if q else ''
        codes=fpc(tt)
        f=[]
        def add(rule,status,reason,evidence='',source=None,severity='medium'):
            f.append(finding(rule,status,reason,evidence,source or d['name'],severity))
        # FPC: distinguish printed codes from actual line-level proof.
        if not codes:
            add('R01','NOT VERIFIED','FPC was not extractable from PO/PR; verify the product code and line allocations.','',severity='high')
        elif any(x.upper() not in ALLOWED for x in codes):
            add('R01','FAIL','An FPC falls outside the standard guideline product list; route to the designated owner.','FPC: '+', '.join(codes),severity='high')
        else:
            add('R01','PASS' if len(codes)==1 else 'REVIEW',
                'Declared FPC is in the guideline list; quotation-to-FPC composition is assessed separately.' if len(codes)==1 else 'Multiple FPCs appear; verify each has its own PO/PR line.',
                'Declared FPC(s): '+', '.join(codes))
        # Totals, expiration.
        if not q:
            add('R02','NOT VERIFIED','Matching quotation cannot be identified; upload the quotation referenced in the PO/PR.',', '.join(qids),severity='high')
            add('R03','NOT VERIFIED','Quotation not available for validity check.','',severity='high')
        else:
            oa=extract_amounts(tt);qa=from_quote_amount(q)
            if oa and qa:
                matched=any(a==b and ca==cb for a,ca,_ in oa for b,cb,_ in qa)
                add('R02','PASS' if matched else 'FAIL',
                    'PO/PR amount and currency match the quotation.' if matched else 'PO/PR and quotation amount/currency mismatch; verify source totals.',
                    'PO/PR: '+', '.join(f'{c} {v}' for v,c,_ in oa[:3])+'; quotation: '+', '.join(f'{c} {v}' for v,c,_ in qa),d['name']+' / '+q['name'],'high')
            else:add('R02','NOT VERIFIED','Could not reliably identify both document totals.',source=q['name'],severity='high')
            dd=dates(tt);qd=dates(qt)
            if 'quote_expiry' in qd and 'tc_expiry' in qd and qd['quote_expiry']!=qd['tc_expiry']:
                add('R03','FAIL','Quotation contains conflicting expiration dates; obtain written clarification before approval.',
                    f"Header {qd['quote_expiry']} vs T&C {qd['tc_expiry']}",q['name'],'high')
            elif 'po_date' in dd and ('quote_expiry' in qd or 'tc_expiry' in qd):
                expiry=qd.get('quote_expiry',qd.get('tc_expiry'));expired=dd['po_date']>expiry
                add('R03','FAIL' if expired else 'PASS',
                    'PO was issued after the quotation expired; extension evidence required.' if expired else 'PO date is within quotation validity.',
                    f"PO {dd['po_date']}; expires {expiry}",d['name']+' / '+q['name'],'high')
            else:add('R03','NOT VERIFIED','PO date or quotation expiration missing; cannot establish validity.',str(dd)+' / '+str(qd),severity='high')
        # Gold order evidence: attachment list is not uploaded evidence.
        goldrefs=refs['gold']
        found=[x for x in gold if any(z.replace(' ','') in x['text'].replace(' ','') for z in goldrefs)]
        if found:
            add('R04','REVIEW','Gold Order evidence is uploaded. Verify values, FPC and OTC/MRC schedule against PO/PR.',
                ', '.join(goldrefs),', '.join(x['name'] for x in found),'high')
        else:
            note='A supporting image is listed in the PR, but its contents were not uploaded for verification.' if re.search(r'Attachments[\s\S]{0,400}\.png',tt,re.I) else 'Gold Order reference alone does not establish matching figures or billing structure.'
            add('R04','NOT VERIFIED','Gold Order screenshot/data was not available for verification. '+note,
                ', '.join(goldrefs),severity='high')
        # OTC and recurring: cues suggest possible issues, not confirmed billing violations.
        has_otc=bool(re.search(r'\bOTC\b|One[- ]Off',tt,re.I))
        commercial_scope=re.split(r'\bTerms\s*&\s*Conditions\b',qt,flags=re.I)[0]
        recurring=bool(re.search(r'Managed Firewall|Change hours per month|OCD Managed Services|\bMRC\b',commercial_scope,re.I))
        milestone=bool(re.search(r'90% of each subtask|remaining 10%|at completion of the subtask',qt,re.I))
        if not q:
            add('R05','NOT VERIFIED','Quotation missing; OTC/MRC and delivery milestones cannot be assessed.')
        elif has_otc and recurring:
            add('R05','REVIEW','PO/PR declares OTC while the quotation includes managed-service or monthly-change items. Confirm the actual billing schedule and Gold configuration before approval.',
                'OTC in PO/PR; managed-service/monthly wording in quotation',page_ref(q,'Managed Firewall'),'high')
        elif has_otc and milestone:
            add('R05','REVIEW','Quotation defines staged invoicing (90% at subtask completion and 10% at full completion); verify that the single OTC line is consistent with the approved delivery and billing schedule.',
                '90% / 10% staged invoicing',page_ref(q,'90%'),'medium')
        elif has_otc:
            add('R05','REVIEW','PO/PR is designated OTC. Billing-period alignment cannot be confirmed without full Gold Order data.',
                'OTC stated in PO/PR')
        else:add('R05','NOT VERIFIED','Could not confirm OTC/MRC invoicing structure from the available documents.')
        # Entities: local-country check is possible, but legal-name verification needs evidence.
        countries=['BELGIUM','UNITED KINGDOM','NETHERLANDS','SWITZERLAND','PORTUGAL']
        names=[c for c in countries if c in tt.upper()]
        supplier_country='UNITED KINGDOM' if re.search(r'ORANGE CYBERDEFENSE UK',tt,re.I) else ('BELGIUM' if (re.search(r'ORANGE CYBERDEFENSE[\s\S]{0,100}?(?:BELGIUM|BELIGUM)\s*NV',tt,re.I) or re.search(r'ORANGE BUSINESS BELGIUM',tt,re.I) and re.search(r'ORANGE CYBERDEFENSE',tt,re.I)) else '')
        buyer_country='UNITED KINGDOM' if re.search(r'\bBU\s+0872|Requisitioning BU\s+0872',tt,re.I) else ('BELGIUM' if re.search(r'ORANGE BUSINESS BELGIUM',tt,re.I) else '')
        if supplier_country and buyer_country and supplier_country==buyer_country:
            add('R06','PASS','Buyer and supplier country are consistent with the local-to-local principle; validate legal name if necessary.',
                f'Buyer {buyer_country}; supplier {supplier_country}')
        else:add('R06','NOT VERIFIED','Unable to confirm both legal entities and local-to-local compliance.',
                 f'Buyer {buyer_country or "unknown"}; supplier {supplier_country or "unknown"}')
        # management code evidence is distinct from proving correct margin.
        mc=re.search(r'\b(DPS\d{2}|SC21[A-S])\b',tt,re.I)
        if mc:
            add('R07','REVIEW','Management code extracted, but appropriate routing and 0% revenue-transfer margin require separate supporting evidence.',
                'Management code: '+mc.group(1))
        else:add('R07','NOT VERIFIED','MC/CDR and margin are not demonstrated in the uploaded order; verify the accounting distribution / Gold setup.')
        # Product classification: configurable heuristics identify potential mismatches.
        if q and re.search(r'\bF35\b', ' '.join(codes),re.I) and re.search(r'PS-UK-PMG-|Project Manager \(PM\)',qt,re.I) and re.search(r'Tech-based Consulting',qt,re.I):
            add('R08','REVIEW','Quotation combines project management and technical consulting under a single declared F35 line. A proposed PM→F19 / consulting→F35 mapping must be confirmed by the product owner before requiring an FPC split.',
                'UK PM and TBC service line items',page_ref(q,'PS-UK-PMG-'),'high')
        elif q and 'S79' in [c.upper() for c in codes] and re.search(r'Setting up privileges|Service Take Over|Integration with|knowledge transfer|onboarding',qt,re.I) and not recurring:
            add('R08','REVIEW','Quotation describes one-time setup/integration without a clearly identified ongoing service. Confirm S79 eligibility versus other service FPCs; customer-end billing evidence is needed.',
                'Setup / integration / takeover services',page_ref(q,'Service Take Over'),'high')
        elif q and 'S79' in [c.upper() for c in codes] and recurring:
            add('R08','REVIEW','Quotation includes managed and professional-service components. Confirm product/FPC allocation per line and end-customer billing treatment.',
                'Professional and managed services in quotation',page_ref(q,'Managed Firewall'))
        else:add('R08','NOT VERIFIED','No reliable product-to-FPC mapping is demonstrated; validate against an approved product catalogue or commercial mapping.')
        # GL / exceptions.
        gl=re.search(r'\b\d{4}-(\d{8})-',tt)
        if gl:
            add('R09','REVIEW','GL account extracted; confirm capitalization eligibility and purchasing category with Finance.',
                'GL account: '+gl.group(1))
        else:add('R09','NOT VERIFIED','GL account and Capex/Opex classification are not available in the order evidence.')
        add('R10','NOT VERIFIED','Any required exceptional approval or authorized deviation must be checked; no approval evidence was established from the supplied files.')
        decision='REJECT' if any(x['status']=='FAIL' for x in f) else ('PENDING REVIEW' if any(x['status']!='PASS' for x in f) else 'APPROVE')
        results.append(dict(id=key,decision=decision,findings=f,quote=q['name'] if q else None,source=d['name']))
    return results
