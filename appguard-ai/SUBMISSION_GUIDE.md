# Submission and demo guide

## Present the project
1. Launch with `launch.cmd` or `.venv\Scripts\python.exe -m streamlit run app.py`.
2. Open the overview and explain that the model is trained on the instructor dataset.
3. Analyze `INTERNET`, `READ_SMS`, and `SEND_SMS`. These are demonstration inputs, not a known malicious app. Read the actual result rather than promising a particular score.
4. Show SHAP, including absent permissions. Download the HTML report.
5. Compare a changed permission set and explain why lower model probability does not establish safety.
6. Open Model evidence. Show the validation comparison, test errors and data audit.
7. Explain the repeated-pattern issue and why the held-out result is more useful than chasing a high accuracy number.

## Upload source to GitHub
The instructor workbook and derived artifacts are excluded by `.gitignore`. Do not upload the whole working directory through a web form, which bypasses Git ignore rules. Use Git or the prepared source-only ZIP.

```powershell
git init
git add .
git status
git commit -m "Build AppGuard AI explainable permission classifier"
```

Review `git status` before committing: no `.venv`, workbook, model binary, secrets or derived row-level files should be staged. Create an empty GitHub repository, then use the remote instructions GitHub provides. No repository has been created or published automatically.

Without model files, a public checkout displays a clear instruction to train. Unit tests run; artifact/UI integration tests skip explicitly. This is an intentional source-only distribution until sharing rights are established.

## Enable a runnable public demo after permission
Ask the instructor whether both the workbook and trained model (which includes sampled feature rows for SHAP) may be shared. Record the permission/license and dataset provenance in the data README. If model redistribution is permitted, include these three matching files:

- `models/model.joblib`
- `models/metrics.json`
- `models/schema.json`

These are currently ignored. After receiving permission, add the approved files explicitly with `git add -f` or revise the ignore rules. The raw workbook is not needed for inference. The split manifest and test predictions are needed for full local audit tests; include them only if approved. If you use a different dataset, retrain and update all reported results and documentation.

## Streamlit Community Cloud
After approved artifacts are committed, connect the repository, choose `app.py` as the entry point and Python 3.12 in advanced settings, then deploy. The root requirements file and `.streamlit/config.toml` provide dependencies and theme. Verify all four pages, real inference, SHAP and report download at the deployed URL. Do not list a live link until it works. No cloud deployment has been performed here.

## Before applying
- Read the interview guide and explain the code in your own words.
- Attach the source repository and, if available, an authorized working demo.
- Include actual results and the missed-malware count.
- Credit the instructor dataset; do not claim data collection as your work.
- Be transparent about AI-assisted development.
- Avoid claiming production security readiness or a reproduced 95.15% accuracy.
