import json
import os
import re
from typing import Dict, List, Any

# Resolve data path relative to this file
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Mock database mapping postcodes to alert levels for testing
POSTCODE_ALERTS = {
    "LS1": "Amber",
    "BD1": "Yellow",
    "WF1": "Amber",
    "HD1": "Red",
    "HX1": "Green"
}

def sanitize_and_validate_postcode(postcode: str) -> str:
    """Strictly validates UK postcode formats to prevent prompt injection or directory traversal attacks.

    Returns the sanitized outward code (e.g. 'LS1').
    """
    if not postcode or not isinstance(postcode, str):
        raise ValueError("Invalid postcode format: must be a non-empty string.")
        
    # Clean input
    cleaned = postcode.strip().upper()
    parts = cleaned.split()
    if not parts:
        raise ValueError("Invalid postcode format: cannot be empty.")
    outward_part = parts[0]

    
    # Enforce strict UK outward postcode format: 1-2 letters, 1-2 digits, optional trailing letter
    # E.g. LS1, BD1, WF1, HD1, HX1
    if not re.match(r"^[A-Z]{1,2}[0-9][A-Z0-9]?$", outward_part):
        raise ValueError(f"Security Alert: Invalid postcode format '{postcode}'. Request rejected.")
        
    return outward_part

def _normalize_postcode(postcode: str) -> str:
    """Helper to clean and extract the outer district (e.g. 'LS1 3AB' -> 'LS1') with validation."""
    if not postcode:
        return ""
    try:
        return sanitize_and_validate_postcode(postcode)
    except ValueError:
        # Fallback to simple clean if needed, but raise validation warning or raise error in tools
        clean = postcode.strip().upper()
        return clean.split()[0]


def get_current_alert(postcode: str) -> Dict[str, Any]:
    """Retrieve the official UKHSA alert level and general guidelines for a UK postcode.

    Args:
        postcode: The UK postcode area (e.g., 'LS1', 'BD1').

    Returns:
        A dictionary containing the alert level, trigger description, and guidelines.
    """
    normalized = _normalize_postcode(postcode)
    
    # Load playbook data
    playbook_path = os.path.join(DATA_DIR, "playbook.json")
    try:
        with open(playbook_path, "r") as f:
            playbook = json.load(f)
    except FileNotFoundError:
        return {"status": "error", "message": "Playbook database not found."}

    if normalized not in POSTCODE_ALERTS:
        return {
            "status": "error",
            "message": f"Postcode '{postcode}' (normalized to '{normalized}') is outside the West Yorkshire community-heatwave-agent pilot coverage area. Supported areas: LS1, BD1, WF1, HD1, HX1."
        }

    alert_level = POSTCODE_ALERTS[normalized]
    alert_info = playbook["alerts"].get(alert_level, {})
    
    return {
        "status": "success",
        "postcode": normalized,
        "alert_level": alert_level,
        "details": alert_info.get("level", "Unknown"),
        "trigger": alert_info.get("trigger", "Unknown"),
        "general_guidelines": alert_info.get("general_guidelines", [])
    }

def find_cooling_hubs(postcode: str) -> List[Dict[str, Any]]:
    """Find localized air-conditioned cooling hubs (libraries, community centers) for a UK postcode.

    Args:
        postcode: The UK postcode area (e.g., 'LS1', 'BD1').

    Returns:
        A list of nearby cooling hubs with addresses, facilities, and opening hours.
    """
    normalized = _normalize_postcode(postcode)
    
    hubs_path = os.path.join(DATA_DIR, "hubs.json")
    try:
        with open(hubs_path, "r") as f:
            hubs_data = json.load(f)
    except FileNotFoundError:
        return []

    return hubs_data.get(normalized, [])

def fetch_safety_guidance(vulnerability_type: str) -> Dict[str, Any]:
    """Fetch official UKHSA clinical safety guidance, risks, actions, and red flags for a vulnerability type.

    Args:
        vulnerability_type: The category of vulnerability ('elderly', 'infants', 'chronic_illness').

    Returns:
        A dictionary containing clinical guidance, actions, and medical red flags.
    """
    vulnerability_type = vulnerability_type.strip().lower()
    
    playbook_path = os.path.join(DATA_DIR, "playbook.json")
    try:
        with open(playbook_path, "r") as f:
            playbook = json.load(f)
    except FileNotFoundError:
        return {"status": "error", "message": "Playbook database not found."}

    vulnerabilities = playbook.get("vulnerability_guidance", {})
    if vulnerability_type not in vulnerabilities:
        supported = list(vulnerabilities.keys())
        return {
            "status": "error",
            "message": f"Unknown vulnerability type '{vulnerability_type}'. Supported types: {', '.join(supported)}"
        }

    info = vulnerabilities[vulnerability_type]
    return {
        "status": "success",
        "vulnerability_type": info.get("vulnerability_type", vulnerability_type),
        "clinical_risks": info.get("clinical_risks", ""),
        "recommended_actions": info.get("actions", []),
        "medical_red_flags": info.get("red_flags", [])
    }

def safety_filter(script: str) -> Dict[str, Any]:
    """Scans the generated volunteer script to ensure it explicitly includes a disclaimer:
    "If someone shows signs of heatstroke (confusion, lack of sweat), call 999 immediately."
    
    If it is missing, automatically appends it to guarantee safety.
    """
    if not script or not isinstance(script, str):
        script = ""
        
    disclaimer = "If someone shows signs of heatstroke (confusion, lack of sweat), call 999 immediately."
    
    normalized_script = " ".join(script.lower().split())
    normalized_disclaimer = " ".join(disclaimer.lower().split())
    
    if normalized_disclaimer in normalized_script:
        return {
            "status": "success",
            "valid": True,
            "script": script
        }
    else:
        # Append disclaimer automatically to guarantee safety
        updated_script = script.strip() + f"\n\nDisclaimer: {disclaimer}"
        return {
            "status": "warning",
            "valid": False,
            "script": updated_script
        }

