"""
Feature Extraction and Engineering for PhishShift Classifiers
Extracts lexical, syntactic, cybersecurity domain, and safe URL features.
"""
import re
import json
from typing import Dict, Any, List, Union
import numpy as np
import pandas as pd
from src.config import URGENCY_KEYWORDS, CREDENTIAL_HARVEST_KEYWORDS, SUSPICIOUS_TLDS
from src.defanger import extract_sanitized_url_features

SENDER_DOMAIN_CATEGORIES = [
    "internal_trusted",
    "verified_partner",
    "public_freemail",
    "typosquat_lookalike",
    "suspicious_tld",
    "unknown_domain",
    "unfamiliar_neutral_domain",
    "cloud_file_share",
    "no_domain_sms"
]

def extract_domain_features(row: Union[pd.Series, Dict[str, Any]]) -> Dict[str, float]:
    """
    Extracts tabular/structured cybersecurity domain features.
    Works for both offline DataFrame rows and live single input dictionaries.
    """
    body = str(row.get("body_text", ""))
    subject = str(row.get("subject_or_title", ""))
    full_text = f"{subject} {body}".lower()
    channel = str(row.get("channel", "email")).lower()
    sender_type = str(row.get("sender_domain_type", "unknown_domain")).lower()

    # Parse sanitized URL features if present, otherwise extract on the fly
    url_feats = row.get("sanitized_url_features", None)
    if isinstance(url_feats, str):
        try:
            url_feats = json.loads(url_feats)
        except Exception:
            url_feats = extract_sanitized_url_features(body)
    elif not isinstance(url_feats, dict):
        url_feats = extract_sanitized_url_features(body)

    # 1. URL structural risks
    has_url = 1.0 if url_feats.get("has_url", False) else 0.0
    url_count = float(url_feats.get("url_count", 0))
    is_suspicious_tld = 1.0 if url_feats.get("is_suspicious_tld", False) else 0.0
    has_ip_host = 1.0 if url_feats.get("has_ip_host", False) else 0.0
    is_shortener = 1.0 if url_feats.get("is_shortener", False) else 0.0
    num_subdomains = float(url_feats.get("num_subdomains", 0))
    has_at_symbol = 1.0 if url_feats.get("has_at_symbol", False) else 0.0

    # 2. Urgency and Credential Harvest Lexical Cues
    urgency_count = sum(1 for kw in URGENCY_KEYWORDS if kw in full_text)
    cred_count = sum(1 for kw in CREDENTIAL_HARVEST_KEYWORDS if kw in full_text)

    # 3. Surface Text and Syntax Patterns
    raw_body = str(row.get("body_text", ""))
    text_len = float(len(raw_body))
    letters = [c for c in raw_body if c.isalpha()]
    caps_count = sum(1 for c in letters if c.isupper())
    caps_ratio = (caps_count / len(letters)) if letters else 0.0
    exclamation_count = float(raw_body.count("!"))
    defanged_token_count = float(raw_body.count("[:]") + raw_body.count("[.]"))

    # 4. Channel Flag (SMS vs Email)
    is_sms = 1.0 if channel == "sms" else 0.0

    # 5. Sender domain one-hot flags
    sender_flags = {
        f"sender_{cat}": 1.0 if sender_type == cat else 0.0
        for cat in SENDER_DOMAIN_CATEGORIES
    }

    # Assembled feature dictionary
    features = {
        "has_url": has_url,
        "url_count": url_count,
        "is_suspicious_tld": is_suspicious_tld,
        "has_ip_host": has_ip_host,
        "is_shortener": is_shortener,
        "num_subdomains": num_subdomains,
        "has_at_symbol": has_at_symbol,
        "urgency_count": float(urgency_count),
        "cred_harvest_count": float(cred_count),
        "text_length": text_len,
        "caps_ratio": float(caps_ratio),
        "exclamation_count": exclamation_count,
        "defanged_token_count": defanged_token_count,
        "is_sms": is_sms,
        **sender_flags
    }
    return features

def extract_features_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts structured features for an entire dataframe.
    """
    feature_rows = [extract_domain_features(row) for _, row in df.iterrows()]
    return pd.DataFrame(feature_rows)
