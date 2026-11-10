"""Train candidates on train, select on validation, evaluate once on test."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.calibration import calibration_curve
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix, brier_score_loss, roc_curve,
    precision_recall_curve)
from appguard.data import load_dataset, split_groups, LABELS

ROOT = Path(__file__).resolve().parent


def metrics(y, p):
    pred = p >= .5
    return {"accuracy": accuracy_score(y, pred), "precision": precision_score(y, pred, zero_division=0),
            "recall": recall_score(y, pred, zero_division=0), "f1": f1_score(y, pred, zero_division=0),
            "roc_auc": roc_auc_score(y, p), "average_precision": average_precision_score(y, p),
            "brier_score": brier_score_loss(y, p), "confusion_matrix": confusion_matrix(y, pred).tolist()}


def bootstrap(y, p, groups, seed=42, repeats=500):
    """Resample whole test groups, not correlated rows."""
    rng = np.random.default_rng(seed)
    unique = np.unique(groups)
    members = [np.flatnonzero(groups == g) for g in unique]
    scores = []
    for _ in range(repeats):
        ix = np.concatenate([members[i] for i in rng.integers(0, len(unique), len(unique))])
        scores.append([accuracy_score(y[ix], p[ix] >= .5), f1_score(y[ix], p[ix] >= .5, zero_division=0)])
    limits = np.quantile(scores, [.025, .975], axis=0)
    return {name: limits[:, i].tolist() for i, name in enumerate(["accuracy", "f1"])}


def train(data_path, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    x, y, groups, audit = load_dataset(data_path)
    tr, va, te = split_groups(x, y, groups)
    candidates = {
        "Prior baseline": DummyClassifier(strategy="prior"),
        "Logistic regression": LogisticRegression(C=1, max_iter=2000, random_state=42),
        "Random forest": RandomForestClassifier(n_estimators=240, min_samples_leaf=2, max_features="sqrt", n_jobs=-1, random_state=42),
        "Extra trees": ExtraTreesClassifier(n_estimators=240, min_samples_leaf=2, max_features="sqrt", n_jobs=-1, random_state=42),
    }
    comparison = {}
    for name, model in candidates.items():
        print(f"Training {name}...", flush=True)
        model.fit(x.iloc[tr], y.iloc[tr])
        comparison[name] = metrics(y.iloc[va], model.predict_proba(x.iloc[va])[:, 1])
    selected = max((n for n in candidates if n != "Prior baseline"), key=lambda n: comparison[n]["f1"])
    development = np.concatenate([tr, va])
    model = clone(candidates[selected]).fit(x.iloc[development], y.iloc[development])
    probability = model.predict_proba(x.iloc[te])[:, 1]
    test = metrics(y.iloc[te], probability)
    baseline = DummyClassifier(strategy="prior").fit(x.iloc[development], y.iloc[development])
    test_baseline = metrics(y.iloc[te], baseline.predict_proba(x.iloc[te])[:, 1])
    fpr, tpr, _ = roc_curve(y.iloc[te], probability)
    precision, recall, _ = precision_recall_curve(y.iloc[te], probability)
    observed, predicted = calibration_curve(y.iloc[te], probability, n_bins=10, strategy="uniform")
    version = "1.0-" + audit["sha256"][:10]
    background = x.iloc[development].sample(n=min(100, len(development)), random_state=42)
    artifact = {"model": model, "features": x.columns.tolist(), "label_mapping": LABELS,
                "version": version, "selected_model": selected, "background": background,
                "observed_features": x.iloc[development].max().to_dict(),
                "permission_count_range": [int(x.iloc[development].sum(axis=1).min()), int(x.iloc[development].sum(axis=1).max())]}
    joblib.dump(artifact, output / "model.joblib", compress=3)
    # Hashes and split assignments make overlap independently auditable without app identifiers.
    split = np.full(len(x), "train", dtype=object)
    split[va], split[te] = "validation", "test"
    pd.DataFrame({"pattern_hash": [str(g) for g in groups], "split": split, "label": y}).to_csv(output / "split_manifest.csv", index=False)
    pd.DataFrame({"pattern_hash": [str(g) for g in groups[te]], "label": y.iloc[te].to_numpy(), "probability": probability}).to_csv(output / "test_predictions.csv", index=False)
    importance = (model.feature_importances_ if hasattr(model, "feature_importances_") else np.abs(model.coef_[0]))
    evidence = {"version": version, "created_at": datetime.now(timezone.utc).isoformat(),
        "selected_model": selected, "selection_rule": "Highest validation F1 at fixed 0.5 threshold; refit on train + validation.",
        "seed": 42, "dataset": audit, "validation_comparison": comparison, "test": test,
        "test_baseline": test_baseline, "test_group_bootstrap_95_ci": bootstrap(y.iloc[te].to_numpy(), probability, groups[te]),
        "split": {name: {"rows": len(ix), "patterns": len(np.unique(groups[ix])), "malware_fraction": float(y.iloc[ix].mean())} for name, ix in [("train", tr), ("validation", va), ("test", te)]},
        "pattern_overlap": 0, "roc": {"fpr": fpr.tolist(), "tpr": tpr.tolist()},
        "pr": {"precision": precision.tolist(), "recall": recall.tolist()},
        "calibration": {"predicted": predicted.tolist(), "observed": observed.tolist()},
        "global_importance": dict(sorted(zip(x.columns, importance.tolist()), key=lambda item: -item[1])),
        "global_importance_method": "Impurity importance" if hasattr(model, "feature_importances_") else "Absolute logistic coefficient (log-odds)",
        "runtime": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
        "artifact_sha256": hashlib.sha256((output / "model.joblib").read_bytes()).hexdigest()}
    (output / "metrics.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    (output / "schema.json").write_text(json.dumps({"features": x.columns.tolist(), "labels": LABELS}, indent=2), encoding="utf-8")
    print(json.dumps({"selected": selected, "test": test, "split": evidence["split"]}, indent=2), flush=True)
    return evidence


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "Combined.xlsx")
    parser.add_argument("--output", type=Path, default=ROOT / "models")
    args = parser.parse_args()
    train(args.data, args.output)
