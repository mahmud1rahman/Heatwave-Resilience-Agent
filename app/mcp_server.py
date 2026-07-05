import json
from mcp.server.fastmcp import FastMCP
from app.tools import (
    sanitize_and_validate_postcode,
    get_current_alert as local_get_current_alert,
    find_cooling_hubs as local_find_cooling_hubs,
    fetch_safety_guidance as local_fetch_safety_guidance,
    safety_filter as local_safety_filter
)

mcp = FastMCP("community-heatwave-mcp")

@mcp.tool()
def get_current_alert(postcode: str) -> dict:
    """Retrieve the official UKHSA alert level and general guidelines for a UK postcode.

    Args:
        postcode: The UK postcode area (e.g., 'LS1', 'BD1').
    """
    # Force sanitisation and validation
    sanitize_and_validate_postcode(postcode)
    return local_get_current_alert(postcode)

@mcp.tool()
def find_cooling_hubs(postcode: str) -> list:
    """Find localized air-conditioned cooling hubs (libraries, community centers) for a UK postcode.

    Args:
        postcode: The UK postcode area (e.g., 'LS1', 'BD1').
    """
    # Force sanitisation and validation
    sanitize_and_validate_postcode(postcode)
    return local_find_cooling_hubs(postcode)

@mcp.tool()
def fetch_safety_guidance(vulnerability_type: str) -> dict:
    """Fetch official UKHSA clinical safety guidance, risks, actions, and red flags for a vulnerability type.

    Args:
        vulnerability_type: The category of vulnerability ('elderly', 'infants', 'chronic_illness').
    """
    return local_fetch_safety_guidance(vulnerability_type)

@mcp.tool()
def safety_filter(script: str) -> dict:
    """Scans the generated volunteer script to ensure it explicitly includes the mandatory safety disclaimer.

    Args:
        script: The volunteer speech script to scan.
    """
    return local_safety_filter(script)

if __name__ == "__main__":
    mcp.run()
