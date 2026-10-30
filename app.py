"""Streamlit UI for rule-based PO/PR validation. No external AI integration."""
from pathlib import Path
import streamlit as st
from extraction import extract_document, EXTS
from workflow import run
from report import build_report

st.set_page_config(page_title='PO Validation Agent', page_icon='📋', layout='wide')
st.title('PO Validation & Compliance Agent')
st.caption('Rule-based validation; no OpenAI API key or AI service required. Decisions are recommendations only.')

with st.expander('1. Upload evidence', expanded=True):
    uploaded = st.file_uploader(
        'Upload PO/PR, quotations, Gold Orders, and supporting documents',
        type=[ext[1:] for ext in sorted(EXTS)], accept_multiple_files=True,
    )
    st.caption('Upload as many files as needed. Scanned PDFs and images are not fully readable without OCR; unresolved checks remain pending.')

with st.expander('2. Confirm the governing guideline', expanded=True):
    st.info('Default: PO/PR approval guideline — August 2026. Confirm that it remains applicable or upload a newer version.')
    choice = st.radio('Applicable guideline', ['August 2026 — confirm as current', 'Upload newer guideline'], horizontal=True)
    replacement = st.file_uploader('Replacement guideline (when applicable)', type=['docx', 'pdf', 'txt'], key='guideline') if choice == 'Upload newer guideline' else None
    confirmed = st.checkbox('I confirm the selected guideline is applicable to these purchase orders')
    if choice == 'Upload newer guideline' and replacement is None:
        st.warning('Upload the newer guideline to proceed.')

ready = bool(uploaded) and confirmed and (choice != 'Upload newer guideline' or replacement is not None)
if st.button('Validate purchase orders', type='primary', disabled=not ready):
    st.session_state.pop('assessment', None)
    try:
        if replacement is not None:
            guideline = extract_document(replacement.name, replacement.getvalue())
        else:
            path = Path(__file__).with_name('guideline_aug_2026.docx')
            guideline = extract_document(path.name, path.read_bytes())
        files = [(item.name, item.getvalue()) for item in uploaded]
        with st.spinner('Extracting, matching, and checking the evidence...'):
            result = run(files, guideline)
        st.session_state['assessment'] = (result, guideline)
    except Exception as exc:
        st.error(f'Validation could not be completed: {exc}')

if 'assessment' in st.session_state:
    result, guideline = st.session_state['assessment']
    results = result['results']
    if not results:
        st.error('No recognizable purchase order or requisition was found. Check the document type or extraction quality.')
    else:
        st.subheader('Executive decision summary')
        for record in results:
            color = {'APPROVE': 'green', 'REJECT': 'red', 'PENDING REVIEW': 'orange'}[record['decision']]
            st.markdown(f"### :{color}[{record['decision']}] — {record['id']}")
            failures = [item for item in record['findings'] if item['status'] == 'FAIL']
            unresolved = [item for item in record['findings'] if item['status'] in ('REVIEW', 'NOT VERIFIED')]
            st.write(f"**Confirmed failures:** {len(failures)} · **Unresolved checks:** {len(unresolved)} · **Guideline:** {guideline['name']}")
            for item in (failures + unresolved)[:5]:
                st.write(f"**{item['rule']} · {item['status']}** — {item['reason']}")
            with st.expander('All validation checks'):
                st.dataframe(
                    [{field: item.get(field, '') for field in ('rule', 'status', 'reason', 'source', 'evidence')} for item in record['findings']],
                    hide_index=True, use_container_width=True,
                )
        st.download_button(
            'Download full analysis (Word)',
            data=build_report(results, guideline, [item['name'] for item in result['docs']]),
            file_name='PO_Validation_Full_Analysis.docx',
            mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            type='primary',
        )
        st.caption('No AI model is used. Checks that require interpretation, unavailable screenshots or missing evidence remain NOT VERIFIED / PENDING REVIEW.')
