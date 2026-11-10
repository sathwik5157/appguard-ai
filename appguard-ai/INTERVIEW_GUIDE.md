# Explain AppGuard AI in an interview

## 30-second introduction
“I built AppGuard AI, an explainable machine-learning application that classifies Android permission patterns. I used an instructor-created dataset with 11,274 apps and 195 permission features. I found many repeated patterns, so I kept identical patterns together across splits to reduce leakage. Extra Trees won on validation F1 and achieved 88.66% F1 on a separate test set. The app shows real predictions, SHAP explanations, what-if comparisons and a transparent evaluation dashboard.”

Use this wording only after you can explain the implementation. Be candid about AI assistance in building the project when asked. Do not claim you collected the dataset, deployed production antivirus, or independently reproduced the earlier 95.15% result.

## Two-minute technical explanation
“I first checked the data rather than assuming the prompt described it exactly. The workbook had 197 total columns, but two were the label and app ID, so the input was 195 permissions. There were no missing values. There were only 3,273 distinct patterns across 11,274 apps, including 85 patterns with conflicting labels.

“I excluded the identifier and target, hashed each permission vector, and used stratified group splitting for approximately 60% training, 20% validation and 20% test. I compared logistic regression, Random Forest and Extra Trees, with a prior-only baseline. I selected the model using validation F1 at a fixed 0.5 threshold, then refitted it on training plus validation and evaluated it once on test.

“Extra Trees achieved 89.63% accuracy, 96.01% precision and 82.36% recall. That precision–recall gap matters: it missed 196 malware-labeled apps. I show those errors, probability reliability and group-bootstrap uncertainty rather than presenting a single accuracy number.

“The Streamlit app converts selections into the exact training schema, runs the saved model, and uses Tree SHAP to explain its probability relative to 100 development-background examples. I verify additivity and label present and absent permissions. Tests cover schema ordering, invalid inputs, leakage, explanation consistency, exported reports and interactive page flows. The next essential step is an independent, time-separated evaluation with verified data provenance.”

## Ten questions and answers

**1. Why use permissions?**
They are structured, interpretable static signals and match the available dataset. They cannot reveal all malicious behavior. Sensitive permissions are also used by legitimate apps.

**2. What is Random Forest, and why did you use Extra Trees instead?**
Random Forest combines many decision trees trained with randomness in data and feature selection. Extra Trees introduces additional randomness in candidate split thresholds and normally uses the full training sample by default. Both average tree probabilities. I compared them, and Extra Trees had the highest validation F1 with the fixed configurations. That is evidence for this split, not proof it is universally better.

**3. What was the most important data issue?**
Repeated permission patterns. If identical inputs occur in both training and test, a model can appear to generalize while recognizing familiar patterns. I grouped identical inputs before splitting, including patterns whose labels disagreed.

**4. Why not remove every repeated pattern?**
Different app IDs can legitimately share permissions. I kept those observations and grouped them. Removing conflicting labels would hide a real limitation. Exact duplicate full rows would be removed, but none existed in the supplied file.

**5. How did you avoid target leakage?**
The label and app ID are excluded. Matching feature patterns never cross splits. Validation selects the model; test does not. Background data for SHAP comes only from development data. This does not eliminate every possible family or collection-source leakage route.

**6. Explain precision, recall, F1 and ROC-AUC.**
Precision asks what fraction of malware predictions are correct. Recall asks what fraction of malware-labeled apps are detected. F1 balances them using a harmonic mean. ROC-AUC measures ranking across thresholds. The displayed classification uses a fixed 0.5 threshold, and malware is the positive class.

**7. What does SHAP explain?**
It attributes the difference between a reference model output and this prediction across features. For the selected tree model, contributions are in probability units. Both absent and present features can matter. The contributions plus baseline reproduce the probability. They do not prove a permission causes malware.

**8. Is an 80% score an 80% chance that the app is malicious?**
It is the model's estimated probability under its learned data distribution, not a verified real-world probability. The model is not post-hoc calibrated. I report Brier score and reliability curves and label the risk bands illustrative.

**9. What is tested?**
Feature order and duplicate selections, empty/invalid input, risk-band boundaries, pasted-name normalization, disjoint groups, real model inference, SHAP additivity, artifact checksums, metric reproduction, HTML escaping and the Streamlit analysis journey. Restricted artifact tests skip in source-only CI and run locally after training.

**10. What would you improve before deployment?**
Establish source provenance and sharing rights, evaluate an independent dataset and future malware families, use grouped nested validation for tuning, assess calibration and operational thresholds, and add code/behavior signals. I would not deploy it as an antivirus based on this evidence alone.

## Five-minute code walkthrough
1. `appguard/data.py`: validation, feature exclusion and grouped splitting.
2. `train_model.py`: candidates, validation selection, refit, final evaluation and saved evidence.
3. `appguard/inference.py`: exact feature vector, inference, input warnings and SHAP additivity.
4. `app.py`: permission analysis, what-if exploration and evidence views.
5. `tests/`: show a real passing test and explain what failure it prevents.

## Resume bullet
Built an explainable Android permission-classification app using Python, scikit-learn, SHAP and Streamlit; evaluated 11,274 instructor-supplied app records using disjoint permission-pattern groups, achieving 88.66% held-out F1 and 0.9704 ROC-AUC, with reproducible evaluation artifacts and automated tests.

Do not call this production experience. Explain your contributions and the assistance used accurately.
