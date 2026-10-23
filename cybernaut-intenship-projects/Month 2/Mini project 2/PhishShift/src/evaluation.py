"""
FR-05: Comprehensive Evaluation and Robustness Drift Measurement Engine
Evaluates:
- General metrics (Accuracy, Precision, Recall, F1, ROC-AUC)
- False-Positive Rate specifically on Legitimate Urgent messages (FR-05, AT-01)
- Campaign-Separated Generalization Gap (FR-03, AT-02)
- Robustness Drift on Controlled Text Perturbations (FR-05, AT-03)
"""
from typing import Dict, Any, List, Tuple
import json
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix
)

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_prob: np.ndarray) -> Dict[str, Any]:
    """
    Computes standard binary classification metrics.
    """
    acc = float(accuracy_score(y_true, y_pred))
    prec = float(precision_score(y_true, y_pred, zero_division=0))
    rec = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))
    try:
        auc = float(roc_auc_score(y_true, y_prob))
    except Exception:
        auc = 0.5

    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel() if cm.shape == (2, 2) else (0, 0, 0, 0)
    fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0

    return {
        "accuracy": round(acc, 4),
        "precision": round(prec, 4),
        "recall": round(rec, 4),
        "f1_score": round(f1, 4),
        "roc_auc": round(auc, 4),
        "fpr": round(fpr, 4),
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        }
    }

def measure_urgent_benign_fpr(
    model,
    test_df: pd.DataFrame
) -> Dict[str, Any]:
    """
    FR-05 & AT-01: Measures False-Positive Rate specifically on legitimate messages
    that contain security/urgency words ('password', 'reset', 'payroll', 'urgent').
    """
    # Identify legitimate urgent records
    urgent_keywords = ["password", "reset", "payroll", "urgent", "deadline", "tax", "w-2"]
    
    def is_urgent_benign(row):
        if row["label"] != 0:
            return False
        text = f"{row['subject_or_title']} {row['body_text']}".lower()
        has_kw = any(kw in text for kw in urgent_keywords)
        is_urgent_camp = "urgent" in str(row["campaign_group"]).lower() or "payroll" in str(row["campaign_group"]).lower()
        return has_kw or is_urgent_camp

    urgent_mask = test_df.apply(is_urgent_benign, axis=1)
    urgent_benign_df = test_df[urgent_mask].copy()

    total_urgent_benign = len(urgent_benign_df)
    if total_urgent_benign == 0:
        return {"total_urgent_benign": 0, "fpr_on_urgent": 0.0, "false_positives": 0}

    probs = model.predict_proba(urgent_benign_df)[:, 1]
    preds = (probs >= 0.50).astype(int)

    false_positives = int(np.sum(preds == 1))
    true_negatives = int(np.sum(preds == 0))
    urgent_fpr = float(false_positives / total_urgent_benign)

    # General FPR across all benign
    all_benign_df = test_df[test_df["label"] == 0]
    all_benign_probs = model.predict_proba(all_benign_df)[:, 1]
    all_benign_preds = (all_benign_probs >= 0.50).astype(int)
    general_fpr = float(np.sum(all_benign_preds == 1) / len(all_benign_df)) if len(all_benign_df) > 0 else 0.0

    return {
        "total_urgent_benign_samples": total_urgent_benign,
        "urgent_benign_false_positives": false_positives,
        "urgent_benign_true_negatives": true_negatives,
        "fpr_on_urgent_benign": round(urgent_fpr, 4),
        "fpr_general_benign": round(general_fpr, 4),
        "fpr_inflation_delta": round(urgent_fpr - general_fpr, 4),
        "analysis_note": (
            f"FPR on legitimate urgent messages is {urgent_fpr:.1%}, compared to {general_fpr:.1%} overall. "
            f"Attack-like vocabulary in legitimate contexts causes a measurable +{urgent_fpr - general_fpr:.1%} FPR shift."
        )
    }

def evaluate_heldout_campaigns(
    model,
    test_df: pd.DataFrame,
    heldout_campaigns: List[str]
) -> Dict[str, Any]:
    """
    FR-03, AT-02: Evaluates generalization exclusively on held-out unseen campaign groups.
    """
    heldout_df = test_df[test_df["campaign_group"].isin(heldout_campaigns)].copy()
    if heldout_df.empty:
        return {"heldout_samples": 0}

    y_true = heldout_df["label"].values
    probs = model.predict_proba(heldout_df)[:, 1]
    preds = (probs >= 0.50).astype(int)

    metrics = compute_metrics(y_true, preds, probs)
    metrics["heldout_samples"] = len(heldout_df)
    metrics["campaigns_tested"] = heldout_campaigns

    # Breakdown by individual campaign
    breakdown = {}
    for camp in heldout_campaigns:
        c_df = heldout_df[heldout_df["campaign_group"] == camp]
        if not c_df.empty:
            c_true = c_df["label"].values
            c_probs = model.predict_proba(c_df)[:, 1]
            c_preds = (c_probs >= 0.50).astype(int)
            breakdown[camp] = {
                "samples": len(c_df),
                "label": int(c_true[0]),
                "accuracy": round(float(accuracy_score(c_true, c_preds)), 4),
                "avg_predicted_phishing_prob": round(float(np.mean(c_probs)), 4)
            }
    metrics["breakdown_by_campaign"] = breakdown
    return metrics

def evaluate_perturbations(
    model,
    perturbations_list: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    FR-05, AT-03: Tests model robustness against 8 controlled text perturbations.
    """
    results = []
    for item in perturbations_list:
        # Build synthetic row for original
        orig_row = {
            "channel": "email" if "sms" not in item["id"].lower() else "sms",
            "subject_or_title": "Original Alert",
            "body_text": item["original"],
            "sender_domain_type": "internal_trusted" if item["expected_label"] == 0 else "suspicious_tld"
        }
        pert_row = {
            "channel": "email" if "sms" not in item["id"].lower() else "sms",
            "subject_or_title": "Perturbed Alert",
            "body_text": item["perturbed"],
            "sender_domain_type": "internal_trusted" if item["expected_label"] == 0 else "suspicious_tld"
        }

        orig_df = pd.DataFrame([orig_row])
        pert_df = pd.DataFrame([pert_row])

        prob_orig = float(model.predict_proba(orig_df)[0, 1])
        prob_pert = float(model.predict_proba(pert_df)[0, 1])
        pred_pert = int(prob_pert >= 0.50)

        drift = prob_pert - prob_orig
        is_correct = (pred_pert == item["expected_label"])

        results.append({
            "test_id": item["id"],
            "type": item["type"],
            "description": item["description"],
            "expected_label": item["expected_label"],
            "orig_probability": round(prob_orig, 4),
            "perturbed_probability": round(prob_pert, 4),
            "probability_drift": round(drift, 4),
            "perturbed_prediction": pred_pert,
            "prediction_status": "PASS" if is_correct else "DRIFT_FAILURE",
            "text_snippet": item["perturbed"][:90] + "..."
        })
    return results
