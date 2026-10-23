"""
FR-04: Selective Classification with Abstain / Reject Option
Routes uncertain predictions to human helpdesk analysts instead of forcing risky automated decisions.
"""
import math
from typing import Dict, Any, Union
import numpy as np
import pandas as pd
from src.config import ABSTAIN_LOWER_BOUND, ABSTAIN_UPPER_BOUND

def compute_entropy(prob_phish: float) -> float:
    """
    Computes Shannon entropy (base 2) as an information-theoretic measure of uncertainty.
    Ranges from 0.0 (total certainty) to 1.0 (maximum uncertainty at p=0.50).
    """
    p = max(1e-6, min(1.0 - 1e-6, prob_phish))
    q = 1.0 - p
    return float(-(p * math.log2(p) + q * math.log2(q)))

class AbstainClassifierWrapper:
    """
    Wraps any base probability estimator with an abstain/reject mechanism.
    Enforces FR-04 by declining to classify messages falling in the uncertainty region.
    """
    def __init__(
        self,
        base_model,
        lower_bound: float = ABSTAIN_LOWER_BOUND,
        upper_bound: float = ABSTAIN_UPPER_BOUND
    ):
        self.base_model = base_model
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    def predict_with_abstain(self, df_or_row: Union[pd.DataFrame, pd.Series, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Classifies input message with abstain decision support.
        """
        if isinstance(df_or_row, dict):
            df_input = pd.DataFrame([df_or_row])
        elif isinstance(df_or_row, pd.Series):
            df_input = pd.DataFrame([df_or_row.to_dict()])
        else:
            df_input = df_or_row

        # Get probability from base model
        probs = self.base_model.predict_proba(df_input)
        prob_phish = float(probs[0, 1])
        prob_benign = float(probs[0, 0])

        entropy = compute_entropy(prob_phish)
        
        # Decision Logic with Abstain Thresholds
        if self.lower_bound <= prob_phish <= self.upper_bound or entropy >= 0.93:
            decision = "ABSTAIN"
            action_code = "NEEDS_MANUAL_TRIAGE"
            action_label = "Uncertain - Escalated to SOC Analyst"
            badge_class = "badge-warning"
            confidence_level = "Low (High Uncertainty)"
        elif prob_phish > self.upper_bound:
            decision = "PHISHING"
            action_code = "SUSPICIOUS_PHISHING"
            action_label = "Flagged Suspicious Phishing"
            badge_class = "badge-danger"
            confidence_level = "High" if prob_phish >= 0.85 else "Moderate"
        else:
            decision = "BENIGN"
            action_code = "LEGITIMATE_BENIGN"
            action_label = "Verified Legitimate Business Message"
            badge_class = "badge-success"
            confidence_level = "High" if prob_phish <= 0.15 else "Moderate"

        return {
            "decision": decision,
            "action_code": action_code,
            "action_label": action_label,
            "badge_class": badge_class,
            "confidence_level": confidence_level,
            "phishing_probability": round(prob_phish, 4),
            "benign_probability": round(prob_benign, 4),
            "uncertainty_entropy": round(entropy, 4),
            "abstain_bounds": [self.lower_bound, self.upper_bound],
            "is_abstain": decision == "ABSTAIN"
        }

    def evaluate_batch(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Evaluates a batch of messages, recording coverage and accuracy on non-abstained samples.
        """
        probs = self.base_model.predict_proba(df)[:, 1]
        y_true = df["label"].values

        abstained_mask = (probs >= self.lower_bound) & (probs <= self.upper_bound)
        non_abstained_mask = ~abstained_mask

        total_samples = len(df)
        abstained_count = int(np.sum(abstained_mask))
        covered_count = int(np.sum(non_abstained_mask))
        coverage_rate = float(covered_count / total_samples) if total_samples > 0 else 0.0

        if covered_count > 0:
            preds_covered = (probs[non_abstained_mask] > self.upper_bound).astype(int)
            accuracy_covered = float(np.mean(preds_covered == y_true[non_abstained_mask]))
        else:
            accuracy_covered = 0.0

        return {
            "total_samples": total_samples,
            "abstained_count": abstained_count,
            "coverage_rate": round(coverage_rate, 4),
            "accuracy_on_covered": round(accuracy_covered, 4)
        }
