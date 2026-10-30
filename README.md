# PO Validation Agent — V1

Decision-first Streamlit and LangGraph app, using a user-confirmed purchasing guideline. Accepts any number of PDFs, DOCX, text, CSV, XLSX, JPG/PNG files and matches POs/PRs to quotations by reference.

## Deploy
1. Create a **private** GitHub repository; commit the files in this folder.
2. In Streamlit Community Cloud, point to `app.py` and deploy. (For internal restricted files, prefer an approved company-controlled deployment.)
3. In the UI upload the case documents, confirm whether August 2026 is still current or upload a new guideline, and choose deterministic mode or API-based AI contextual review.
4. Select Validate → executive decisions appear → download full Word report.

## Security
Documents are processed in memory by the app. Optional AI transmits extracted document text to the OpenAI API **only if explicitly enabled**. Do not send Orange Restricted materials to third-party hosted services without organization approval. Streamlit Community Cloud and external API configurations must be approved by your security/privacy team. Avoid committing sample customer files to public GitHub. The bundled guideline is itself marked Orange Restricted: keep the entire repository private and use only approved hosting.

## Decision policy
- **REJECT**: at least one evidence-backed FAIL.
- **PENDING REVIEW**: no FAIL, but REVIEW or NOT VERIFIED remains.
- **APPROVE**: every required check explicitly PASS. This is an advisory recommendation, not an ERP action.

Note: The deterministic V1 does **not** approve merely because amounts match. The optional AI interprets category/FPC/OTC/MRC guidelines and proposes evidence-backed findings. For production, validate AI outputs against real document spans, formalize FPC mapping, implement image/PDF vision extraction, guideline effective-date governance, user authentication, and test all scenarios. Never assume blank screenshots are compliant.

### Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
