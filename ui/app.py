# ui/app.py

"""
NeuroHealth Web Interface
--------------------------
User-facing web application built with Streamlit.

To run: streamlit run ui/app.py
Opens in browser at: http://localhost:8501
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
import html as html_module
import requests
from src.pipeline import process_message

API_BASE_URL = "http://localhost:8000/api/v1"

# ── PAGE CONFIGURATION ───────────────────────────────────────
st.set_page_config(
    page_title="NeuroHealth — AI Health Assistant",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ── STYLES ───────────────────────────────────────────────────
st.markdown("""
<style>
.urgency-emergency { background-color: #FFE5E5; border-left: 5px solid #FF0000; padding: 15px; border-radius: 5px; margin: 10px 0; }
.urgency-urgent    { background-color: #FFF3E5; border-left: 5px solid #FF6600; padding: 15px; border-radius: 5px; margin: 10px 0; }
.urgency-soon      { background-color: #FFFBE5; border-left: 5px solid #FFCC00; padding: 15px; border-radius: 5px; margin: 10px 0; }
.urgency-routine   { background-color: #E5FFE5; border-left: 5px solid #00CC00; padding: 15px; border-radius: 5px; margin: 10px 0; }
.urgency-self_care { background-color: #E5F0FF; border-left: 5px solid #0099FF; padding: 15px; border-radius: 5px; margin: 10px 0; }
.urgency-needs_clarification { background-color: #F5F5F5; border-left: 5px solid #999999; padding: 15px; border-radius: 5px; margin: 10px 0; }
.disclaimer-box { background-color: #f8f9fa; border: 1px solid #dee2e6; padding: 10px; border-radius: 5px; font-size: 0.85em; color: #6c757d; }

/* ── Mobile / Responsive Enhancements ──────────────── */
@media (max-width: 768px) {
    /* Make main content fullwidth on narrow screens */
    .block-container { padding-left: 1rem !important; padding-right: 1rem !important; max-width: 100% !important; }
    /* Stack sidebar on top for mobile */
    [data-testid="stSidebar"] { min-width: 100% !important; }
    /* Larger touch targets */
    .stButton > button { min-height: 48px; font-size: 1rem; }
    .stChatInput textarea { font-size: 16px !important; }  /* prevents iOS zoom */
    /* Reduce padding in urgency boxes */
    .urgency-emergency, .urgency-urgent, .urgency-soon,
    .urgency-routine, .urgency-self_care, .urgency-needs_clarification {
        padding: 10px; font-size: 0.95rem;
    }
}
/* Touch-friendly tap targets */
.stButton > button { touch-action: manipulation; }
</style>

<!-- PWA-ready viewport meta (Streamlit provides one but we reinforce) -->
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=5, user-scalable=yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="theme-color" content="#4A90D9">
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────
st.title("🧠 NeuroHealth")
st.markdown(
    "**AI-Powered Health Assistant** — RAG-powered symptom assessment, "
    "urgency triage, and appointment guidance."
)
st.divider()

# Emergency banner
st.error("🚨 If you are experiencing a life-threatening emergency, call **911** immediately.")

# ── SESSION STATE ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "satisfaction_log" not in st.session_state:
    st.session_state.satisfaction_log = []

# ── CHAT HISTORY ─────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant" and message.get("urgency_class"):
            safe_content = html_module.escape(message["content"])
            st.markdown(
                f'<div class="{message["urgency_class"]}">{safe_content}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(message["content"])

# ── CHAT INPUT ───────────────────────────────────────────────
if user_input := st.chat_input("Describe your symptoms or ask a health question..."):

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Process with NeuroHealth pipeline
    with st.chat_message("assistant"):
        with st.spinner("NeuroHealth is analyzing your message..."):
            try:
                result = process_message(
                    user_input,
                    session_id=st.session_state.session_id
                )

                # Save session ID for continuity
                st.session_state.session_id = result["session_id"]
                st.session_state.turn_count += 1

                # Display response
                response_text = result["response"]["text"]
                urgency_level = result["response"]["urgency_level"]

                # Color-coded urgency box
                VALID_URGENCY = {"emergency", "urgent", "soon", "routine", "self_care", "needs_clarification"}
                urgency_lower = urgency_level.lower() if urgency_level != "N/A" else ""
                urgency_class = f"urgency-{urgency_lower}" if urgency_lower in VALID_URGENCY else ""
                if urgency_class:
                    safe_text = html_module.escape(response_text)
                    st.markdown(
                        f'<div class="{urgency_class}">{safe_text}</div>',
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(response_text)

                # Store with urgency class for history rendering
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "urgency_class": urgency_class,
                })

                # Debug expander (for development)
                with st.expander("🔍 Debug Info", expanded=False):
                    debug = result.get("debug", {})
                    if debug:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Intent", debug.get("intent", {}).get("intent", "N/A"))
                        with col2:
                            st.metric("Urgency", debug.get("urgency", {}).get("level", "N/A"))
                        with col3:
                            symptom_count = len(debug.get("symptoms", {}).get("symptoms", []))
                            st.metric("Symptoms", symptom_count)
                        st.json(debug)

                # Satisfaction feedback widget
                with st.expander("📊 Rate this response", expanded=False):
                    sat_cols = st.columns([3, 1, 1])
                    with sat_cols[0]:
                        rating = st.slider(
                            "How helpful was this response?",
                            min_value=1, max_value=5, value=3,
                            key=f"rating_{st.session_state.turn_count}",
                            help="1 = Not helpful, 5 = Very helpful"
                        )
                    with sat_cols[1]:
                        thumbs = st.radio(
                            "Quick feedback",
                            options=["👍", "👎"],
                            horizontal=True,
                            key=f"thumbs_{st.session_state.turn_count}",
                        )
                    with sat_cols[2]:
                        if st.button("Submit", key=f"submit_{st.session_state.turn_count}"):
                            thumbs_val = "up" if thumbs == "👍" else "down"
                            feedback = {
                                "turn": st.session_state.turn_count,
                                "session_id": st.session_state.session_id,
                                "rating": rating,
                                "thumbs": thumbs_val,
                                "user_message": user_input[:100],
                                "urgency": urgency_level,
                            }
                            st.session_state.satisfaction_log.append(feedback)
                            # Send feedback to API (best-effort, don't break UI on failure)
                            try:
                                requests.post(
                                    f"{API_BASE_URL}/feedback",
                                    json={
                                        "session_id": st.session_state.session_id,
                                        "rating": rating,
                                        "thumbs": thumbs_val,
                                    },
                                    timeout=3,
                                )
                            except Exception:
                                pass  # API may not be running; feedback is still logged locally
                            st.success("Thank you for your feedback!")

            except Exception as e:
                error_msg = (
                    "⚠️ I encountered an error processing your message. "
                    "Please try again or rephrase your question.\n\n"
                    f"*Technical details: {str(e)[:200]}*"
                )
                st.markdown(error_msg)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_msg,
                })

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.header("🧠 About NeuroHealth")
    st.markdown("""
    **NeuroHealth** is an AI-powered health assistant built
    for the [OSRE 2026](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/)
    program at UC Santa Cruz.

    **Capabilities:**
    - 🔍 Symptom interpretation & extraction
    - 🚨 5-level urgency triage
    - 📚 RAG-powered medical knowledge retrieval
    - 🏥 Appointment & specialist recommendations
    - 🛡️ Multi-layer safety guardrails
    - 💬 Multi-turn conversation memory
    - 📊 Health literacy adaptation
    """)

    st.divider()

    st.subheader("Urgency Levels")
    st.markdown("""
    - 🔴 **Emergency** — Call 911
    - 🟠 **Urgent** — Urgent care today
    - 🟡 **Soon** — See doctor in 1-2 days
    - 🟢 **Routine** — Schedule appointment
    - 🔵 **Self-care** — Manage at home
    - ⚪ **Needs Info** — More details needed
    """)

    st.divider()

    # Session info
    if st.session_state.session_id:
        st.caption(f"Session: `{st.session_state.session_id}`")
        st.caption(f"Turns: {st.session_state.turn_count}")

    if st.button("🔄 Start New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.session_state.turn_count = 0
        st.rerun()

    st.divider()

    st.markdown(
        '<div class="disclaimer-box">'
        "⚕️ <b>Disclaimer:</b> NeuroHealth is NOT a substitute for "
        "professional medical advice, diagnosis, or treatment. Always seek "
        "the advice of your physician or other qualified health provider."
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.caption("Powered by Llama 3.1 + ChromaDB + MedlinePlus")
    st.caption("© 2026 Regents of the University of California | CC BY 4.0")
