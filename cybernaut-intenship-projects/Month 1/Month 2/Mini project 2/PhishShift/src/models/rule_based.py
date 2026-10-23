"""
FR-02: Baseline Model 1 - Heuristic Rule-Based Risk Classifier
Applies expert cybersecurity triage rules without statistical training.
"""
from typing import Dict, Any, List, Union
import json
import pandas as pd
from src.config import URGENCY_KEYWORDS, CREDENTIAL_HARVEST_KEYWORDS, SUSPICIOUS_TLDS
from src.defanger import extract_sanitized_url_features

class RuleBasedClassifier:
    """
    Expert rule-based heuristic classifier.
    Assigns risk scores based on explicit cybersecurity triage heuristics.
    """
    def __init__(self, risk_threshold: float = 0.50):
        self.risk_threshold = risk_threshold
        self.name = "Heuristic Rule-Based Classifier"

    def evaluate_message(self, message_data: Union[pd.Series, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates a single message against cybersecurity triage rules.
        """
        body = str(message_data.get("body_text", ""))
        subject = str(message_data.get("subject_or_title", ""))
        full_text = f"{subject} {body}".lower()
        sender_type = str(message_data.get("sender_domain_type", "unknown_domain")).lower()

        # Parse URL features
        url_feats = message_data.get("sanitized_url_features", None)
        if isinstance(url_feats, str):
            try:
                url_feats = json.loads(url_feats)
            except Exception:
                url_feats = extract_sanitized_url_features(body)
        elif not isinstance(url_feats, dict):
            url_feats = extract_sanitized_url_features(body)

        score = 0.0
        triggered_rules = []

        # Rule 1: High-risk sender domain type
        if sender_type in ["typosquat_lookalike", "suspicious_tld"]:
            score += 0.40
            triggered_rules.append(f"RULE-01: Sender domain categorized as '{sender_type}' (+0.40)")
        elif sender_type in ["public_freemail"]:
            score += 0.20
            triggered_rules.append("RULE-01B: Business notice sent from public freemail provider (+0.20)")
        elif sender_type in ["internal_trusted", "verified_partner"]:
            score -= 0.35
            triggered_rules.append(f"RULE-SAFE: Verified trusted internal/partner domain '{sender_type}' (-0.35)")

        # Rule 2: Suspicious Defanged URL patterns
        if url_feats.get("has_url", False):
            if url_feats.get("is_suspicious_tld", False):
                score += 0.35
                tld = url_feats.get("primary_tld", "unknown")
                triggered_rules.append(f"RULE-02A: Inert link points to high-risk/abused TLD '.{tld}' (+0.35)")
            if url_feats.get("has_ip_host", False):
                score += 0.35
                triggered_rules.append("RULE-02B: Defanged URL points directly to numeric IP address (+0.35)")
            if url_feats.get("is_shortener", False):
                score += 0.20
                triggered_rules.append("RULE-02C: URL shortener obfuscation detected (+0.20)")
            if url_feats.get("has_at_symbol", False):
                score += 0.25
                triggered_rules.append("RULE-02D: URL contains embedded @ credential trap (+0.25)")

        # Rule 3: Urgency & Coercive Deadline pressure
        matched_urgency = [kw for kw in URGENCY_KEYWORDS if kw in full_text]
        if matched_urgency:
            weight = min(0.30, len(matched_urgency) * 0.10)
            score += weight
            triggered_rules.append(f"RULE-03: Coercive urgency cues detected: {matched_urgency[:3]} (+{weight:.2f})")

        # Rule 4: Credential harvesting prompts
        matched_cred = [kw for kw in CREDENTIAL_HARVEST_KEYWORDS if kw in full_text]
        if matched_cred:
            weight = min(0.30, len(matched_cred) * 0.10)
            score += weight
            triggered_rules.append(f"RULE-04: Credential/payment validation prompts: {matched_cred[:3]} (+{weight:.2f})")

        # Rule 5: Brand impersonation mismatch
        # e.g., mentions Microsoft, Okta, ADP, Workday but sender is not internal/verified
        brand_mentions = ["microsoft", "office 365", "m365", "okta", "adp", "workday", "duo"]
        has_brand = any(b in full_text for b in brand_mentions)
        if has_brand and sender_type not in ["internal_trusted", "verified_partner"]:
            score += 0.25
            triggered_rules.append("RULE-05: Brand impersonation mismatch (Claims identity but sender unverified) (+0.25)")

        # Normalize score between 0.0 and 1.0
        normalized_score = max(0.0, min(1.0, score))
        prediction = 1 if normalized_score >= self.risk_threshold else 0

        return {
            "model": self.name,
            "raw_score": round(score, 3),
            "probability": round(normalized_score, 4),
            "prediction": prediction,
            "prediction_label": "Phishing" if prediction == 1 else "Benign",
            "triggered_rules": triggered_rules
        }

    def predict_proba(self, df: pd.DataFrame):
        """
        Scikit-learn compatible predict_proba.
        Returns array of shape (n_samples, 2): [P(benign), P(phishing)].
        """
        results = [self.evaluate_message(row)["probability"] for _, row in df.iterrows()]
        import numpy as np
        probs = np.array(results)
        return np.column_stack([1.0 - probs, probs])

    def predict(self, df: pd.DataFrame):
        """
        Scikit-learn compatible predict.
        """
        import numpy as np
        probs = self.predict_proba(df)[:, 1]
        return (probs >= self.risk_threshold).astype(int)
