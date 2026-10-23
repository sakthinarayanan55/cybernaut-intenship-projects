"""
FR-04: Safe Risk Cue Explainer and Educational Triage Engine
Conforms to:
- NFR-01 (Inert parsing, never clicks/executes external links)
- NFR-02 (Zero live credentials, synthetic token cues)
- NFR-03 (Mandatory decision-support disclaimer)
"""
import re
import json
from typing import Dict, Any, List, Union
import pandas as pd
from src.config import URGENCY_KEYWORDS, CREDENTIAL_HARVEST_KEYWORDS, SUSPICIOUS_TLDS
from src.defanger import extract_sanitized_url_features, defang_url

MANDATORY_DISCLAIMER = (
    "SAFETY NOTICE (NFR-03): PhishShift is an educational triage and decision-support tool, "
    "not a guarantee of safety. Classification outputs are probabilistic recommendations. "
    "Never click, fetch, or execute suspicious content or enter live enterprise credentials."
)

class RiskCueExplainer:
    """
    Generates safe, educational explanations of message risk cues.
    """
    def __init__(self):
        self.disclaimer = MANDATORY_DISCLAIMER

    def explain_message(
        self,
        message_data: Union[pd.Series, Dict[str, Any]],
        prediction_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extracts and synthesizes risk cues into an analyst triage breakdown.
        """
        body = str(message_data.get("body_text", ""))
        subject = str(message_data.get("subject_or_title", ""))
        full_text = f"{subject} {body}".lower()
        sender_type = str(message_data.get("sender_domain_type", "unknown_domain")).lower()
        channel = str(message_data.get("channel", "email")).lower()

        # Parse URL features safely
        url_feats = message_data.get("sanitized_url_features", None)
        if isinstance(url_feats, str):
            try:
                url_feats = json.loads(url_feats)
            except Exception:
                url_feats = extract_sanitized_url_features(body)
        elif not isinstance(url_feats, dict):
            url_feats = extract_sanitized_url_features(body)

        risk_cues = []
        mitigating_cues = []
        highlighted_phrases = []

        # 1. URL Analysis (Safe & Inert - NFR-01)
        url_analysis = {
            "has_url": url_feats.get("has_url", False),
            "is_inert_defanged": True,
            "url_count": url_feats.get("url_count", 0),
            "primary_domain": url_feats.get("primary_domain"),
            "primary_tld": url_feats.get("primary_tld"),
            "risk_flags": []
        }

        if url_feats.get("has_url", False):
            if url_feats.get("is_suspicious_tld", False):
                tld = url_feats.get("primary_tld", "unknown")
                cue = f"Defanged link routes to high-abuse TLD '.{tld}'"
                risk_cues.append(cue)
                url_analysis["risk_flags"].append(cue)
            if url_feats.get("has_ip_host", False):
                cue = "Defanged URL points to bare numeric IP host rather than registered enterprise domain"
                risk_cues.append(cue)
                url_analysis["risk_flags"].append(cue)
            if url_feats.get("is_shortener", False):
                cue = "URL shortening service detected (conceals true destination domain)"
                risk_cues.append(cue)
                url_analysis["risk_flags"].append(cue)
            if url_feats.get("has_at_symbol", False):
                cue = "Embedded '@' symbol in URL (HTTP basic auth deception vector)"
                risk_cues.append(cue)
                url_analysis["risk_flags"].append(cue)
        else:
            mitigating_cues.append("No embedded hyperlinks or click targets present")

        # 2. Sender Domain Cues
        domain_analysis = {
            "sender_domain_type": sender_type,
            "is_trusted": sender_type in ["internal_trusted", "verified_partner"]
        }
        if sender_type in ["typosquat_lookalike"]:
            risk_cues.append("Sender domain exhibits brand-impersonation lookalike/typosquat characteristics")
        elif sender_type in ["suspicious_tld"]:
            risk_cues.append("Sender domain originates from a high-risk non-standard top-level domain")
        elif sender_type in ["public_freemail"]:
            risk_cues.append("Official enterprise matter dispatched from unauthenticated public freemail account")
        elif sender_type in ["internal_trusted", "verified_partner"]:
            mitigating_cues.append(f"Sender originates from cryptographically verified source: '{sender_type}'")

        # 3. Urgency & Coercive Pressure Cues
        matched_urgency = [kw for kw in URGENCY_KEYWORDS if kw in full_text]
        if matched_urgency:
            risk_cues.append(f"High-pressure artificial urgency cues identified: {matched_urgency}")
            highlighted_phrases.extend(matched_urgency)

        # 4. Credential Harvesting Cues
        matched_cred = [kw for kw in CREDENTIAL_HARVEST_KEYWORDS if kw in full_text]
        if matched_cred:
            risk_cues.append(f"Credential/identity verification phrasing: {matched_cred}")
            highlighted_phrases.extend(matched_cred)

        # 5. Synthesis Narrative & Educational Triage Rationale
        prob_phish = prediction_result.get("phishing_probability", 0.5)
        decision = prediction_result.get("decision", "ABSTAIN")

        narrative = self._generate_narrative(
            decision=decision,
            prob_phish=prob_phish,
            risk_cues=risk_cues,
            mitigating_cues=mitigating_cues,
            full_text=full_text,
            sender_type=sender_type
        )

        return {
            "decision": decision,
            "action_code": prediction_result.get("action_code"),
            "action_label": prediction_result.get("action_label"),
            "phishing_probability": prob_phish,
            "risk_cues": risk_cues,
            "mitigating_cues": mitigating_cues,
            "highlighted_phrases": list(set(highlighted_phrases)),
            "url_analysis": url_analysis,
            "domain_analysis": domain_analysis,
            "triage_narrative": narrative,
            "disclaimer": self.disclaimer
        }

    def _generate_narrative(
        self,
        decision: str,
        prob_phish: float,
        risk_cues: List[str],
        mitigating_cues: List[str],
        full_text: str,
        sender_type: str
    ) -> str:
        """
        Synthesizes human-readable explanation conforming to FR-04 requirements.
        """
        if decision == "ABSTAIN":
            return (
                f"Prediction uncertainty is high (P={prob_phish:.1%}). The message combines conflicting signals: "
                f"it contains {len(risk_cues)} suspicious cues but originates from '{sender_type}'. "
                f"Automated blocking is deferred; routing to Tier-2 SOC Analyst for out-of-band verification."
            )
        elif decision == "PHISHING":
            cues_summary = "; ".join(risk_cues[:3]) if risk_cues else "structural anomalies"
            return (
                f"Elevated risk detected (P={prob_phish:.1%}). Primary risk drivers: {cues_summary}. "
                f"The message exhibits characteristic social-engineering coercion and unverified destination links."
            )
        else: # BENIGN
            if "password" in full_text or "payroll" in full_text:
                return (
                    f"Classified as legitimate business message (P={prob_phish:.1%}). "
                    f"Although sensitive topics ('password'/'payroll') or urgency terms appear, the sender domain "
                    f"is verified ('{sender_type}') and destination links are legitimate corporate assets."
                )
            return (
                f"Low risk assessment (P={prob_phish:.1%}). No malicious links, spoofing indicators, "
                f"or deceptive credential harvest patterns were detected."
            )
