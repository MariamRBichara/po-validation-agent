import streamlit as st
from pathlib import Path
from extraction import extract_document,EXTS
from workflow import run
from report import build_report

st.set_page_config(page_title='PO Validation Agent',page_icon='📋',layout='wide')
st.title('PO Validation & Compliance Agent')
st.caption('Upload any number of PO/PR, quotation, Gold Order and supporting files. Decisions are advisory, never posted to an ERP.')
with st.expander('1. Upload evidence',expanded=True):
    uploaded=st.file_uploader('PO/PR evidence — PDF, DOCX, Excel, CSV, TXT and images',type=[e[1:] for e in sorted(EXTS)],accept_multiple_files=True)
    st.caption('Scanned PDFs and images require vision processing (not enabled in deterministic mode). Original documents remain in memory only.')
with st.expander('2. Confirm the governing guideline',expanded=True):
    st.info('Default guideline: PR approval guideline — August 2026. Confirm whether this is still the applicable version or replace it with an updated one.')
    choice=st.radio('Applicable guideline', ['August 2026 — confirm as current','Upload newer guideline'],horizontal=True)
    replacement=st.file_uploader('Guideline document',type=['docx','pdf','txt'],key='guideline')
    confirmed=st.checkbox('I confirm this is the applicable guideline for these POs')
    if choice=='Upload newer guideline' and replacement is None:st.warning('Please upload the newer guideline before running.')
with st.expander('3. Assessment mode',expanded=True):
    use_ai=st.toggle('Use AI for contextual business assessment (explicitly transmits document text to configured OpenAI API)',value=False)
    ai_key=st.text_input('OpenAI API key',type='password',value=st.secrets.get('OPENAI_API_KEY','') if use_ai else '',disabled=not use_ai)
    st.caption('Without AI: key date/value matching and missing-evidence controls run, and unverified policy checks remain pending. With AI: contextual assessments add evidence-backed findings.')

ready=bool(uploaded) and confirmed and (choice=='August 2026 — confirm as current' or bool(replacement)) and (not use_ai or bool(ai_key))
if st.button('Validate purchase orders',type='primary',disabled=not ready):
    try:
        if replacement: guideline=extract_document(replacement.name,replacement.getvalue())
        else: guideline=extract_document('PR approval guideline - August 2026.docx',Path(__file__).with_name('guideline_aug_2026.docx').read_bytes())
        files=[(f.name,f.getvalue()) for f in uploaded]
        if any('guideline' in x[0].lower() for x in files):st.warning('A guideline was included among evidence; the confirmed guideline above remains the controlling policy.')
        with st.spinner('Extracting, matching, and validating evidence...'):
            result=run(files,guideline,ai_key if use_ai else '')
        st.session_state['assessment']=(result,guideline,use_ai)
    except Exception as e:
        st.error(f'Validation could not be completed: {e}')
if 'assessment' in st.session_state:
    result,guide,used_ai=st.session_state['assessment']
    results=result['results']
    if not results:st.error('No recognizable PO or requisition found. Upload a PO/PR or check the input format.')
    else:
        st.subheader('Executive decision summary')
        for r in results:
            color={'APPROVE':'green','REJECT':'red','PENDING REVIEW':'orange'}[r['decision']]
            st.markdown(f"### :{color}[{r['decision']}] — {r['id']}")
            blockers=[x for x in r['findings'] if x['status']=='FAIL']
            pending=[x for x in r['findings'] if x['status'] in ('REVIEW','NOT VERIFIED')]
            st.write(f"**Confirmed failures:** {len(blockers)} · **Unresolved checks:** {len(pending)} · **Guideline:** {guide['name']}")
            for f in (blockers+pending)[:5]:st.write(f"**{f['rule']} · {f['status']}** — {f['reason']}")
            with st.expander('All validation checks'):
                st.dataframe([{k:f.get(k,'') for k in ('rule','status','reason','source','evidence')} for f in r['findings']],hide_index=True,use_container_width=True)
        st.download_button('Download full analysis (Word)',data=build_report(results,guide,[d['name'] for d in result['docs']],used_ai),file_name='PO_Validation_Full_Analysis.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document',type='primary')
