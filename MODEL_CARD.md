# AppGuard AI model card

## Intended use
Educational demonstration of binary classification from Android permission patterns. Supports model inspection and ML portfolio discussion. Not intended for blocking software, approving applications, incident response, or asserting that an app is safe.

## Data
Instructor-created Combined.xlsx supplied by the project owner: 11,274 app records, 195 binary permission inputs, 5,721 benign and 5,553 malware labels. The two additional columns are label and app ID. Source documentation and redistribution rights are pending. The file does not establish collection dates, families, label quality, device distribution or Android-version coverage.

## Model and decision rule
Extra Trees, 240 estimators, minimum leaf size 2, square-root feature subsampling, seed 42. Selected by validation F1 against logistic regression and Random Forest. A prior baseline provides context. The final model is trained on 9,018 development apps. Predictions at or above 0.5 are malware-like. Scores are uncalibrated probability estimates. The 0.3/0.7 display bands are illustrative only.

## Evaluation
Matching permission vectors remain in one split, including conflicting labels. Test contains 2,256 apps in 661 groups. Accuracy 89.63%, precision 96.01%, recall 82.36%, F1 88.66%, ROC-AUC 0.9704. Confusion matrix: TN 1,107, FP 38, FN 196, TP 915. Saved JSON includes grouped-bootstrap intervals and reliability diagnostics. Counts and metric definitions are malware-positive.

## Explanation
Interventional Tree SHAP in probability space, using 100 randomly selected development rows as background. Presence and absence can contribute. The app verifies that the baseline plus all contributions equals the predicted output within numerical tolerance. Feature correlations and the chosen background affect attributions; they are not causal evidence.

## Risks and limitations
- False negatives are substantial. The model missed 17.64% of malware-labeled test apps.
- 85 permission patterns have both labels, illustrating an information limit of permissions alone.
- A grouped same-source test does not measure performance on new families or future Android apps.
- Row-weighted metrics emphasize common patterns. Group bootstrap respects clustering but does not remove this weighting.
- 56 full-dataset columns are constant; unobserved permissions cannot be assessed from this training data.
- A hand-entered incomplete permission list changes the input semantics. Unselected means absent, not unknown.
- Reliability may change with class prevalence; scores should not be treated as operational confidence.
- No privacy, fairness, family-level or temporal evaluation is possible from the available metadata.

## Artifact handling
Only trusted local training outputs may be loaded. Raw data, fitted model (including SHAP background), split manifest and test predictions are ignored by Git pending instructor permission. The checksum verifies file consistency, not file trust. Local artifacts are not a public redistribution license.
