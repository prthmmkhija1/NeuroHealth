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
from src.pipeline import process_message

# ── PAGE CONFIGURATION ───────────────────────────────────────
st.set_page_config(
    page_title="NeuroHealth",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ── STYLES ───────────────────────────────────────────────────
st.markdown("""
<style>
.urgency-emergency { background-color: #FFE5E5; border-left: 5px solid #FF0000; padding: 10px; }
.urgency-urgent    { background-color: #FFF3E5; border-left: 5px solid #FF6600; padding: 10px; }
.urgency-soon      { background-color: #FFFBE5; border-left: 5px solid #FFCC00; padding: 10px; }
.urgency-routine   { background-color: #E5FFE5; border-left: 5px solid #00CC00; padding: 10px; }
.urgency-self_care { background-color: #E5F0FF; border-left: 5px solid #0099FF; padding: 10px; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────────
st.title("🧠 NeuroHealth")
st.markdown("**AI-Powered Health Assistant** | *Not a substitute for professional medical advice*")
st.divider()

# Emergency banner
st.error("🚨 If you are experiencing a life-threatening emergency, call **911** immediately.")

# ── SESSION STATE ─────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = None

# ── CHAT HISTORY ─────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ── CHAT INPUT ───────────────────────────────────────────────
if user_input := st.chat_input("Describe your symptoms or ask a health question..."):

    # Show user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Process with NeuroHealth pipeline
    with st.chat_message("assistant"):
        with st.spinner("NeuroHealth is thinking..."):
            result = process_message(
                user_input,
                session_id=st.session_state.session_id
            )

        # Save session ID for continuity
        st.session_state.session_id = result["session_id"]

        # Display response
        response_text = result["response"]["text"]
        urgency_level = result["response"]["urgency_level"]

        # Color-coded urgency box
        urgency_class = f"urgency-{urgency_level.lower()}" if urgency_level != "N/A" else ""
        if urgency_class:
            st.markdown(f'<div class="{urgency_class}">{response_text}</div>',
                       unsafe_allow_html=True)
        else:
            st.markdown(response_text)

        # Debug expander (for development)
        if st.checkbox("Show debug info", key=f"debug_{len(st.session_state.messages)}"):
            st.json(result.get("debug", {}))

    st.session_state.messages.append({"role": "assistant", "content": response_text})

# ── SIDEBAR ──────────────────────────────────────────────────
with st.sidebar:
    st.header("About NeuroHealth")
    st.markdown("""
    NeuroHealth is an AI health assistant that:
    - Understands your symptoms
    - Assesses urgency level
    - Recommends appropriate care
    - Provides health education

    **Urgency Levels:**
    - 🔴 Emergency — Call 911
    - 🟠 Urgent — Go to urgent care today
    - 🟡 Soon — See a doctor in 1-2 days
    - 🟢 Routine — Schedule an appointment
    - 🔵 Self-care — Can manage at home
    """)

    if st.button("Start New Conversation"):
        st.session_state.messages = []
        st.session_state.session_id = None
        st.rerun()
