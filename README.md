# PO Validation Agent V1.2 — no API key

Streamlit + LangGraph workflow with deterministic, evidence-based PO/PR assessment.

## Update existing GitHub application
Replace **validation.py**, **app.py**, **report.py**, and **tests/test_validation.py** with files from the update ZIP. You can also replace README.md. Keep your existing **workflow.py**, **extraction.py**, **requirements.txt**, and **guideline_aug_2026.docx** unchanged. Do not commit `__pycache__/` or sensitive sample POs.

## Results
Run a variable bundle of PDF, DOCX, XLSX, TXT, CSV and image files. Image-only text is **not interpreted** by this version, so supporting screenshots require further development. Decisions per recognized PO/PR: REJECT if a verified FAIL; otherwise PENDING REVIEW when any check is not PASS; otherwise APPROVE. The decision is a recommendation, not an ERP workflow action.

Checks include FPC in guideline list, value and currency, quotation validity (including contradictory dates), uploaded Gold evidence presence, OTC/MRC and milestone cues, local country consistency, management code, potential product classification mismatches, GL account, and exceptions. Contextual signals are REVIEW rather than hard failures unless source evidence/policy establish a direct conflict.

**Policy caveat:** The allowed-FPC list and rule logic are coded from the supplied August 2026 guideline. Uploading a replacement guideline changes the displayed governing document, but does **not automatically rewrite the deterministic rules**. A revised policy requires a validated rule update; do not rely on automatic policy adaptation.

## Test
`python -m unittest discover -s tests -v`

## Security
Source files carry an Orange Restricted classification. Use only environments approved for your company's information handling. No OpenAI or third-party AI API is invoked by this code; Streamlit Cloud remains third-party hosting. API secrets should not be committed to GitHub.
