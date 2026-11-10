"""Single inference contract used by the app, reports and tests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
import joblib

ROOT = Path(__file__).resolve().parents[1]
DISCLAIMER = "This model estimates malware risk from permission patterns. Its predictions are not a guarantee that an application is safe or malicious."


def load_artifacts(directory=ROOT / "models"):
    directory = Path(directory)
    evidence = json.loads((directory / "metrics.json").read_text(encoding="utf-8"))
    path = directory / "model.joblib"
    if hashlib.sha256(path.read_bytes()).hexdigest() != evidence["artifact_sha256"]:
        raise ValueError("Model checksum mismatch. Retrain or restore matching artifacts.")
    # Only load the local, trusted training output. Never accept uploaded pickle/joblib files.
    bundle = joblib.load(path)
    if bundle["version"] != evidence["version"] or list(bundle["model"].feature_names_in_) != bundle["features"]:
        raise ValueError("Model metadata or feature schema mismatch.")
    return bundle, evidence


def vectorize(permissions, features):
    if isinstance(permissions, str):
        raise ValueError("Supply a list of permission names.")
    chosen = set(permissions)
    unknown = chosen - set(features)
    if unknown:
        raise ValueError("Unknown permissions: " + ", ".join(sorted(unknown)))
    if not chosen:
        raise ValueError("Select at least one known permission to analyze.")
    return pd.DataFrame([[int(f in chosen) for f in features]], columns=features, dtype=np.uint8)


def risk_category(probability):
    if not np.isfinite(probability) or not 0 <= probability <= 1:
        raise ValueError("Probability must be between zero and one.")
    return "Low" if probability < .3 else "Moderate" if probability < .7 else "High"


def predict(permissions, bundle):
    x = vectorize(permissions, bundle["features"])
    positive = list(bundle["model"].classes_).index(1)
    p = float(bundle["model"].predict_proba(x)[0, positive])
    unseen = [f for f in permissions if bundle["observed_features"][f] == 0]
    warnings = []
    if unseen:
        warnings.append("Selected permissions never present in development data: " + ", ".join(sorted(set(unseen))))
    count = int(x.sum(axis=1).iloc[0])
    low, high = bundle["permission_count_range"]
    if not low <= count <= high:
        warnings.append(f"Permission count is outside the development range ({low}-{high}).")
    return {"probability": p, "classification": "Malware-like" if p >= .5 else "Benign-like",
            "risk_category": risk_category(p), "permissions": sorted(set(permissions)),
            "timestamp": datetime.now(timezone.utc).isoformat(), "version": bundle["version"],
            "model": bundle["selected_model"], "warnings": warnings, "disclaimer": DISCLAIMER}


def explain(permissions, bundle):
    import shap
    x = vectorize(permissions, bundle["features"])
    model = bundle["model"]
    if hasattr(model, "feature_importances_"):
        explainer = shap.TreeExplainer(model, data=bundle["background"], feature_perturbation="interventional", model_output="probability")
        values = np.asarray(explainer.shap_values(x))[0, :, 1]
        base = float(np.asarray(explainer.expected_value)[1])
        output = float(model.predict_proba(x)[0, 1])
        units = "probability"
    else:
        explainer = shap.LinearExplainer(model, bundle["background"])
        values = np.asarray(explainer.shap_values(x))[0]
        base = float(explainer.expected_value)
        output = float(model.decision_function(x)[0])
        units = "log-odds"
    if not np.isclose(base + values.sum(), output, atol=1e-5):
        raise ValueError("SHAP additivity check failed.")
    contributions = [{"permission": f, "present": bool(x[f].iloc[0]), "contribution": float(v)} for f, v in zip(bundle["features"], values)]
    contributions.sort(key=lambda row: -abs(row["contribution"]))
    return {"base_value": base, "output_value": output, "units": units, "contributions": contributions}


def parse_permissions(text, features):
    """Accept newline/comma-separated manifest names, preserving custom namespaces."""
    tokens = [s.strip() for s in text.replace(",", "\n").splitlines() if s.strip()]
    tokens = [s.removeprefix("android.permission.") for s in tokens]
    known = sorted(set(tokens) & set(features))
    unknown = sorted(set(tokens) - set(features))
    return known, unknown
