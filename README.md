# PO Validation Agent V1.4 — no API key

Existing Streamlit app with deterministic LangGraph workflow. It accepts variable numbers of uploads, asks the user to confirm the guideline, issues a recommendation, and exports a Word report.

## V1.4 changes

- Adds an 18-row **August 2026 guideline traceability matrix** with section references, evidence, and explicit check coverage.
- The matrix differentiates *a tested sub-check* from *full guideline compliance*. Passing an FPC-list check does not imply one-FPC-per-line has been established.
- When an uploaded guideline appears to replace the August 2026 version, the matrix **does not silently reuse the August rules as proof**. The user must review and update the validation code against the new policy.
- No external AI API, no key, and no automatic ERP approval.

## Updating existing GitHub repo

Replace `app.py`, `report.py`, `README.md`. Add `compliance.py` and `tests/test_compliance.py`. Everything else remains unchanged.

## Tests

`python -m unittest discover -s tests -v`

## Limitations

The 18-row matrix is traceability for specific requirements in the uploaded August guideline, **not 18 fully automated checks**. Check status `NOT VERIFIED` is intentional when rules need other evidence or new parsing logic. Actual source attachments and confidential guidelines should only be hosted in company-approved environments.
