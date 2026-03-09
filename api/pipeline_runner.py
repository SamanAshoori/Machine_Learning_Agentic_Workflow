import json
import os
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from typing import Any
from scipy import stats as scipy_stats
from sklearn.utils.class_weight import compute_class_weight
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import mutual_info_classif
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    roc_auc_score,
    recall_score,
    f1_score,
)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


# ---------------------------------------------------------------------------
# ETL helpers (user-driven, no agent)
# ---------------------------------------------------------------------------

def get_column_details(csv_path: str) -> list[dict[str, Any]]:
    """Return detailed stats for every column in the dataset."""
    df = pd.read_csv(csv_path, nrows=2000)
    full_len = len(pd.read_csv(csv_path, usecols=[0]))

    columns = []
    for col in df.columns:
        s = df[col]
        info: dict[str, Any] = {
            "name": col,
            "dtype": str(s.dtype),
            "null_count": int(s.isnull().sum()),
            "null_pct": round(float(s.isnull().mean()) * 100, 2),
            "n_unique": int(s.nunique()),
            "total_rows": full_len,
            "sample_values": [str(v) for v in s.dropna().head(5).tolist()],
        }
        if pd.api.types.is_numeric_dtype(s):
            info["stats"] = {
                "mean": round(float(s.mean()), 4) if not s.isnull().all() else None,
                "median": round(float(s.median()), 4) if not s.isnull().all() else None,
                "std": round(float(s.std()), 4) if not s.isnull().all() else None,
                "min": float(s.min()) if not s.isnull().all() else None,
                "max": float(s.max()) if not s.isnull().all() else None,
            }
        else:
            vc = s.value_counts().head(5)
            info["top_values"] = {str(k): int(v) for k, v in vc.items()}
        columns.append(info)
    return columns


def run_target_stats(csv_path: str, target: str) -> dict[str, Any]:
    """Run statistical tests for every column against the target variable."""
    df = pd.read_csv(csv_path, nrows=50000)
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in dataset")

    y = df[target]
    results = []
    for col in df.columns:
        if col == target:
            continue
        s = df[col].dropna()
        y_clean = y[s.index]
        entry: dict[str, Any] = {"column": col}
        try:
            if pd.api.types.is_numeric_dtype(s) and s.nunique() > 10:
                groups = [s[y_clean == v] for v in y.unique()]
                if len(groups) == 2:
                    stat, p = scipy_stats.mannwhitneyu(groups[0], groups[1], alternative="two-sided")
                    entry["test"] = "Mann-Whitney U"
                else:
                    stat, p = scipy_stats.kruskal(*groups)
                    entry["test"] = "Kruskal-Wallis"
                entry["statistic"] = round(float(stat), 4)
                entry["p_value"] = float(p)
            else:
                ct = pd.crosstab(s, y_clean)
                stat, p, dof, _ = scipy_stats.chi2_contingency(ct)
                entry["test"] = "Chi-squared"
                entry["statistic"] = round(float(stat), 4)
                entry["p_value"] = float(p)
            entry["significant"] = entry["p_value"] < 0.05
        except Exception as e:
            entry["test"] = "error"
            entry["p_value"] = None
            entry["significant"] = False
            entry["error"] = str(e)
        results.append(entry)
    return {"target": target, "tests": results}


def apply_etl_decisions(csv_path: str, decisions) -> dict[str, Any]:
    """Drop user-marked columns, encode strings, save cleaned CSV + class weights."""
    df = pd.read_csv(csv_path)

    columns_to_drop = [c.column for c in decisions.columns if c.decision == "drop"]
    columns_to_keep = [c for c in df.columns if c not in columns_to_drop]
    if decisions.target not in columns_to_keep:
        columns_to_keep.append(decisions.target)

    cleaned = df[columns_to_keep].copy()

    # Encode string/object columns with LabelEncoder
    for col in cleaned.columns:
        if cleaned[col].dtype == "object" or str(cleaned[col].dtype) == "string":
            cleaned[col] = LabelEncoder().fit_transform(cleaned[col].astype(str))

    # Compute class weights
    target_vals = cleaned[decisions.target]
    classes = np.unique(target_vals)
    weights = compute_class_weight("balanced", classes=classes, y=target_vals)
    class_weights = {int(c): round(float(w), 6) for c, w in zip(classes, weights)}

    DATA.mkdir(exist_ok=True)
    cleaned.to_csv(DATA / "cleaned_fraud.csv", index=False)
    with open(DATA / "class_weights.json", "w") as f:
        json.dump(class_weights, f)

    return {
        "columns_kept": list(columns_to_keep),
        "columns_dropped": columns_to_drop,
        "cleaned_shape": [len(cleaned), len(cleaned.columns)],
        "class_weights": class_weights,
    }


def get_dataset_summary(csv_path: str) -> dict[str, Any]:
    df = pd.read_csv(csv_path, nrows=5000)
    full_len = len(pd.read_csv(csv_path, usecols=[0]))
    column_info = []
    for col in df.columns:
        column_info.append({
            "name": col,
            "dtype": str(df[col].dtype),
            "null_pct": round(float(df[col].isnull().mean()) * 100, 2),
            "n_unique": int(df[col].nunique()),
            "sample_values": [str(v) for v in df[col].dropna().head(3).tolist()],
        })
    return {
        "filename": os.path.basename(csv_path),
        "rows": full_len,
        "columns": len(df.columns),
        "column_info": column_info,
    }


# ---------------------------------------------------------------------------
# Stats stage — correlation, VIF, mutual information, feature selection
# ---------------------------------------------------------------------------

def run_stats(target: str) -> dict[str, Any]:
    """Run full statistical feature analysis on cleaned data."""
    df = pd.read_csv(DATA / "cleaned_fraud.csv")

    # Encode any remaining string columns so numeric ops work
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    y = df[target]
    X = df.drop(columns=[target])

    # Correlation — flag pairs > 0.85
    corr_matrix = X.corr().abs()
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    high_corr_pairs = []
    high_corr_drop = set()
    for col in upper.columns:
        for row in upper.index:
            if upper.loc[row, col] > 0.85:
                high_corr_pairs.append({"a": row, "b": col, "corr": round(float(upper.loc[row, col]), 4)})
                high_corr_drop.add(col)

    # Chi-squared p-values for all features
    p_values = {}
    for col in X.columns:
        try:
            ct = pd.crosstab(X[col], y)
            _, p, _, _ = scipy_stats.chi2_contingency(ct)
            p_values[col] = float(p)
        except Exception:
            p_values[col] = 1.0

    # VIF via sklearn LinearRegression
    vif_data = {}
    for col in X.columns:
        try:
            X_others = X.drop(columns=[col])
            r2 = LinearRegression().fit(X_others, X[col]).score(X_others, X[col])
            vif_data[col] = round(1.0 / (1.0 - r2), 4) if r2 < 1.0 else float("inf")
        except Exception:
            vif_data[col] = float("inf")

    # Mutual information
    mi_scores = mutual_info_classif(X, y, random_state=42)
    mi_dict = {col: round(float(s), 6) for col, s in zip(X.columns, mi_scores)}

    # Build per-feature metrics and auto-select
    feature_metrics = {}
    selected = []
    excluded = {}
    for col in X.columns:
        feature_metrics[col] = {
            "p_value": p_values[col],
            "vif": vif_data[col],
            "mutual_info": mi_dict[col],
        }
        if col in high_corr_drop:
            excluded[col] = "high correlation (>0.85)"
        elif p_values[col] > 0.05:
            excluded[col] = f"not significant (p={p_values[col]:.4f})"
        elif vif_data[col] > 5:
            excluded[col] = f"high VIF ({vif_data[col]:.2f})"
        else:
            selected.append(col)

    # Sort selected by mutual information descending
    selected.sort(key=lambda c: mi_dict.get(c, 0), reverse=True)

    # Save outputs
    output = {
        "selected_features": selected,
        "feature_metrics": feature_metrics,
    }
    with open(DATA / "selected_features.json", "w") as f:
        json.dump(output, f, indent=2)

    return {
        "selected_features": selected,
        "feature_metrics": feature_metrics,
        "excluded": excluded,
        "high_corr_pairs": high_corr_pairs,
        "total_features": len(X.columns),
    }


# ---------------------------------------------------------------------------
# Model stage — train with user-configurable hyperparameters
# ---------------------------------------------------------------------------

def run_model(
    target: str,
    selected_features: list[str],
    n_estimators: int = 100,
    max_depth: int = 10,
    class_weight_mode: str = "balanced",
    test_split: float = 0.2,
) -> dict[str, Any]:
    """Train a Random Forest on cleaned data with the given config."""
    df = pd.read_csv(DATA / "cleaned_fraud.csv")
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    with open(DATA / "class_weights.json") as f:
        raw_weights = json.load(f)
    class_weights = {int(k): v for k, v in raw_weights.items()}

    y = df[target]
    X = df[selected_features]

    # Chronological split (no shuffle)
    split_idx = int(len(df) * (1 - test_split))
    X_train, X_val = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_val = y.iloc[:split_idx], y.iloc[split_idx:]

    cw = class_weights if class_weight_mode == "balanced" else class_weight_mode

    model = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        class_weight=cw,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_val)
    y_prob = model.predict_proba(X_val)[:, 1]

    cm = confusion_matrix(y_val, y_pred)
    report = classification_report(y_val, y_pred, output_dict=True)
    roc_auc = float(roc_auc_score(y_val, y_prob))
    target_recall = float(recall_score(y_val, y_pred, pos_label=1))

    importances = sorted(
        zip(selected_features, model.feature_importances_),
        key=lambda x: x[1],
        reverse=True,
    )

    # Save model + metrics
    joblib.dump(model, DATA / "model.pkl")
    metrics = {
        "roc_auc": roc_auc,
        "target_recall": target_recall,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "feature_importances": {f: round(float(v), 6) for f, v in importances},
        "train_shape": list(X_train.shape),
        "val_shape": list(X_val.shape),
    }
    with open(DATA / "model_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)

    return {
        "model_metrics": metrics,
        "model_saved": True,
    }


# ---------------------------------------------------------------------------
# Evaluate stage — threshold tuning on validation or test data
# ---------------------------------------------------------------------------

def run_evaluate(
    target: str,
    selected_features: list[str],
    test_csv_path: str | None = None,
) -> dict[str, Any]:
    """Evaluate the trained model. Uses validation split from training data if no test CSV."""
    model = joblib.load(DATA / "model.pkl")

    if test_csv_path and Path(test_csv_path).exists():
        df = pd.read_csv(test_csv_path)
    else:
        df = pd.read_csv(DATA / "cleaned_fraud.csv")
        split_idx = int(len(df) * 0.8)
        df = df.iloc[split_idx:]

    # Encode non-numeric columns
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            df[col] = LabelEncoder().fit_transform(df[col].astype(str))

    y_test = df[target]
    # Only use features the model was trained on
    available = [f for f in selected_features if f in df.columns]
    X_test = df[available]

    y_probs = model.predict_proba(X_test)[:, 1]

    # Default threshold 0.5
    y_pred_default = (y_probs >= 0.5).astype(int)
    cm_default = confusion_matrix(y_test, y_pred_default).tolist()
    report_default = classification_report(y_test, y_pred_default, output_dict=True)
    roc_auc = float(roc_auc_score(y_test, y_probs))

    # Threshold tuning
    best_f1 = -1.0
    best_threshold = 0.5
    for t in np.arange(0.1, 0.95, 0.05):
        preds = (y_probs >= t).astype(int)
        f = float(f1_score(y_test, preds, pos_label=1))
        if f > best_f1:
            best_f1 = f
            best_threshold = float(t)

    y_pred_opt = (y_probs >= best_threshold).astype(int)
    cm_opt = confusion_matrix(y_test, y_pred_opt).tolist()
    report_opt = classification_report(y_test, y_pred_opt, output_dict=True)

    eval_report = {
        "roc_auc": roc_auc,
        "default_threshold_0.5": {
            "confusion_matrix": cm_default,
            "classification_report": report_default,
            "target_recall": float(report_default.get("1", {}).get("recall", 0)),
        },
        "optimal_threshold_tuning": {
            "optimal_threshold": round(best_threshold, 2),
            "confusion_matrix": cm_opt,
            "classification_report": report_opt,
            "target_recall": float(report_opt.get("1", {}).get("recall", 0)),
            "best_f1_score": round(best_f1, 6),
        },
    }

    with open(DATA / "eval_report.json", "w") as f:
        json.dump(eval_report, f, indent=2)

    return {"eval_report": eval_report}
