import json
import pytest
from app.tools import (
    _normalize_postcode,
    get_current_alert,
    find_cooling_hubs,
    fetch_safety_guidance,
    sanitize_and_validate_postcode,
    safety_filter
)
from app.agent import triage_node, HeatwaveWorkflowInput
from google.adk.events.request_input import RequestInput
from google.adk.events.event import Event
from google.adk.agents.context import Context
from unittest.mock import MagicMock, AsyncMock

def test_postcode_normalization():
    assert _normalize_postcode("ls1 3ab") == "LS1"
    assert _normalize_postcode("  BD1  ") == "BD1"
    assert _normalize_postcode("") == ""
    assert _normalize_postcode(None) == ""

def test_get_current_alert():
    # Valid postcode
    res = get_current_alert("LS1")
    assert res["status"] == "success"
    assert res["alert_level"] == "Amber"
    assert "guidelines" in res["details"].lower() or len(res["general_guidelines"]) > 0

    # Invalid postcode
    res_invalid = get_current_alert("XYZ")
    assert res_invalid["status"] == "error"
    assert "outside the West Yorkshire" in res_invalid["message"]

def test_find_cooling_hubs():
    hubs = find_cooling_hubs("LS1")
    assert len(hubs) > 0
    assert hubs[0]["name"] == "Leeds Central Library"

    hubs_invalid = find_cooling_hubs("XYZ")
    assert len(hubs_invalid) == 0

def test_fetch_safety_guidance():
    guidance = fetch_safety_guidance("elderly")
    assert guidance["status"] == "success"
    assert "Elderly" in guidance["vulnerability_type"]
    assert len(guidance["recommended_actions"]) > 0

    guidance_invalid = fetch_safety_guidance("unknown")
    assert guidance_invalid["status"] == "error"

@pytest.mark.asyncio
async def test_triage_node_valid():
    # Mock context
    ctx = MagicMock(spec=Context)
    ctx.resume_inputs = {}

    # Input with valid postcode
    node_input = HeatwaveWorkflowInput(postcode="LS1", vulnerability_type="elderly")
    
    events = []
    async for event in triage_node(ctx, node_input):
        events.append(event)
        
    assert len(events) == 1
    assert isinstance(events[0], Event)
    assert events[0].output["postcode"] == "LS1"
    assert events[0].output["alert_level"] == "Amber"

@pytest.mark.asyncio
async def test_triage_node_invalid_trigger_hitl():
    # Mock context
    ctx = MagicMock(spec=Context)
    ctx.resume_inputs = {}

    # Input with invalid postcode
    node_input = HeatwaveWorkflowInput(postcode="INVALID", vulnerability_type="elderly")
    
    events = []
    async for event in triage_node(ctx, node_input):
        events.append(event)
        
    assert len(events) == 1
    assert isinstance(events[0], RequestInput)
    assert events[0].interrupt_id == "corrected_postcode"
    assert "Please enter a valid postcode" in events[0].message

def test_postcode_regex_validation():
    # Valid formats
    assert sanitize_and_validate_postcode("LS1 3AB") == "LS1"
    assert sanitize_and_validate_postcode("bd1") == "BD1"
    assert sanitize_and_validate_postcode("  wf1   ") == "WF1"
    assert sanitize_and_validate_postcode("EC1A 2BB") == "EC1A"
    
    # Invalid formats (traversal / injection attempts)
    with pytest.raises(ValueError, match="Invalid postcode format"):
        sanitize_and_validate_postcode("../LS1")
    with pytest.raises(ValueError, match="Invalid postcode format"):
        sanitize_and_validate_postcode("LS1; DROP TABLE alerts")
    with pytest.raises(ValueError, match="Invalid postcode format"):
        sanitize_and_validate_postcode("")

def test_safety_filter_disclaimer():
    # Case: script already contains disclaimer
    script_with = "Hello! Please drink water. If someone shows signs of heatstroke (confusion, lack of sweat), call 999 immediately."
    res = safety_filter(script_with)
    assert res["valid"] is True
    assert res["script"] == script_with

    # Case: script is missing disclaimer
    script_without = "Hello! Please drink water."
    res = safety_filter(script_without)
    assert res["valid"] is False
    assert "If someone shows signs of heatstroke (confusion, lack of sweat), call 999 immediately." in res["script"]

