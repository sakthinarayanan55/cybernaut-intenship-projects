"""
Safe URL and Text Sanitizer / Defanger
Ensures NFR-01 (Never click, fetch or execute suspicious content)
Ensures NFR-02 (No real credentials or PII)
"""
import re
import json
from typing import Dict, Any, List
from urllib.parse import urlparse
from src.config import SUSPICIOUS_TLDS

# URL regex matching both normal and already defanged URLs
RAW_URL_PATTERN = re.compile(
    r'(https?://[^\s<>"\',]+|www\.[^\s<>"\',]+)',
    re.IGNORECASE
)

DEFANGED_URL_PATTERN = re.compile(
    r'(hxxps?://[^\s<>"\',]+|hxxps?\[:\]//[^\s<>"\',]+|[a-zA-Z0-9_\-\.]+\[\.\][a-zA-Z0-9_\-\./]+)',
    re.IGNORECASE
)

IP_PATTERN = re.compile(
    r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
)

SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "goo.gl", "ow.ly", "t.co", "is.gd", "buff.ly", "cutt.ly"
}

def defang_url(url: str) -> str:
    """
    Renders a URL inert so it cannot be accidentally clicked or resolved.
    http:// -> hxxp[:]//
    https:// -> hxxps[:]//
    . -> [.]
    """
    if not url:
        return ""
    # If already defanged, normalize
    cleaned = url
    cleaned = re.sub(r'^https?://', lambda m: m.group(0).replace('http', 'hxxp') + '[:]', cleaned)
    cleaned = cleaned.replace('[:]//', '[:]//') if '[:]//' in cleaned else cleaned.replace('//', '[:]//')
    # Replace dots in domain
    parts = cleaned.split('[:]/', 1)
    if len(parts) == 2:
        proto_part = parts[0] + '[:]'
        rest = parts[1]
        rest = rest.replace('.', '[.]')
        return proto_part + rest
    return cleaned.replace('.', '[.]')

def refang_for_analysis_only(defanged: str) -> str:
    """
    Internal lexical refanging solely for URL parsing/string inspection.
    NEVER sends network requests or executes.
    """
    s = defanged
    s = s.replace('hxxps[:]//', 'https://')
    s = s.replace('hxxp[:]//', 'http://')
    s = s.replace('hxxps://', 'https://')
    s = s.replace('hxxp://', 'http://')
    s = s.replace('[.]', '.')
    s = s.replace('[:]', ':')
    if not s.startswith(('http://', 'https://')):
        s = 'http://' + s
    return s

def extract_sanitized_url_features(text: str) -> Dict[str, Any]:
    """
    Extracts structural metadata from URLs found in text without opening them.
    Returns JSON-serializable dictionary conforming to SRS Section 05.
    """
    if not isinstance(text, str):
        return {
            "has_url": False,
            "url_count": 0,
            "is_defanged": True,
            "primary_domain": None,
            "primary_tld": None,
            "is_suspicious_tld": False,
            "has_ip_host": False,
            "is_shortener": False,
            "num_subdomains": 0,
            "has_at_symbol": False,
            "extracted_urls": []
        }

    # Find raw and defanged matches
    raw_matches = RAW_URL_PATTERN.findall(text)
    defanged_matches = DEFANGED_URL_PATTERN.findall(text)
    
    all_raw_urls = list(set(raw_matches + defanged_matches))
    url_count = len(all_raw_urls)
    
    if url_count == 0:
        return {
            "has_url": False,
            "url_count": 0,
            "is_defanged": True,
            "primary_domain": None,
            "primary_tld": None,
            "is_suspicious_tld": False,
            "has_ip_host": False,
            "is_shortener": False,
            "num_subdomains": 0,
            "has_at_symbol": False,
            "extracted_urls": []
        }

    extracted_defanged = []
    primary_domain = None
    primary_tld = None
    is_suspicious_tld = False
    has_ip = False
    is_shortener = False
    max_subdomains = 0
    has_at_symbol = False

    for item in all_raw_urls:
        defanged = defang_url(item)
        extracted_defanged.append(defanged)
        
        # Analyze safely using string manipulation & standard urlparse on inert string
        analyzable = refang_for_analysis_only(defanged)
        try:
            parsed = urlparse(analyzable)
            netloc = parsed.netloc.lower().split(':')[0]
            
            if '@' in parsed.netloc or '@' in item:
                has_at_symbol = True
                
            if IP_PATTERN.match(netloc):
                has_ip = True
                primary_domain = netloc
            elif netloc:
                parts = netloc.split('.')
                tld = parts[-1] if len(parts) > 1 else ""
                if not primary_tld:
                    primary_tld = tld
                if not primary_domain:
                    primary_domain = netloc
                if tld in SUSPICIOUS_TLDS:
                    is_suspicious_tld = True
                if netloc in SHORTENER_DOMAINS:
                    is_shortener = True
                max_subdomains = max(max_subdomains, max(0, len(parts) - 2))
        except Exception:
            pass

    return {
        "has_url": True,
        "url_count": url_count,
        "is_defanged": True,
        "primary_domain": primary_domain,
        "primary_tld": primary_tld,
        "is_suspicious_tld": is_suspicious_tld,
        "has_ip_host": has_ip,
        "is_shortener": is_shortener,
        "num_subdomains": max_subdomains,
        "has_at_symbol": has_at_symbol,
        "extracted_urls": extracted_defanged
    }

def sanitize_and_defang_text(text: str) -> str:
    """
    Replaces all live URLs with defanged variants in text.
    Also strips any accidental live IP or protocol links.
    """
    if not isinstance(text, str):
        return ""
    
    def _replace_url(match):
        raw = match.group(0)
        return defang_url(raw)
        
    sanitized = RAW_URL_PATTERN.sub(_replace_url, text)
    return sanitized
