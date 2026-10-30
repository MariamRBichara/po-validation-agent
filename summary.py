"""Decision-first concise presentation: every claim comes from a recorded rule finding."""
from collections import Counter

ACTION_TEXT = {
 'R01':'Correct or confirm the FPC allocation for each PO/PR line.',
 'R02':'Provide a revised quotation/order with reconciled amount and currency.',
 'R03':'Obtain a revised valid quotation or written confirmation of the correct expiry date.',
 'R04':'Upload the relevant Gold Order screenshot(s) showing FPC, amount and OTC/MRC.',
 'R05':'Confirm the billing frequency, invoice milestones and Gold Order schedule.',
 'R06':'Provide legal buyer/supplier entity information for local-to-local verification.',
 'R07':'Supply the MC/CDR distribution and documented margin/financial routing evidence.',
 'R08':'Ask the product owner to confirm the service-to-FPC allocation.',
 'R09':'Provide GL account and purchasing-category evidence; obtain Finance confirmation where needed.',
 'R10':'Attach the documented exception approval or correct the noncompliant routing.',
}

def blockers(record,limit=3):
    findings=record.get('findings',[])
    prioritized=[x for s in ('FAIL','REVIEW','NOT VERIFIED') for x in findings if x['status']==s]
    return prioritized[:limit]

def actions(record):
    output=[]
    for f in record.get('findings',[]):
        if f['status'] not in ('FAIL','REVIEW','NOT VERIFIED'):continue
        text=ACTION_TEXT.get(f['rule'],f['reason'])
        if text not in output: output.append(text)
    return output

def rationale(record):
    selected=blockers(record,3)
    if not selected:return 'No exceptions were identified in the applicable verified checks.'
    return ' '.join(x['reason'] for x in selected)

def message_to_requester(record):
    lines=[f'Subject: {record["id"]} — Purchase order assessment: {record["decision"]}',
           '', 'Hello,','',
           f'Following the review of {record["id"]}, the recommendation is {record["decision"]}.',
           'Please address the following items before approval can be reconsidered:' ,'']
    lines += [f'{i}. {act}' for i,act in enumerate(actions(record),1)]
    lines += ['', 'Please share the updated documentation for reassessment.', '', 'Best regards']
    return '\n'.join(lines)
