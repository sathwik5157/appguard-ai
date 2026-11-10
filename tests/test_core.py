import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from appguard.inference import vectorize, risk_category, parse_permissions, load_artifacts, predict, explain
from appguard.report import make_report
from appguard.data import split_groups

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def artifacts():
    if not (ROOT / "models/model.joblib").exists():
        pytest.skip("Train the instructor dataset to run artifact integration tests.")
    return load_artifacts()


def test_schema_order_and_duplicates():
    x = vectorize(["CAMERA", "INTERNET", "CAMERA"], ["INTERNET", "READ_SMS", "CAMERA"])
    assert x.iloc[0].tolist() == [1, 0, 1]
    assert list(x.columns) == ["INTERNET", "READ_SMS", "CAMERA"]


@pytest.mark.parametrize("permissions", [[], ["unknown"], "INTERNET"])
def test_invalid_input(permissions):
    with pytest.raises(ValueError):
        vectorize(permissions, ["INTERNET"])


@pytest.mark.parametrize("p,expected", [(0, "Low"), (.2999, "Low"), (.3, "Moderate"), (.6999, "Moderate"), (.7, "High"), (1, "High")])
def test_risk_boundaries(p, expected):
    assert risk_category(p) == expected


@pytest.mark.parametrize("p", [-.1, 1.1, float("nan")])
def test_invalid_probability(p):
    with pytest.raises(ValueError):
        risk_category(p)


def test_paste_normalization():
    known, unknown = parse_permissions("android.permission.INTERNET, UNKNOWN\ncom.android.browser.permission.READ_HISTORY_BOOKMARKS", ["INTERNET", "com.android.browser.permission.READ_HISTORY_BOOKMARKS"])
    assert len(known) == 2 and unknown == ["UNKNOWN"]


def test_split_keeps_conflicting_patterns_together():
    # Synthetic fixture tests splitting only; never used to train portfolio artifacts.
    x = pd.DataFrame({"a": np.arange(100).repeat(2)})
    y = pd.Series(np.tile([0, 1], 100))
    groups = x.a.to_numpy()
    tr, va, te = split_groups(x, y, groups)
    assert len(set(tr) | set(va) | set(te)) == len(x)
    assert not set(groups[tr]) & set(groups[va])
    assert not set(groups[tr]) & set(groups[te])
    assert not set(groups[va]) & set(groups[te])


def test_real_prediction_and_explanation(artifacts):
    bundle, _ = artifacts
    selected = ["INTERNET", "READ_SMS", "SEND_SMS"]
    result = predict(selected, bundle)
    assert 0 <= result["probability"] <= 1
    assert result["classification"] in ["Malware-like", "Benign-like"]
    assert result["probability"] == pytest.approx(predict(list(reversed(selected)), bundle)["probability"])
    explanation = explain(selected, bundle)
    assert len(explanation["contributions"]) == len(bundle["features"])
    assert np.isclose(explanation["base_value"] + sum(c["contribution"] for c in explanation["contributions"]), explanation["output_value"], atol=1e-5)
    if explanation["units"] == "probability":
        assert np.isclose(result["probability"], explanation["output_value"])


def test_metrics_and_split_audit(artifacts):
    _, evidence = artifacts
    manifest = pd.read_csv(ROOT / "models/split_manifest.csv")
    assert manifest.groupby("pattern_hash").split.nunique().max() == 1
    predictions = pd.read_csv(ROOT / "models/test_predictions.csv")
    from train_model import metrics
    actual = metrics(predictions.label, predictions.probability)
    for name in ["accuracy", "precision", "recall", "f1", "roc_auc", "brier_score"]:
        assert actual[name] == pytest.approx(evidence["test"][name])
    assert actual["confusion_matrix"] == evidence["test"]["confusion_matrix"]


def test_artifact_tampering_rejected(tmp_path, artifacts):
    _, evidence = artifacts
    (tmp_path / "metrics.json").write_text(json.dumps(evidence))
    (tmp_path / "model.joblib").write_bytes(b"changed")
    with pytest.raises(ValueError, match="checksum"):
        load_artifacts(tmp_path)


def test_report_escapes_untrusted_fields():
    result = {"timestamp": "2026-11-10", "classification": "Benign-like", "probability": .25,
              "risk_category": "Low", "permissions": ["<script>alert(1)</script>"], "warnings": [],
              "version": "test", "model": "test", "disclaimer": "Research only"}
    report = make_report(result)
    assert "<script>" not in report
    assert "&lt;script&gt;" in report and "25.0%" in report
    assert "Local explanation unavailable" in report
