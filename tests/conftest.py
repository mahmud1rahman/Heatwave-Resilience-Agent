import os
import json
import vertexai
from google.genai import types
from google.adk.models.llm_response import LlmResponse
from google.adk.models import Gemini
import google.auth
from unittest.mock import MagicMock

# Mock google.auth.default to return dummy credentials and project ID
mock_credentials = MagicMock()
google.auth.default = lambda *args, **kwargs: (mock_credentials, "community-heatwave-pilot")

# Set mock environment variables for local testing to bypass GCP auth checks
os.environ["GOOGLE_CLOUD_PROJECT"] = "community-heatwave-pilot"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
os.environ["GEMINI_API_KEY"] = "mock-api-key"
os.environ["GOOGLE_API_KEY"] = "mock-api-key"
os.environ["INTEGRATION_TEST"] = "TRUE"

# Initialize vertexai globally with mock project
vertexai.init(project="community-heatwave-pilot", location="us-central1")

# Mock the LLM content generation to prevent actual API calls during integration tests
async def mock_generate_content_async(self, llm_request, stream=False):
    response_text = ""
    # Check if there is a response schema in the request config
    if llm_request.config and getattr(llm_request.config, "response_schema", None):
        # Generate dummy content conforming to DispatchOutput Pydantic schema
        dummy_data = {
            "door_knocking_script": "Hello! I am a volunteer checking on residents due to the heatwave. Are you doing alright?",
            "safety_disclaimer": "This is a volunteer check. If you have medical concerns, contact NHS 111.",
            "volunteer_checklist": [
                "1. Introduce yourself.",
                "2. Ask how they are feeling.",
                "3. Check indoor temperature.",
                "4. Provide information about Leeds Central Library cooling hub."
            ],
            "reasoning_summary": "Resident is elderly in LS1 (Amber Alert). Checked on them to provide cooling hub options."
        }
        response_text = json.dumps(dummy_data)
    else:
        response_text = "Mock LLM Response"
        
    part = types.Part.from_text(text=response_text)
    candidate = types.Candidate(
        content=types.Content(role="model", parts=[part]),
        finish_reason=types.FinishReason.STOP
    )
    resp = types.GenerateContentResponse(
        candidates=[candidate],
        usage_metadata=types.GenerateContentResponseUsageMetadata()
    )
    
    yield LlmResponse.create(resp)

# Apply the mock to the Gemini class
Gemini.generate_content_async = mock_generate_content_async
