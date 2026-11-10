# Local verification

Verified on 10 November 2026 with Python 3.12.14 on Windows.

- Trained all four baseline/candidate models on the actual supplied workbook.
- Selected Extra Trees using validation F1, then refitted on train + validation.
- Recomputed saved test metrics from held-out predictions and checked split-group disjointness.
- Verified real inference and numerical SHAP additivity.
- Executed the complete automated suite: **24 passed**, no skipped tests in the local artifact-enabled run.
- Streamlit AppTest verified Overview, Analyze, Model evidence and Project notes, empty-input handling, real prediction, SHAP availability, changed-input messaging and what-if interaction.
- Verified report escaping and checksum failure handling.
- Started Streamlit on `127.0.0.1:8501` and visually reviewed the rendered overview and browser analysis workflow.
- Source packaging uses an explicit allowlist and excludes the workbook, model binary and row-level evaluation artifacts.

The restricted execution sandbox blocked local sockets and temporary-folder creation; final integration tests and the localhost server ran with the tool's approved sandbox escalation. This is an execution-environment constraint, not an app permission requirement.

The source-only CI suite skips tests requiring private model artifacts. Those tests must be rerun after training on an authorized dataset. No public GitHub repository or cloud deployment has been created or verified. Dataset collection provenance and redistribution permission remain unresolved.
