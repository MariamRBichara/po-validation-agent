# PO Validation Agent — V1.1 (no API key)

A Streamlit + LangGraph app for rule-based PO/PR validation. No OpenAI API integration is present and no API key is required.

## Deploy in Streamlit
1. Replace `app.py`, `workflow.py`, `report.py`, `requirements.txt` and `README.md` in your existing GitHub repository with these versions.
2. Delete `ai.py` from the repository. You do not need to change `extraction.py`, `validation.py` or `tests/test_validation.py`.
3. Keep `guideline_aug_2026.docx` **only** if authorized to store it in that repository/hosting environment. Otherwise use an approved internal environment and supply the guideline there.
4. Streamlit redeploys after the GitHub changes; if needed select **Reboot app** under the app's Manage controls.
5. Upload your evidence files, confirm the guideline, click **Validate purchase orders**, and download the Word report.

## Validation limitations
* This release is rule-based, not an LLM agent. It verifies selected totals, currencies, quote expiry dates and evidence presence, and explicitly leaves other guideline checks as `NOT VERIFIED`.
* A `REJECT` indicates a verified failure; `PENDING REVIEW` means information or complex checks remain unresolved. An `APPROVE` recommendation is possible only where all required checks pass.
* Scanned documents and screenshots may not be interpretable; this is *not* reliable for unreviewed production approvals.
* The app does not create or approve orders in any purchasing system.

## Security
Your example documents and guideline include `Orange Restricted` markings. A private GitHub repository or Streamlit Community Cloud deployment does not automatically meet corporate data-security requirements. Use only company-authorized hosting and do not upload sensitive documents until approved. This release does not call the OpenAI API.

## Run locally
```
pip install -r requirements.txt
streamlit run app.py
```
