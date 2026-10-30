from io import BytesIO
from docx import Document
from docx.shared import Inches,Pt,RGBColor
from summary import rationale, actions, message_to_requester

def build_report(results, guideline, evidence_files):
    doc=Document(); sec=doc.sections[0]; sec.header.paragraphs[0].text='PO VALIDATION  |  Internal decision support'
    doc.add_heading('Purchase Order Validation',0)
    doc.add_paragraph(f'Guideline: {guideline["name"]}  |  Assessment: rule-based (no external AI)')
    doc.add_paragraph('DECISION SUMMARY',style='Heading 1')
    table=doc.add_table(rows=1, cols=3);table.style='Light Shading Accent 1'
    for i,x in enumerate(('PO / PR','Recommendation','Main blockers')):table.rows[0].cells[i].text=x
    for r in results:
        cells=table.add_row().cells;cells[0].text=r['id'];cells[1].text=r['decision'];cells[2].text=rationale(r)[:330]
    for r in results:
        doc.add_heading(f'{r["id"]} — {r["decision"]}',level=1)
        doc.add_paragraph(f'PO/PR source: {r["source"]} | Matched quote: {r["quote"] or "Not found"}')
        doc.add_heading('Executive rationale', level=2)
        doc.add_paragraph(rationale(r))
        t=doc.add_table(rows=1,cols=3);t.style='Table Grid'
        for i,x in enumerate(('Rule','Status','Finding and evidence')):t.rows[0].cells[i].text=x
        for f in r['findings']:
            c=t.add_row().cells;c[0].text=f['rule'];c[1].text=f['status'];c[2].text=f['reason']+'\nEvidence: '+(f['evidence'][:170] or 'Not supplied')+'\nSource: '+(f['source'] or 'Not supplied')
        doc.add_heading('Required actions',level=2)
        for act in actions(r):doc.add_paragraph(act, style='List Bullet')
        doc.add_heading('Suggested response to requester',level=2)
        doc.add_paragraph(message_to_requester(r))
    doc.add_heading('Audit notes',level=1)
    doc.add_paragraph('A PASS means the given check was supported by the available evidence; NOT VERIFIED and REVIEW cannot justify approval; NOT APPLICABLE is excluded from the outstanding-check count. REJECT means at least one documented failure; PENDING REVIEW means no verified failure but one or more checks remain unresolved. Recommendations are not ERP approval actions.')
    doc.add_paragraph('Documents provided: '+', '.join(evidence_files))
    doc.add_paragraph('The guideline version was selected by the user. Confirm current policy ownership and effective version before operational use.')
    for st in doc.styles:
        if st.name=='Normal':st.font.name='Aptos';st.font.size=Pt(9)
    out=BytesIO();doc.save(out);return out.getvalue()
