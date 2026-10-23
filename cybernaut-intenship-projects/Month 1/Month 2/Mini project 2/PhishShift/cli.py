"""
Command-Line Interface (CLI) for PhishShift Message Risk Scanner
Task T6: Reliable CLI with valid inputs/outputs, graceful error handling and saved model version.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import argparse
import json
import pandas as pd

from src.config import MODELS_DIR
from src.defanger import sanitize_and_defang_text, extract_sanitized_url_features
from src.models.advanced_ensemble import AdvancedHybridClassifier
from src.models.abstain_classifier import AbstainClassifierWrapper
from src.explainer import RiskCueExplainer

PRESETS = {
    "pwd_reset": {
        "channel": "email",
        "subject_or_title": "Urgent Notice: Annual Mandatory Password Rotation Policy",
        "body_text": (
            "Attention staff: In compliance with ISO 27001 security standards, your corporate Active Directory "
            "password will expire in 7 days. Please change your password directly from your Windows Ctrl+Alt+Del menu "
            "or visit our verified single sign-on portal at hxxps[:]//sso[.]company[.]com/idp/profile. IT Security Team."
        ),
        "sender_domain_type": "internal_trusted"
    },
    "zero_day_phish": {
        "channel": "email",
        "subject_or_title": "Shared Workspace Synchronization Request",
        "body_text": (
            "A collaborating research partner has shared a synchronized encrypted workspace folder with your enterprise identity. "
            "To synchronize local metadata and review project documentation, validate your domain authorization token at "
            "hxxps[:]//docs-sync-federation[.]live/workspace/share-99."
        ),
        "sender_domain_type": "unfamiliar_neutral_domain"
    },
    "urgent_payroll": {
        "channel": "email",
        "subject_or_title": "Action Required: Review Your Monthly Payroll Stub (Workday)",
        "body_text": (
            "Your monthly payslip for October 2026 is now available. Please log in to your verified employee Workday "
            "portal at hxxps[:]//workday[.]company[.]com/payroll to review tax deductions and direct deposit amounts."
        ),
        "sender_domain_type": "internal_trusted"
    },
    "smishing": {
        "channel": "sms",
        "subject_or_title": "SMS Alert: Bank Fraud Notification",
        "body_text": (
            "ALERT: Suspicious transaction of $849.00 flagged on your debit card. If unauthorized, "
            "cancel transaction immediately at hxxps[:]//card-fraud-prevent[.]top/c"
        ),
        "sender_domain_type": "suspicious_tld"
    }
}

def load_system():
    model_path = MODELS_DIR / "advanced_hybrid.joblib"
    if not model_path.exists():
        print(f"[!] Model file not found at {model_path}. Please run 'python train.py' first.")
        sys.exit(1)
    
    hybrid_model = AdvancedHybridClassifier.load(str(model_path))
    abstain_wrapper = AbstainClassifierWrapper(hybrid_model)
    explainer = RiskCueExplainer()
    return abstain_wrapper, explainer

def scan_single(msg_dict: dict, abstain_wrapper, explainer, json_output: bool = False):
    # Ensure text is safely defanged
    msg_dict["body_text"] = sanitize_and_defang_text(msg_dict.get("body_text", ""))
    url_feats = extract_sanitized_url_features(msg_dict["body_text"])
    msg_dict["sanitized_url_features"] = json.dumps(url_feats)

    # Run inference with abstain support
    pred = abstain_wrapper.predict_with_abstain(msg_dict)
    explanation = explainer.explain_message(msg_dict, pred)

    if json_output:
        combined = {**pred, **explanation}
        print(json.dumps(combined, indent=2))
        return

    # Formatted terminal display
    print("=" * 65)
    print(" PHISHSHIFT MESSAGE RISK SCANNER - TRIAGE REPORT")
    print("=" * 65)
    print(f" Subject/Title  : {msg_dict.get('subject_or_title', 'N/A')}")
    print(f" Channel        : {msg_dict.get('channel', 'email').upper()}")
    print(f" Sender Domain  : {msg_dict.get('sender_domain_type', 'unknown_domain')}")
    print("-" * 65)
    print(f" DECISION       : [{pred['decision']}]")
    print(f" ACTION CODE    : {pred['action_code']}")
    print(f" ACTION LABEL   : {pred['action_label']}")
    print(f" Phishing Prob  : {pred['phishing_probability']:.1%}")
    print(f" Confidence     : {pred['confidence_level']}")
    print(f" Entropy Uncert : {pred['uncertainty_entropy']:.3f} (Max: 1.000)")
    print("-" * 65)
    print(" SAFE RISK CUES DETECTED:")
    if explanation["risk_cues"]:
        for cue in explanation["risk_cues"]:
            print(f"  [!] {cue}")
    else:
        print("  [*] None identified")

    if explanation["mitigating_cues"]:
        print("\n MITIGATING CUES:")
        for cue in explanation["mitigating_cues"]:
            print(f"  [+] {cue}")

    print("\n EDUCATIONAL TRIAGE NARRATIVE:")
    print(f"  {explanation['triage_narrative']}")
    print("-" * 65)
    print(f" {explanation['disclaimer']}")
    print("=" * 65)

def main():
    parser = argparse.ArgumentParser(
        description="PhishShift Message Risk Scanner CLI (ML-07)",
        epilog="Educational triage tool. Decision support only — not a guarantee of safety."
    )
    parser.add_argument("--subject", type=str, help="Email subject or SMS header")
    parser.add_argument("--body", type=str, help="Message body content (URLs will be auto-defanged)")
    parser.add_argument("--channel", choices=["email", "sms"], default="email", help="Communication channel")
    parser.add_argument(
        "--sender-domain",
        default="unknown_domain",
        choices=[
            "internal_trusted", "verified_partner", "public_freemail",
            "typosquat_lookalike", "suspicious_tld", "unknown_domain",
            "unfamiliar_neutral_domain", "cloud_file_share", "no_domain_sms"
        ],
        help="Sender domain risk type"
    )
    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Run a predefined test scenario")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    
    args = parser.parse_args()
    abstain_wrapper, explainer = load_system()

    if args.preset:
        msg = PRESETS[args.preset]
        print(f"[*] Running preset scenario: '{args.preset}'")
        scan_single(msg, abstain_wrapper, explainer, json_output=args.json)
    elif args.body:
        msg = {
            "channel": args.channel,
            "subject_or_title": args.subject or "Direct Submission",
            "body_text": args.body,
            "sender_domain_type": args.sender_domain
        }
        scan_single(msg, abstain_wrapper, explainer, json_output=args.json)
    else:
        print("[!] No input provided. Running interactive demo with preset 'pwd_reset'...")
        scan_single(PRESETS["pwd_reset"], abstain_wrapper, explainer, json_output=False)

if __name__ == "__main__":
    main()
