"""
Configuration and constants for PhishShift Message Risk Scanner.
ML-07 | Focus: Cybersecurity NLP + Robustness
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models" / "saved"
REPORTS_DIR = BASE_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# Dataset settings
DATASET_PATH = DATA_DIR / "phishshift_dataset.csv"
SOURCE_MANIFEST_PATH = DATA_DIR / "source_manifest.json"
PERTURBATIONS_PATH = DATA_DIR / "test_perturbations.json"

# Schema specification (Section 05)
REQUIRED_SCHEMA = [
    "message_id",
    "channel",
    "subject_or_title",
    "body_text",
    "sanitized_url_features",
    "sender_domain_type",
    "label",
    "campaign_group",
    "collected_date"
]

# FR-04: Uncertainty & Abstain Thresholds
# If model probability falls between LOWER and UPPER bounds, abstain and route to manual triage
ABSTAIN_LOWER_BOUND = 0.38
ABSTAIN_UPPER_BOUND = 0.65

# High entropy threshold for prediction uncertainty
HIGH_ENTROPY_THRESHOLD = 0.90

# High-risk TLDs and lookalike patterns
SUSPICIOUS_TLDS = {
    "top", "xyz", "click", "buzz", "work", "loan", "tk", "ml", "ga", "cf", "gq",
    "rest", "cam", "fit", "live", "country", "bid", "stream", "trade"
}

LEGIT_DOMAINS = {
    "company.com", "corp.internal", "adp.com", "okta.com", "microsoft.com",
    "google.com", "workday.com", "slack.com", "github.com", "jira.internal"
}

# Lexical Urgency / Coercion Patterns
URGENCY_KEYWORDS = [
    "immediately", "urgent", "action required", "within 24 hours", "account suspended",
    "terminated", "payroll freeze", "unauthorized access", "wire transfer", "penalty",
    "legal action", "overdue notice", "confirm identity", "security alert", "expires today",
    "final warning", "breach", "restricted", "verify immediately", "failure to respond"
]

CREDENTIAL_HARVEST_KEYWORDS = [
    "password reset", "verify password", "update payment", "confirm credentials",
    "re-enter password", "login now", "click here to unlock", "validate your account",
    "direct deposit", "w-2 form", "tax document", "routing number", "session expired"
]

# Random seed for reproducibility
RANDOM_STATE = 42

# Ensure directories exist if filesystem is writable (serverless environments like Vercel have read-only filesystems)
for d in [DATA_DIR, MODELS_DIR, REPORTS_DIR, FIGURES_DIR]:
    try:
        d.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass

