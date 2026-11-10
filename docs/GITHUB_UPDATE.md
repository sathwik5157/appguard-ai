# Apply this presentation update

This package includes the full source, original screenshots, three documentation graphics and the plain-language PDF. It does not include the instructor workbook or trained model.

## Upload

1. Extract `appguard-ai-github-update.zip` into a new empty folder.
2. Open that folder. You should immediately see `README.md`, `app.py`, `appguard`, `assets`, `tests` and `docs`.
3. In your existing GitHub repository, choose **Add file > Upload files**.
4. Select and drag all extracted files AND folders, including `.github`, `.streamlit` and `.gitignore`. Do not drag the enclosing folder or ZIP.
5. Commit with: `Improve project documentation, add screenshot gallery and restore complete source`.
6. Confirm the README banner, screenshots, results graphic and architecture image load. Open the PDF link.
7. Confirm `appguard/inference.py`, `tests/test_core.py` and `.github/workflows/tests.yml` exist in GitHub. The public repository reviewed on 10 November was missing these source folders.

Uploading this package updates matching paths but does not remove files already on GitHub. The reviewed public repository also contained `Combined.xlsx`, `streamlit.log` and `streamlit-error.log`. Remove runtime logs from the repository. Confirm permission with your instructor before continuing to publish the workbook. Removing a file in a later commit does not remove earlier copies from Git history. The local `.gitignore` cannot retroactively remove files already uploaded through GitHub's browser.

## Repository About settings

Description: `Explainable Android permission classification with SHAP, grouped evaluation, and an interactive Streamlit app.`

Topics: `machine-learning`, `explainable-ai`, `android`, `malware-detection`, `streamlit`, `scikit-learn`, `shap`, `python`.

Leave Website blank until a real public demo has been deployed. A localhost address is not a recruiter-accessible website.

## What recruiters can review now

The README provides a 30-second introduction, screenshots, real test metrics, design rationale, a code map and a PDF guide. To execute predictions, a reviewer still needs an authorized workbook for training or trusted trained model artifacts. Source-only tests intentionally skip artifact-dependent checks. No live deployment or updated GitHub commit is implied by downloading this package.
