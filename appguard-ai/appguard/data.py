"""Strict input validation and group-disjoint dataset splitting."""
from pathlib import Path
import hashlib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

LABELS = {"Benign": 0, "Malware": 1}


def load_dataset(path: str | Path):
    path = Path(path)
    df = pd.read_excel(path)
    if not {"File Type", "Apk id"}.issubset(df.columns):
        raise ValueError("Expected File Type and Apk id columns.")
    if df.columns.duplicated().any() or df.isna().any().any():
        raise ValueError("Duplicate columns or missing values: inspect the source first.")
    if set(df["File Type"].unique()) != set(LABELS):
        raise ValueError("Expected exactly Benign and Malware labels.")
    raw_rows = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    if df["Apk id"].duplicated().any():
        raise ValueError("Repeated app IDs require a source audit before training.")
    x = df.drop(columns=["File Type", "Apk id"])
    if not x.isin([0, 1]).all().all():
        raise ValueError("All permission features must be binary 0/1.")
    x = x.astype(np.uint8)
    y = df["File Type"].map(LABELS).astype(int)
    # Identical patterns are one group even when their labels disagree.
    groups = pd.util.hash_pandas_object(x, index=False).to_numpy()
    grouped = pd.DataFrame({"group": groups, "label": y}).groupby("group").label
    audit = {
        "source": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "provenance": "Instructor-created workbook, supplied by the project owner. Collection method, label verification, dates and redistribution permission unverified.",
        "raw_rows": raw_rows, "rows": len(df), "exact_duplicates_removed": raw_rows - len(df),
        "features": len(x.columns), "unique_patterns": int(len(np.unique(groups))),
        "conflicting_patterns": int((grouped.nunique() > 1).sum()),
        "constant_features": x.columns[x.nunique() == 1].tolist(),
        "class_counts": df["File Type"].value_counts().to_dict(),
        "missing_values": 0,
    }
    return x, y, groups, audit


def split_groups(x, y, groups, seed=42):
    """Approximate 60/20/20 split; never search seeds using held-out outcomes."""
    outer = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=seed)
    development, test = next(outer.split(x, y, groups))
    inner = StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=seed + 1)
    train_local, val_local = next(inner.split(x.iloc[development], y.iloc[development], groups[development]))
    train, val = development[train_local], development[val_local]
    for a, b in [(train, val), (train, test), (val, test)]:
        if set(groups[a]) & set(groups[b]):
            raise AssertionError("Permission-pattern leakage detected.")
    for indices in [train, val, test]:
        if y.iloc[indices].nunique() != 2:
            raise ValueError("Both classes must be present in each split.")
    return train, val, test
