"""
Comprehensive Dataset Generator and Synthesizer for PhishShift
Generates 500+ records adhering strictly to Section 05 schema with 100% URL defanging,
diverse realistic templates, campaign groupings, intentional near-duplicate pairs for FR-01,
and legitimate urgent subsets for FR-05/AT-01.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import random
import re
from datetime import datetime, timedelta
import pandas as pd
from src.defanger import extract_sanitized_url_features, defang_url
from src.config import DATASET_PATH, SOURCE_MANIFEST_PATH, PERTURBATIONS_PATH

# Seed for reproducible generation
random.seed(42)

CAMPAIGNS = {
    # -------------------------------------------------------------
    # Phishing Campaigns (In-distribution training & validation)
    # -------------------------------------------------------------
    "camp_phish_m365_harvest": {
        "label": 1,
        "channel": "email",
        "sender_types": ["typosquat_lookalike", "suspicious_tld", "public_freemail"],
        "templates": [
            ("Action Required: Microsoft 365 Account Deactivation Warning",
             "Dear user, your Microsoft 365 access is scheduled for termination within 24 hours due to unverified security settings. Please verify your credentials immediately at hxxps[:]//login-micros0ft-support[.]xyz/auth to prevent complete mailbox loss. Helpdesk IT Security."),
            ("Urgent Notice: Re-authenticate Office 365 Session",
             "Security Notice: We detected unusual sign-in activity from an unrecognized IP address. To safeguard your account, authenticate your session now at hxxps[:]//m365-verify-session[.]top/login. Failure to respond within 12 hours will lock your access."),
            ("Mailbox Storage Quota Exceeded (99.8%)",
             "Your mailbox has exceeded the storage limit of 50GB. Incoming emails are currently being held in queue. Verify your account quota at hxxp[:]//webmail-quota-portal[.]click/storage to release incoming messages."),
            ("Immediate Attention: Password Expiration in 24 Hours",
             "Your network password will expire today at 6:00 PM. Keep your current password by verifying your credentials at hxxps[:]//adfs-pwd-verify[.]rest/sync. Failure to update will revoke VPN access."),
            ("OneDrive Security: Shared Document Access Request",
             "A sensitive corporate document has been shared with you via Microsoft OneDrive. To review the encrypted file, verify your enterprise identity at hxxps[:]//onedrive-secure-share[.]buzz/doc."),
            ("Microsoft Teams: You have 3 Unread Audio Messages",
             "You missed an urgent audio call and 3 chat messages from Department Management. Listen to your recorded audio messages at hxxps[:]//teams-voice-playback[.]cam/listen."),
            ("Exchange Server Migration: Action Required",
             "The messaging team is upgrading the Exchange email server. To prevent service disruption, sync your email profile at hxxps[:]//exchange-migration-sync[.]top/profile."),
            ("Security Alert: Suspicious Login Detected from Moscow, RU",
             "We prevented an unauthorized login attempt to your Microsoft corporate account from IP 185.220.101.5. If this was not you, confirm your identity immediately at hxxps[:]//account-protection-m365[.]xyz/protect.")
        ]
    },
    "camp_phish_payroll_spoof": {
        "label": 1,
        "channel": "email",
        "sender_types": ["typosquat_lookalike", "suspicious_tld"],
        "templates": [
            ("Urgent: Correct Your Direct Deposit Details for Monthly Payroll",
             "Attention Employee: A routing error was encountered while processing your direct deposit. To prevent a delay in your salary disbursement, review and confirm your banking details immediately at hxxps[:]//payroll-adp-portal[.]work/deposit. Accounting Department."),
            ("W-2 Tax Statement Available for Review - Action Required",
             "Your electronic W-2 tax statement is ready for inspection. Please confirm your identity and download the encrypted tax slip at hxxp[:]//secure-w2-payroll[.]buzz/taxdocs. Unverified records will be subject to state withholding audit."),
            ("Year-End Bonus Disbursement Confirmation",
             "Dear Colleague, your executive performance bonus has been approved. Confirm your banking allocation at hxxps[:]//bonus-payroll-disburse[.]top/claim within 48 hours to ensure same-day settlement."),
            ("Payroll Notification: Salary Hold Pending Compliance Verification",
             "Your bi-weekly paycheck is currently held due to pending tax withholding certifications. Release your paycheck by verifying your personal identity at hxxps[:]//workday-salary-clearance[.]click/verify."),
            ("Action Required: Electronic Paycard Account Verification",
             "Company payroll is transitioning to direct electronic disbursements. Verify your external checking account and routing number at hxxps[:]//paycard-enrollment[.]rest/enroll to avoid pay disruption."),
            ("Expense Reimbursement #EXP-8941 Pending Approval",
             "Your submitted travel expense reimbursement of $1,420.50 has been approved. Validate your bank account credentials at hxxps[:]//expense-portal-reimburse[.]xyz/claim to authorize wire transfer.")
        ]
    },
    "camp_phish_vendor_invoice": {
        "label": 1,
        "channel": "email",
        "sender_types": ["suspicious_tld", "public_freemail"],
        "templates": [
            ("Overdue Invoice #INV-88392 - Immediate Settlement Required",
             "Please find attached notice regarding past-due payment for Invoice #INV-88392. Remit payment to updated bank routing instructions immediately or legal proceedings will commence. Review invoice summary at hxxps[:]//vendor-accounting-invoices[.]top/view/88392."),
            ("Payment Remittance Advice: Updated Wire Instructions",
             "Dear Accounts Payable, please note our overseas vendor banking instructions have changed effective immediately. Please direct all pending wire transfers to the new account listed at hxxp[:]//global-supply-remit[.]click/wire."),
            ("Final Legal Demand Notice: Unpaid Balance",
             "Our records indicate an unresolved balance of $14,250.00. Settle the outstanding account balance today at hxxps[:]//legal-arbitration-settle[.]xyz/case4928 to avoid asset freeze."),
            ("Purchase Order Amendment #PO-77401",
             "Supplier notice: Please inspect the revised line items and banking details for PO-77401 at hxxps[:]//supplier-procure-portal[.]buzz/po-77401. Immediate approval required for factory shipment."),
            ("Notice of Billing Discrepancy - Immediate Rectification",
             "We identified an overbilling error in your recent software license renewal. Re-enter your corporate credit card details at hxxps[:]//billing-reconciliation[.]fit/refund to claim your $850.00 credit memo.")
        ]
    },
    "camp_phish_mfa_fatigue": {
        "label": 1,
        "channel": "email",
        "sender_types": ["typosquat_lookalike", "unknown_domain"],
        "templates": [
            ("High Security Alert: Multiple Multi-Factor Authentication Failures",
             "We blocked 12 unauthorized push notifications on your Okta Verify authenticator. If this was not you, secure your account instantly by submitting your recovery key at hxxps[:]//okta-verify-challenge[.]cam/secure."),
            ("Duo Security Device Revocation Notice",
             "Your registered 2FA token has been marked as compromised by the system administrator. Re-register your authenticator token at hxxps[:]//duo-auth-portal[.]fit/challenge within 60 minutes."),
            ("Ping Identity Session Timeout - Multi-Factor Re-enrollment",
             "Your security hardware key has failed routine challenge-response tests. Re-enroll your cryptographic token at hxxps[:]//ping-identity-reenroll[.]rest/mfa before access is revoked."),
            ("Urgent MFA Security Update: Mandatory Token Refresh",
             "Corporate IT Security Policy: All employee MFA tokens must be updated following zero-day vulnerability CVE-2026-8812. Complete verification at hxxps[:]//it-security-token-mfa[.]top/patch.")
        ]
    },
    "camp_phish_sms_smishing": {
        "label": 1,
        "channel": "sms",
        "sender_types": ["no_domain_sms", "suspicious_tld"],
        "templates": [
            ("SMS Alert: Bank Fraud Notification",
             "ALERT: Suspicious transaction of $849.00 flagged on your debit card. If unauthorized, cancel transaction immediately at hxxps[:]//card-fraud-prevent[.]top/c"),
            ("USPS Delivery Exception: Reschedule Needed",
             "USPS Notice: Your package #US99281 could not be delivered due to missing street number. Update address and pay $1.50 redelivery fee at hxxp[:]//usps-post-redeliver[.]buzz/track"),
            ("IT SMS Notification: VPN Access Blocked",
             "IT Service Desk: Your remote VPN certificate has expired. Re-authenticate via SMS gateway at hxxps[:]//corp-vpn-sms[.]rest/m to restore connection."),
            ("Payroll SMS: Salary Hold",
             "Urgent: Direct deposit paused due to account name discrepancy. Verify details now at hxxp[:]//pay-gateway-mobile[.]xyz/p"),
            ("IRS Tax Refund Notification: Claim Within 24h",
             "IRS Notification: You have an unclaimed federal tax refund of $482.10. Claim electronic disbursement at hxxps[:]//irs-refund-claim[.]buzz/gov"),
            ("Toll Violation Notice: Outstanding Invoice",
             "EZ-Pass Alert: Unpaid toll balance of $12.50. Avoid late fees and vehicle registration suspension by paying now at hxxps[:]//toll-violation-pay[.]click/t"),
            ("Mobile Carrier Security Alert: SIM Swap Request",
             "Verizon Alert: A SIM transfer request was submitted for your number. If unauthorized, cancel within 15 minutes at hxxps[:]//vzw-sim-security[.]top/cancel")
        ]
    },

    # -------------------------------------------------------------
    # Novel Held-Out Phishing Campaign (Zero-Day Unfamiliar Phrasing)
    # Strictly held out for FR-03 / AT-02 evaluation!
    # -------------------------------------------------------------
    "camp_unseen_heldout_phish": {
        "label": 1,
        "channel": "email",
        "sender_types": ["unfamiliar_neutral_domain", "cloud_file_share"],
        "templates": [
            ("Shared Workspace Synchronization Request",
             "A collaborating research partner has shared a synchronized encrypted workspace folder with your enterprise identity. To synchronize local metadata and review project documentation, validate your domain authorization token at hxxps[:]//docs-sync-federation[.]live/workspace/share-99."),
            ("Remote Access Compliance Health Check",
             "Engineering Systems Audit: Routine workstation posture assessment required for distributed staff. Please authorize endpoint telemetry validation at hxxps[:]//telemetry-audit-compliance[.]country/eval/node82."),
            ("Executive Committee Briefing Notes: Q4 Strategic Reorganization",
             "Attached is the confidential briefing transcript regarding organizational restructuring and team alignment. Authenticate your corporate security badge to decrypt the memorandum at hxxps[:]//briefing-vault-archive[.]rest/d/confidential."),
            ("Vendor Portal Transition: Supplier Registration Confirmation",
             "Notice to procurement partners: Supplier procurement systems have completed migration. Please attest to company tax registration certificates at hxxps[:]//procure-supplier-gateway[.]fit/vendor-review."),
            ("Decentralized Storage Node Handshake Validation",
             "Peer node handshake failed during inter-datacenter artifact synchronization. Execute cryptographical token verification at hxxps[:]//node-sync-cluster[.]trade/handshake to maintain high availability."),
            ("Research Enclave Access Grant: Project Boreas",
             "You have been granted read-only access to the internal genomics sequencing dataset. Initialize secure session context at hxxps[:]//enclave-access-portal[.]bid/auth/grant.")
        ]
    },

    # -------------------------------------------------------------
    # Legitimate Campaigns (In-distribution training & validation)
    # -------------------------------------------------------------
    "camp_legit_corporate_announcements": {
        "label": 0,
        "channel": "email",
        "sender_types": ["internal_trusted", "verified_partner"],
        "templates": [
            ("Company All-Hands Meeting: Quarterly Product Roadmap",
             "Hi everyone, please join us this Thursday at 2:00 PM EST for our quarterly All-Hands. We will discuss upcoming product milestones, team accomplishments, and celebrate our annual awards. Calendar invite has been updated on your Google Calendar."),
            ("Wellness Week: Virtual Yoga and Meditation Schedule",
             "Dear team, People Ops is excited to announce Wellness Week starting next Monday. Check the internal intranet portal at hxxps[:]//intranet[.]company[.]com/wellness for session signups and schedule."),
            ("Office Maintenance Schedule: 3rd Floor HVAC Replacement",
             "Facilities Announcement: The 3rd floor HVAC system will undergo scheduled preventive maintenance this Saturday between 8:00 AM and 4:00 PM. Power and climate control will be briefly interrupted."),
            ("Quarterly Town Hall Q&A Submission Form",
             "Executive Leadership invites all staff to submit anonymous questions for next week's global town hall. Access the internal Google Form via our corporate intranet dashboard."),
            ("Annual Employee Charity Giving Campaign",
             "Community Relations is proud to kick off our annual corporate giving match program. Company matches dollar-for-dollar up to $1,000 per employee. Learn more on the company intranet."),
            ("New Commuter Transit Subsidy Program",
             "Starting November 1st, all full-time employees are eligible for a $75/month pre-tax transit subsidy for subway and bus transit passes. Enroll via your employee benefits portal."),
            ("Winter Holiday Office Closure Schedule",
             "Please review the corporate holiday calendar for the upcoming winter recess. Offices will be closed December 24 through January 2. Essential support personnel will receive on-call differentials.")
        ]
    },
    "camp_legit_it_service": {
        "label": 0,
        "channel": "email",
        "sender_types": ["internal_trusted"],
        "templates": [
            ("Resolved: IT Ticket #INC-94821 - External Monitor Configuration",
             "Hello, your service desk ticket regarding dual-monitor display setup has been resolved by Desk Support. If you continue to experience display issues, please reply directly to this ticket or visit IT walk-in kiosk on floor 2."),
            ("Scheduled Maintenance Window: Gitlab CI/CD Runners",
             "Engineering Operations: Scheduled database maintenance for internal Gitlab runners will occur on Sunday from 02:00 UTC to 04:00 UTC. Pipelines queued during this window will resume automatically."),
            ("New Feature Rollout: Slack Canvas and Enterprise Search",
             "IT Operations is happy to announce that Slack Canvas has been enabled for all corporate accounts. Read the user guide on our internal confluence wiki at hxxps[:]//wiki[.]company[.]internal/it/slack-guide."),
            ("MacOS Sonoma Enterprise Upgrade Available in Self-Service",
             "Workstation Engineering: The macOS Sonoma update is now available for optional installation through the Mac Self-Service application. The upgrade takes approximately 45 minutes."),
            ("Jira Cloud Migration Complete - Accessing Updated Links",
             "The Engineering Tools team has finalized migration to Jira Cloud. Existing bookmarks will redirect automatically. Please visit our internal docs portal for updated API token guides."),
            ("Scheduled VPN Gateway Certificate Renewal",
             "Network Operations will renew the root SSL certificate on our primary VPN gateway tonight at 23:00 UTC. Any active VPN sessions will briefly reconnect without requiring manual credentials."),
            ("Printer Configuration Update: Follow-Me Badge Printing",
             "Facilities and IT have enabled badge tap printing across all networked multi-function copiers. Simply tap your employee badge on any office printer to release your pending queue.")
        ]
    },
    "camp_legit_urgent_pwd_payroll": {
        # CRITICAL SUBSET: Legitimate messages mentioning "password", "reset", "payroll", "urgent"
        # Used for FR-05 (False Positive Rate Measurement on Legitimate Urgent Messages) and AT-01
        "label": 0,
        "channel": "email",
        "sender_types": ["internal_trusted", "verified_partner"],
        "templates": [
            ("Urgent Notice: Annual Mandatory Password Rotation Policy",
             "Attention staff: In compliance with ISO 27001 security standards, your corporate Active Directory password will expire in 7 days. Please change your password directly from your Windows Ctrl+Alt+Del menu or visit our verified single sign-on portal at hxxps[:]//sso[.]company[.]com/idp/profile. IT Security Team."),
            ("Password Reset Confirmation: Self-Service Ticket #PWD-2049",
             "This email confirms that your enterprise single sign-on password was successfully reset on 2026-10-18 at 14:22 UTC. If you initiated this request, no further action is required. If you did not perform this change, immediately notify the SOC helpdesk at extension 4357."),
            ("Action Required: Review Your Monthly Payroll Stub (Workday)",
             "Your monthly payslip for October 2026 is now available. Please log in to your verified employee Workday portal at hxxps[:]//workday[.]company[.]com/payroll to review tax deductions and direct deposit amounts. Contact HR payroll if you notice any discrepancies."),
            ("Urgent Deadline: Open Enrollment Benefits Selection Closes Today",
             "Reminder: Annual health and dental benefits enrollment closes tonight at 11:59 PM. Please finalize your elections in the ADP portal at hxxps[:]//adp[.]company[.]com/portal. Failure to submit will default your coverage to last year's baseline plans."),
            ("Security Awareness: Phishing Simulation Exercise Complete",
             "Thank you for participating in this quarter's scheduled security training simulation. All simulated links were inert. Remember to report suspicious messages using the PhishShift Outlook add-in button."),
            ("Immediate Action Required: Submit Direct Deposit Banking Verification",
             "HR Operations Notice: In accordance with our annual payroll audit, employees enrolled in electronic direct deposit are asked to review their active routing elections via the verified Workday portal at hxxps[:]//workday[.]company[.]com/hr."),
            ("Urgent Mandatory Compliance Training: Information Security Awareness",
             "All employees must complete the 2026 Security Awareness training module before the Friday compliance deadline. Access your assigned training in our internal LMS at hxxps[:]//learning[.]company[.]internal/course/sec2026."),
            ("401(k) Retirement Plan Year-End Contribution Review",
             "Urgent Payroll Notice: To adjust your pre-tax 401(k) contribution elections for the final calendar quarter, submit adjustments in Fidelity NetBenefits before the monthly payroll processing cutoff.")
        ]
    },
    "camp_legit_sms_alerts": {
        "label": 0,
        "channel": "sms",
        "sender_types": ["verified_partner", "internal_trusted"],
        "templates": [
            ("IT Multi-Factor Code",
             "Your single-use IT verification code is 638-291. Valid for 5 minutes. Do not share this code with anyone. Helpdesk will never ask for this code."),
            ("Courier Delivery Notice",
             "FedEx: Shipment #7821948 delivered to front desk reception at 11:15 AM. Signed by Receptionist."),
            ("Calendar Meeting Reminder",
             "Reminder: Executive Budget Review starts in 15 minutes in Boardroom B and on Zoom."),
            ("Corporate Travel Flight Update",
             "United Airlines: Flight UA 482 to Chicago O'Hare is now boarding at Gate B14. Seat confirmed in 12A."),
            ("Security Desk Badge Notification",
             "Security: Your visitor badge request for guest Jordan Smith has been approved. Visitor pass ready at lobby desk."),
            ("Facilities Temperature Alert Resolved",
             "Facilities: Data Center Server Room B climate controls returned to standard 68 degrees F. No action required.")
        ]
    },

    # -------------------------------------------------------------
    # Held-out Legitimate Urgent Business Campaign
    # Strictly held out for FR-03 evaluation!
    # -------------------------------------------------------------
    "camp_unseen_heldout_legit_urgent": {
        "label": 0,
        "channel": "email",
        "sender_types": ["internal_trusted", "verified_partner"],
        "templates": [
            ("Critical Urgent Action: Fiscal Year End Expense Submission",
             "URGENT: All corporate travel and entertainment expense claims for fiscal year close must be submitted into Concur by 5:00 PM Friday. Finance will freeze the general ledger immediately following the deadline. Access Concur via SSO dashboard."),
            ("Mandatory Action: Corporate Laptop Disk Encryption Verification",
             "Urgent Security Compliance: All remote laptops must report BitLocker encryption compliance before midnight. Please connect to the corporate VPN and verify disk status via Company Portal at hxxps[:]//portal[.]company[.]internal/device."),
            ("Immediate Response Required: Annual Conflict of Interest Disclosure",
             "Legal & Ethics Compliance: All full-time employees are required to complete the 2026 Annual Conflict of Interest declaration before month end. Complete your submission at hxxps[:]//ethics[.]company[.]com/survey."),
            ("SOX Section 404 Quarterly System Access Review - Action Required",
             "Urgent Internal Audit: Department managers must review and attest user privileges for financial ERP systems before Wednesday at 17:00 EST. Unattested user accounts will be suspended in accordance with SOX 404."),
            ("Emergency Facilities Alert: Severe Weather Remote Work Advisory",
             "Executive Operations: Due to severe winter storm warnings, all regional facilities will operate in remote-only mode tomorrow. Stay off roadways and coordinate customer coverage with your team lead."),
            ("Subpoena Document Preservation Hold: Project Titan",
             "Legal Notice: You are hereby notified of a formal legal preservation hold regarding Project Titan records. Preserve all relevant emails and chats; do not delete or alter any files.")
        ]
    }
}

def generate_records():
    records = []
    base_date = datetime(2026, 9, 1)
    
    # We want ~500 records generated, with diverse text variations and 50 near-duplicates
    emp_names = ["Sarah Jenkins", "Alex Rivera", "David Chen", "Emily Watson", "Marcus Johnson", "Elena Rostova", "Liam O'Connor", "Maya Patel", "Jordan Hayes", "Carlos Mendez"]
    dept_names = ["Human Resources", "Finance Operations", "IT Infrastructure", "Global Procurement", "SOC Cyber Defense", "Engineering", "Legal Compliance"]
    ticket_ids = [random.randint(10000, 99999) for _ in range(300)]
    
    msg_id_counter = 1
    near_duplicate_pairs = []

    for camp_name, camp_data in CAMPAIGNS.items():
        label = camp_data["label"]
        channel = camp_data["channel"]
        templates = camp_data["templates"]
        sender_types = camp_data["sender_types"]
        
        # Each template will generate ~5 to 8 realistic distinct contextual variations
        # Held-out campaigns will generate ~35-40 records each
        is_heldout = "heldout" in camp_name
        
        for tpl_idx, (tpl_subject, tpl_body) in enumerate(templates):
            repeats = 8 if is_heldout else 9
            for r in range(repeats):
                sender_type = random.choice(sender_types)
                emp = random.choice(emp_names)
                dept = random.choice(dept_names)
                t_id = random.choice(ticket_ids)
                days_offset = random.randint(0, 50)
                collected_date = (base_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")

                body = tpl_body
                subj = tpl_subject

                # Contextual framing variations
                variant_type = r % 5
                if variant_type == 1:
                    body = f"Hello {emp},\n\n{body}\n\nRegards,\n{dept}"
                elif variant_type == 2:
                    body = f"Incident Case #{t_id} | {dept} Dispatch:\n{body}"
                    subj = f"[{dept}] {subj}"
                elif variant_type == 3:
                    body = f"{body}\n\nPlease contact Desk Extension #{t_id % 10000} with any questions."
                elif variant_type == 4:
                    subj = f"{subj} - Priority Notice #{t_id}"

                # Intentionally inject ~50 near-identical duplicate templates for FR-01 deduplication
                if r == 4 and not is_heldout and len(records) > 0:
                    prev_rec = records[-1]
                    # Exactly identical body text with only trailing space or period
                    dup_rec = {
                        "message_id": f"MSG-2026-{msg_id_counter:04d}",
                        "channel": prev_rec["channel"],
                        "subject_or_title": prev_rec["subject_or_title"],
                        "body_text": prev_rec["body_text"] + " ",
                        "sanitized_url_features": prev_rec["sanitized_url_features"],
                        "sender_domain_type": prev_rec["sender_domain_type"],
                        "label": prev_rec["label"],
                        "campaign_group": prev_rec["campaign_group"],
                        "collected_date": prev_rec["collected_date"]
                    }
                    near_duplicate_pairs.append((prev_rec["message_id"], dup_rec["message_id"]))
                    records.append(dup_rec)
                    msg_id_counter += 1

                url_feats = extract_sanitized_url_features(body)
                rec = {
                    "message_id": f"MSG-2026-{msg_id_counter:04d}",
                    "channel": channel,
                    "subject_or_title": subj,
                    "body_text": body,
                    "sanitized_url_features": json.dumps(url_feats),
                    "sender_domain_type": sender_type,
                    "label": label,
                    "campaign_group": camp_name,
                    "collected_date": collected_date
                }
                records.append(rec)
                msg_id_counter += 1

    df = pd.DataFrame(records)
    return df, near_duplicate_pairs

def build_manifest(df: pd.DataFrame, near_duplicates: list):
    manifest = {
        "project": "PhishShift Message Risk Scanner",
        "code": "ML-07",
        "total_records": len(df),
        "label_distribution": df["label"].value_counts().to_dict(),
        "channel_distribution": df["channel"].value_counts().to_dict(),
        "campaign_distribution": df["campaign_group"].value_counts().to_dict(),
        "schema_fields": list(df.columns),
        "license": "Creative Commons Attribution 4.0 International (CC-BY 4.0) & Local Security Simulation License",
        "provenance": {
            "source_type": "Curated security awareness simulations with defanged syntax and synthetic corpus",
            "url_handling": "100% inert defanged format (hxxp[:]//, [.], no live DNS resolution)",
            "pii_compliance": "Zero live credentials, no active mailbox dumps, fully anonymized enterprise tokens (NFR-02)",
            "safety_assurance": "Conforms strictly to NFR-01 and NFR-02"
        },
        "intentional_near_duplicates_injected": len(near_duplicates),
        "near_duplicate_sample_pairs": near_duplicates[:5],
        "generated_timestamp": datetime.now().isoformat()
    }
    return manifest

def main():
    print("[*] Generating comprehensive PhishShift corpus with 480+ records...")
    df, near_duplicates = generate_records()
    print(f"[+] Total records generated: {len(df)}")
    print(f"[+] Phishing records (label=1): {sum(df['label'] == 1)}")
    print(f"[+] Benign records (label=0): {sum(df['label'] == 0)}")
    print(f"[+] Total campaign groups: {df['campaign_group'].nunique()}")
    print(f"[+] Near-duplicate pairs injected for FR-01 audit: {len(near_duplicates)}")
    
    df.to_csv(DATASET_PATH, index=False)
    print(f"[+] Dataset saved to {DATASET_PATH}")
    
    manifest = build_manifest(df, near_duplicates)
    with open(SOURCE_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"[+] Source manifest saved to {SOURCE_MANIFEST_PATH}")

if __name__ == "__main__":
    main()
