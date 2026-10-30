"""Traceability matrix for August 2026 policy. Not a policy interpretation engine.

A matrix row can be verified only as far as its underlying rule finding supports.
Where a rule contains more than one requirement, unimplemented subchecks remain
NOT VERIFIED rather than being automatically labeled PASS.
"""
from collections import Counter

CHECKS = [
 ('G00','Prerequisite','FPC is supported and separate on each order line','R01',False),
 ('G01','1 / Product','Declared FPC belongs to the permitted list','R01',True),
 ('G02','2a / Value','PO/PR total amount and currency match the quotation','R02',True),
 ('G03','2b / Global orders','Multi-Gold list and sum, when applicable','R04',False),
 ('G04','3a–d / Financial setup','OTC/MRC and invoice period or milestones','R05',False),
 ('G05','3e / Gold','Gold amount, FPC and OTC/MRC against evidence','R04',False),
 ('G06','3f / Zero-value Gold','Zero-value Gold supporting screenshots / pre-approval','R04',False),
 ('G07','4 / Entities','OB and OCD local-to-local and legal supplier identity','R06',False),
 ('G08','5 / MC-CDR','Approved MC/CDR routing by region, entity and FPC','R07',False),
 ('G09','6 / Margin','0% revenue-transfer margin, or documented exception','R07',False),
 ('G10','7 / Product consistency','Service, hardware, software and FPC consistency','R08',False),
 ('G11','8 / Morocco','Special Morocco handling and authorizations if applicable','R10',False),
 ('G12','A / S27','S27 supplier and DPS09 requirements if applicable','R10',False),
 ('G13','B / S25 S16 S01 S89','Non-standard product / purchase process if applicable','R10',False),
 ('G14','C / Legacy OB','Legacy PO-on-behalf specific sourcing requirements if applicable','R10',False),
 ('G15','Account classification','GL account and Capex/Opex treatment','R09',False),
 ('G16','Purchasing category','Purchasing category matches the purchase','R09',False),
 ('G17','Quote validity','PO issuance date and quotation validity are compatible','R03',True),
]


def matrix(record, guideline_name='guideline_aug_2026.docx'):
    by_rule = {item['rule']:item for item in record.get('findings',[])}
    updated_guideline = guideline_name.lower() != 'guideline_aug_2026.docx'
    rows=[]
    for cid,section,requirement,rule,fully_automated in CHECKS:
        f=by_rule.get(rule,{})
        underlying=f.get('status','NOT VERIFIED')
        if updated_guideline:
            status='NOT VERIFIED'
            note='Replacement guideline uploaded: current checks are mapped only to the August 2026 guideline. Human rule reconciliation required.'
        elif fully_automated:
            status=underlying
            note=f.get('reason','Not evaluated')
        elif underlying=='FAIL':
            # A broader check failure does not prove which sub-requirement failed.
            status='REVIEW'
            note='Related rule has a failure; review evidence to establish this specific sub-requirement. '+f.get('reason','')
        elif underlying=='NOT APPLICABLE' and cid in ('G11','G12','G13','G14'):
            status='NOT VERIFIED'
            note='Applicability is not established by the available evidence; do not assume an exception is unnecessary.'
        else:
            status='NOT VERIFIED' if underlying=='PASS' else underlying
            note=('Related automated check passed, but this distinct requirement was not independently checked. ' if underlying=='PASS' else '')+f.get('reason','Evidence missing or check not implemented')
        rows.append(dict(check=cid,guideline_section=section,requirement=requirement,status=status,
                         linked_rule=rule,reason=note,source=f.get('source',''),evidence=f.get('evidence','')))
    return rows


def coverage(rows):
    counts=Counter(r['status'] for r in rows)
    return {'total':len(rows),'verified_pass':counts['PASS'],'failed':counts['FAIL'],
            'review':counts['REVIEW'],'not_verified':counts['NOT VERIFIED'],'not_applicable':counts['NOT APPLICABLE']}
