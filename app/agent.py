# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from typing import AsyncGenerator
import google.auth
from pydantic import BaseModel, Field

from google.adk.agents import LlmAgent
from google.adk.agents.context import Context
from google.adk.apps import App
from google.adk.events.event import Event
from google.adk.events.request_input import RequestInput
from google.adk.models import Gemini
from google.adk.workflow import Workflow, START
from google.genai import types

# Set up project environment
from dotenv import load_dotenv
load_dotenv()

try:
    _, project_id = google.auth.default()
    os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    pass

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

# Fallback to Developer API key if GEMINI_API_KEY is provided
if os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# Import mock tools
from .tools import get_current_alert, find_cooling_hubs, fetch_safety_guidance, safety_filter, sanitize_and_validate_postcode

# Define Schema Models
class HeatwaveWorkflowInput(BaseModel):
    postcode: str = Field(description="The UK postcode area (e.g. LS1, BD1, WF1)")
    vulnerability_type: str = Field(description="The vulnerability type: elderly, infants, or chronic_illness")

class DispatchOutput(BaseModel):
    door_knocking_script: str = Field(description="Tailored door-knocking script for the volunteer based on the alert level and resident type.")
    safety_disclaimer: str = Field(description="Safety disclaimer to ensure volunteers protect themselves and residents.")
    volunteer_checklist: list[str] = Field(description="A step-by-step checklist of actions the volunteer should take at the door.")
    reasoning_summary: str = Field(description="Brief summary of the clinical and operational rationale behind this dispatch strategy.")

# Node 1: Ingest & Triage Node (function node)
async def triage_node(ctx: Context, node_input: HeatwaveWorkflowInput) -> AsyncGenerator[Event, None]:
    supported_postcodes = {"LS1", "BD1", "WF1", "HD1", "HX1"}
    
    try:
        postcode = sanitize_and_validate_postcode(node_input.postcode)
    except ValueError as e:
        yield RequestInput(
            interrupt_id="corrected_postcode",
            message=f"{str(e)} Supported pilot areas: {', '.join(supported_postcodes)}. Please enter a valid postcode:"
        )
        return
    
    if postcode not in supported_postcodes:
        # Check if the user has provided a corrected postcode via resume inputs
        if not ctx.resume_inputs or "corrected_postcode" not in ctx.resume_inputs:
            # Yield RequestInput to pause and ask for input
            yield RequestInput(
                interrupt_id="corrected_postcode",
                message=f"Postcode '{node_input.postcode}' is not supported. Supported pilot areas: {', '.join(supported_postcodes)}. Please enter a valid postcode:"
            )
            return
            
        # Retrieve the corrected postcode
        raw_corrected = ctx.resume_inputs["corrected_postcode"]
        if isinstance(raw_corrected, dict):
            corrected_str = raw_corrected.get("output", "") or raw_corrected.get("corrected_postcode", "") or next(iter(raw_corrected.values()), "")
        else:
            corrected_str = str(raw_corrected)
            
        try:
            corrected = sanitize_and_validate_postcode(corrected_str)
        except ValueError as e:
            yield RequestInput(
                interrupt_id="corrected_postcode",
                message=f"{str(e)} Supported pilot areas: {', '.join(supported_postcodes)}. Please try again:"
            )
            return

        if corrected not in supported_postcodes:
            # Still not supported, yield RequestInput again
            yield RequestInput(
                interrupt_id="corrected_postcode",
                message=f"The corrected postcode '{corrected_str}' is also not supported. Supported pilot areas: {', '.join(supported_postcodes)}. Please try again:"
            )
            return
        postcode = corrected


    # Call get_current_alert tool
    alert_info = get_current_alert(postcode)
    
    yield Event(
        output={
            "postcode": postcode,
            "vulnerability_type": node_input.vulnerability_type,
            "alert_level": alert_info.get("alert_level", "Unknown"),
            "alert_details": alert_info
        },
        state={
            "postcode": postcode,
            "vulnerability_type": node_input.vulnerability_type,
            "alert_level": alert_info.get("alert_level", "Unknown"),
            "alert_details": json.dumps(alert_info)
        }
    )

# Node 2: Strategy Node (function node)
async def strategy_node(ctx: Context, node_input: dict) -> AsyncGenerator[Event, None]:
    postcode = node_input["postcode"]
    vulnerability_type = node_input["vulnerability_type"]
    
    # Call the tools
    cooling_hubs = find_cooling_hubs(postcode)
    safety_guidance = fetch_safety_guidance(vulnerability_type)
    
    yield Event(
        output={
            "cooling_hubs": cooling_hubs,
            "safety_guidance": safety_guidance
        },
        state={
            "cooling_hubs": json.dumps(cooling_hubs),
            "safety_guidance": json.dumps(safety_guidance)
        }
    )

# Node 3: Volunteer Dispatch Agent (LlmAgent)
dispatch_agent = LlmAgent(
    name="dispatch_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction="""You are a Volunteer Dispatch Agent for a public health heatwave response campaign in West Yorkshire.
Your task is to prepare a tailored door-knocking script, a safety disclaimer, and a concrete action checklist for a volunteer visiting a vulnerable resident.

Context:
- Target Postcode: {postcode}
- Resident Vulnerability Category: {vulnerability_type}
- Active UKHSA Heat-Health Alert Level: {alert_level}
- UKHSA Alert Guidelines: {alert_details}
- Nearby Cooling Hubs: {cooling_hubs}
- Clinically-Tailored Safety Guidance: {safety_guidance}

Based on this context:
1. Provide a clear reasoning summary of the clinical and operational rationale behind your dispatch strategy.
2. Write a highly tailored door-knocking script that the volunteer should use when speaking to the resident (e.g. friendly tone, specifically addressing their vulnerability type and the active alert level).
3. Create a clear safety disclaimer for the volunteer's own safety and bounds of their support (e.g., they are not medical professionals).
4. Provide a step-by-step checklist of actions the volunteer should perform at the resident's home.

Ensure all outputs are structured exactly according to the output schema.
""",
    output_schema=DispatchOutput,
    output_key="dispatch_output"
)

# Node 4: Safety Guardrail Node (function node)
async def safety_guardrail_node(ctx: Context, node_input: DispatchOutput) -> AsyncGenerator[Event, None]:
    # Call the safety filter tool/function
    filter_result = safety_filter(node_input.door_knocking_script)
    sanitized_script = filter_result["script"]
    
    # Reconstruct the output with the guaranteed safety disclaimer
    final_output = DispatchOutput(
        door_knocking_script=sanitized_script,
        safety_disclaimer=node_input.safety_disclaimer,
        volunteer_checklist=node_input.volunteer_checklist,
        reasoning_summary=node_input.reasoning_summary
    )
    
    yield Event(
        output=final_output,
        state={
            "door_knocking_script": sanitized_script
        }
    )

# Workflow Graph Topology
root_agent = Workflow(
    name="community_heatwave_workflow",
    input_schema=HeatwaveWorkflowInput,
    output_schema=DispatchOutput,
    edges=[
        (START, triage_node),
        (triage_node, strategy_node),
        (strategy_node, dispatch_agent),
        (dispatch_agent, safety_guardrail_node)
    ]
)

app = App(
    root_agent=root_agent,
    name="app"
)
