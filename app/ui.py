import asyncio
import json
import streamlit as st
from google.genai import types
from google.adk.events.request_input import RequestInput
from google.adk.events.event import Event
from app.agent import app, dispatch_agent
from google.adk.runners import InMemoryRunner

# Page Configuration
st.set_page_config(
    page_title="Community Heatwave Dispatch",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');

/* Apply custom fonts */
html, body, [class*="css"], [class*="st-"] {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
    font-family: 'Outfit', sans-serif;
    font-weight: 700;
}

/* Base Body Styling */
.stApp {
    background-color: #f8fafc;
}

/* Gradient Header with Animated Wave Effect */
.header-container {
    background: linear-gradient(135deg, #FF416C 0%, #FF4B2B 50%, #F09819 100%);
    background-size: 200% 200%;
    animation: gradientShift 15s ease infinite;
    padding: 3rem;
    border-radius: 20px;
    color: white;
    margin-bottom: 2.5rem;
    box-shadow: 0 20px 40px rgba(255, 75, 43, 0.15);
    position: relative;
    overflow: hidden;
}

@keyframes gradientShift {
    0% { background-position: 0% 50% }
    50% { background-position: 100% 50% }
    100% { background-position: 0% 50% }
}

.header-container h1 {
    margin: 0;
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    text-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.header-container p {
    margin: 0.75rem 0 0 0;
    font-size: 1.25rem;
    opacity: 0.95;
    font-weight: 300;
}

/* Sidebar Custom Styling */
[data-testid="stSidebar"] {
    background-color: #0f172a !important;
    border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #f8fafc !important;
}

[data-testid="stSidebar"] .stTextInput label, 
[data-testid="stSidebar"] .stSelectbox label {
    color: #cbd5e1 !important;
    font-weight: 600 !important;
}

/* Custom styled sidebar card */
.sidebar-info-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 1rem;
    margin-top: 2rem;
    font-size: 0.85rem;
    color: #94a3b8;
}

/* Primary Button Design */
div.stButton > button {
    background: linear-gradient(135deg, #FF4B2B 0%, #F09819 100%) !important;
    color: white !important;
    border: none !important;
    padding: 0.75rem 1.5rem !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    box-shadow: 0 4px 15px rgba(255, 75, 43, 0.3) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    width: 100% !important;
}

div.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(255, 75, 43, 0.45) !important;
}

/* Metric Card Layout */
.metric-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.03), 0 2px 4px -2px rgba(0, 0, 0, 0.03);
    border-left: 6px solid #e2e8f0;
    text-align: center;
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 20px -5px rgba(0, 0, 0, 0.05);
}

.metric-title {
    font-size: 0.85rem;
    color: #64748b;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

.metric-value {
    font-size: 1.8rem;
    font-weight: 800;
    color: #0f172a;
    font-family: 'Outfit', sans-serif;
    letter-spacing: -0.02em;
}

/* Hub Location Cards */
.hub-card {
    background: white;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.25rem;
    border: 1px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
    transition: all 0.2s ease-in-out;
}

.hub-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.06);
    border-color: #cbd5e1;
}

.hub-header {
    display: flex;
    align-items: center;
    margin-bottom: 0.75rem;
}

.hub-icon {
    font-size: 1.4rem;
    margin-right: 0.6rem;
}

.hub-title {
    font-weight: 700;
    font-size: 1.15rem;
    color: #0f172a;
}

.hub-details p {
    margin: 0.4rem 0;
    font-size: 0.95rem;
    color: #475569;
}

.facility-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.75rem;
}

.facility-badge {
    background: #f1f5f9;
    color: #475569;
    padding: 0.3rem 0.6rem;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    border: 1px solid #e2e8f0;
}

/* Teleprompter Script Container */
.teleprompter-container {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
}

.teleprompter-header {
    display: flex;
    align-items: center;
    font-weight: 700;
    font-size: 1.1rem;
    color: #166534;
    margin-bottom: 0.75rem;
    font-family: 'Outfit', sans-serif;
}

.script-box {
    background-color: #f0fdf4;
    border-left: 6px solid #22c55e;
    padding: 1.75rem;
    border-radius: 8px;
    font-size: 1.05rem;
    line-height: 1.7;
    color: #14532d;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.01);
    margin-bottom: 1.5rem;
}

/* Disclaimer / Warning Box */
.disclaimer-box {
    background-color: #fffbeb;
    border-left: 6px solid #f59e0b;
    padding: 1.5rem;
    border-radius: 8px;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #78350f;
    margin-bottom: 1.5rem;
    border: 1px solid #fef3c7;
}

/* Checkbox Cards */
div[data-testid="stCheckbox"] {
    background-color: white;
    padding: 0.9rem 1.25rem;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    margin-bottom: 0.6rem;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.01);
    transition: all 0.2s ease;
}

div[data-testid="stCheckbox"]:hover {
    background-color: #f8fafc;
    border-color: #cbd5e1;
    transform: translateX(3px);
}

/* Expander/Details Custom Styling */
details {
    background-color: white !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    margin-bottom: 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.02) !important;
}

summary {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important;
    padding: 1rem !important;
    color: #0f172a !important;
}
</style>

""", unsafe_allow_html=True)

# Shared services cache to maintain sessions/memory across Streamlit runs
@st.cache_resource
def get_shared_services():
    from google.adk.sessions.in_memory_session_service import InMemorySessionService
    from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
    return InMemorySessionService(), InMemoryMemoryService()

def get_runner():
    # Instantiate a fresh runner to prevent asyncio loop bound conflicts
    session_service, memory_service = get_shared_services()
    runner = InMemoryRunner(app=app)
    runner.session_service = session_service
    runner.memory_service = memory_service
    return runner

# Helper to run async generator in Streamlit
def run_workflow(postcode, vulnerability_type, resume_value=None, interrupt_id=None):
    # Reset cached properties on global model instances to force recreating
    # client/sessions on the current active event loop.
    model = dispatch_agent.model
    for prop in ["api_client", "_api_backend", "_base_url_and_api_version", "_live_api_version", "_live_api_client"]:
        if prop in model.__dict__:
            del model.__dict__[prop]

    runner = get_runner()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Build the message
    if resume_value and interrupt_id:
        new_message = types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        name=interrupt_id,
                        id=interrupt_id,
                        response={"output": resume_value}
                    )
                )
            ]
        )
        invocation_id = st.session_state.invocation_id
    else:
        input_data = {
            "postcode": postcode,
            "vulnerability_type": vulnerability_type
        }
        new_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=json.dumps(input_data))]
        )
        session = loop.run_until_complete(
            runner.session_service.create_session(
                app_name="app",
                user_id="streamlit_user"
            )
        )
        st.session_state.session_id = session.id
        st.session_state.invocation_id = None
        st.session_state.trace_logs = []
        invocation_id = None

    events = []
    active_interrupt = None
    
    async def drive():
        nonlocal active_interrupt
        async for event in runner.run_async(
            user_id="streamlit_user",
            session_id=st.session_state.session_id,
            invocation_id=invocation_id,
            new_message=new_message
        ):
            events.append(event)
            # Store event types in trace logs
            log_msg = f"**Node:** `{event.node_info.path or 'System'}` | **Author:** `{event.author}`"
            if event.partial:
                log_msg += " (Streaming...)"
            st.session_state.trace_logs.append(log_msg)
            
            if isinstance(event, RequestInput):
                active_interrupt = event
                st.session_state.invocation_id = event.invocation_id
            elif isinstance(event, Event) and event.invocation_id:
                st.session_state.invocation_id = event.invocation_id

    loop.run_until_complete(drive())
    loop.close()
    return events, active_interrupt

# App Header
st.markdown("""
<div class="header-container">
    <h1>☀️ community-heatwave-agent</h1>
    <p>ADK 2.0 Clinically-Guided Heat-Health Dispatch Portal & Volunteer Action Center</p>
</div>
""", unsafe_allow_html=True)

# Main layout split into Sidebar and Content area
with st.sidebar:
    st.markdown("### 🛠️ Campaign Configuration")
    postcode_input = st.text_input("Enter Target UK Postcode:", value="LS1", help="E.g., LS1, BD1, WF1, HD1, HX1")
    vulnerability_select = st.selectbox(
        "Select Vulnerability Profile:",
        options=["elderly", "infants", "chronic_illness"],
        format_func=lambda x: {
            "elderly": "Elderly (65+ years)",
            "infants": "Infants & Young Children",
            "chronic_illness": "Chronic Illness (Heart/Lung/Kidney)"
        }.get(x, x)
    )
    
    st.markdown("---")
    submit_btn = st.button("🔥 Generate Volunteer Checklist", use_container_width=True)
    
    st.markdown("""
    <div class="sidebar-info-card">
        <strong>💡 Dispatch Best Practices</strong><br>
        • Verify postcode belongs to Yorkshire pilot zones.<br>
        • Select profile to adapt dialogue and checklist actions.<br>
        • Instruct volunteer to report any clinical emergency to 999.
    </div>
    """, unsafe_allow_html=True)


# State Management Initialization
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "invocation_id" not in st.session_state:
    st.session_state.invocation_id = None
if "active_interrupt" not in st.session_state:
    st.session_state.active_interrupt = None
if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = []
if "events" not in st.session_state:
    st.session_state.events = None

# Handle fresh run request
if submit_btn:
    st.session_state.active_interrupt = None
    with st.spinner("Executing ADK 2.0 Multi-Agent Workflow..."):
        events, interrupt = run_workflow(postcode_input, vulnerability_select)
        st.session_state.events = events
        st.session_state.active_interrupt = interrupt

# Handle active HITL validation interrupt
if st.session_state.active_interrupt:
    st.markdown(f"""
    <div class="disclaimer-box" style="border-left-color: #3b82f6; background-color: #eff6ff; color: #1e3a8a;">
        <strong>⚠️ Validation Action Required (Human-in-the-Loop Interruption)</strong><br>
        {st.session_state.active_interrupt.message}
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("resume_form"):
        corrected_val = st.text_input("Please enter corrected postcode:", value="")
        resume_btn = st.form_submit_button("Resume Workflow")
        
        if resume_btn and corrected_val:
            with st.spinner("Resuming Workflow with updated inputs..."):
                st.session_state.active_interrupt = None
                events, interrupt = run_workflow(
                    None, None,
                    resume_value=corrected_val,
                    interrupt_id="corrected_postcode"
                )
                st.session_state.events = events
                st.session_state.active_interrupt = interrupt
                st.rerun()

# Display Results & Reasoning
if st.session_state.events:
    # 2. Extract final output schema

    final_output = None
    alert_level = "Unknown"
    hubs = []
    
    # Traverse events to extract results
    for e in st.session_state.events:
        if not e.partial:
            # Check state changes or final output
            if e.actions and e.actions.state_delta:
                if "alert_level" in e.actions.state_delta:
                    alert_level = e.actions.state_delta["alert_level"]
                if "cooling_hubs" in e.actions.state_delta:
                    try:
                        hubs = json.loads(e.actions.state_delta["cooling_hubs"])
                    except Exception:
                        pass
            if e.output:
                # If this is the final DispatchOutput
                if isinstance(e.output, dict) and "door_knocking_script" in e.output:
                    final_output = e.output
                elif hasattr(e.output, "door_knocking_script"):
                    final_output = e.output.__dict__

    # UI Badge and Theme Configuration
    if alert_level == "Red":
        alert_color = "#ef4444"
        alert_bg = "#fee2e2"
        alert_border = "#fca5a5"
        alert_text = "#991b1b"
        alert_glow = "rgba(239, 68, 68, 0.2)"
    elif alert_level == "Amber":
        alert_color = "#f97316"
        alert_bg = "#ffedd5"
        alert_border = "#fed7aa"
        alert_text = "#c2410c"
        alert_glow = "rgba(249, 115, 22, 0.2)"
    elif alert_level == "Yellow":
        alert_color = "#eab308"
        alert_bg = "#fef9c3"
        alert_border = "#fef08a"
        alert_text = "#854d0e"
        alert_glow = "rgba(234, 179, 8, 0.2)"
    else:  # Green
        alert_color = "#22c55e"
        alert_bg = "#dcfce7"
        alert_border = "#86efac"
        alert_text = "#166534"
        alert_glow = "rgba(34, 197, 94, 0.2)"

    # Top Level Metrics Dashboard Row
    m_col1, m_col2, m_col3 = st.columns(3)
    
    with m_col1:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 6px solid #3b82f6;">
            <div class="metric-title">📍 Target Postcode</div>
            <div class="metric-value">{postcode_input.upper().strip()}</div>
        </div>
        """, unsafe_allow_html=True)

    with m_col2:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 6px solid {alert_color}; box-shadow: 0 4px 20px {alert_glow};">
            <div class="metric-title">⚠️ UKHSA Alert Level</div>
            <div class="metric-value" style="color: {alert_text}; background-color: {alert_bg}; padding: 0.2rem 1rem; border-radius: 20px; font-size: 1.3rem; display: inline-block; font-weight: 700; border: 1px solid {alert_border}; margin-top: 0.25rem;">
                {alert_level}
            </div>
        </div>
        """, unsafe_allow_html=True)

    vulnerability_labels = {
        "elderly": "Elderly (65+ years)",
        "infants": "Infants & Young Children",
        "chronic_illness": "Chronic Illness"
    }
    v_label = vulnerability_labels.get(vulnerability_select, vulnerability_select.capitalize())

    with m_col3:
        st.markdown(f"""
        <div class="metric-card" style="border-left: 6px solid #8b5cf6;">
            <div class="metric-title">👥 Vulnerability Group</div>
            <div class="metric-value" style="font-size: 1.3rem; margin-top: 0.25rem; font-weight: 700; color: #5b21b6;">
                {v_label}
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacer

    # Display active conditions
    col1, col2 = st.columns([1, 2])
    with col1:
        # Display cooling hubs
        st.markdown("### 📍 Local Cooling Hubs")
        if hubs:
            for h in hubs:
                facilities_html = "".join([f'<span class="facility-badge">{f}</span>' for f in h.get('facilities', [])])
                st.markdown(f"""
                <div class="hub-card">
                    <div class="hub-header">
                        <span class="hub-icon">🏢</span>
                        <span class="hub-title">{h.get('name', 'Unknown Hub')}</span>
                    </div>
                    <div class="hub-details">
                        <p>📍 {h.get('address', '')}</p>
                        <p>🕒 {h.get('opening_hours', '')}</p>
                    </div>
                    <div class="facility-container">
                        {facilities_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="hub-card" style="text-align: center; padding: 2rem;">
                <span style="font-size: 2rem;">📍</span>
                <h4 style="margin-top: 0.5rem; color: #64748b;">No Cooling Hubs Configured</h4>
                <p style="font-size: 0.9rem; color: #94a3b8;">No hubs are registered for this postcode zone in the active playbook.</p>
            </div>
            """, unsafe_allow_html=True)

    with col2:
        if final_output:
            st.markdown("### 📋 Clinically-Guided Volunteer Action Pack")
            
            # Clinical Rationale
            with st.expander("🔬 View Clinical & Operational Rationale", expanded=True):
                st.write(final_output.get("reasoning_summary", "No rationale summary available."))
                
            # Door Knocking Script
            st.markdown("#### 🗣️ Door-Knocking Conversation Script")
            st.markdown(f"""
            <div class="script-box">
                <div style="font-size: 0.85rem; font-weight: bold; text-transform: uppercase; color: #166534; margin-bottom: 0.5rem; letter-spacing: 0.05em; display: flex; align-items: center;">
                    <span style="margin-right: 0.4rem;">💬</span> Volunteer Speech Script
                </div>
                {final_output.get("door_knocking_script", "").replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
            
            # Safety Disclaimer
            st.markdown("#### ⚠️ Volunteer Safety Disclaimer")
            st.markdown(f"""
            <div class="disclaimer-box">
                <div style="font-size: 0.85rem; font-weight: bold; text-transform: uppercase; color: #92400e; margin-bottom: 0.5rem; letter-spacing: 0.05em; display: flex; align-items: center;">
                    <span style="margin-right: 0.4rem;">⚠️</span> Important Safety Guardrails
                </div>
                {final_output.get("safety_disclaimer", "").replace(chr(10), "<br>")}
            </div>
            """, unsafe_allow_html=True)
            
            # Action Checklist
            st.markdown("#### 🎯 Visit Checklist")
            checklist = final_output.get("volunteer_checklist", [])
            for item in checklist:
                st.checkbox(item, key=f"chk_{item[:30]}")
        else:
            st.info("Agent is preparing the dispatch script and checklist...")

