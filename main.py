import streamlit as st
import os
from uuid import uuid4
from groq import RateLimitError
from chat_service import answer_stream
from memory.memory import load_history, clear_history
from chat_format import compact_saved_answer

# Page config
st.set_page_config(
    page_title="TXST Campus Assistant",
    page_icon="🐱",
    layout="centered"
)

# Custom CSS — TXST maroon & gold branding
st.markdown("""
<style>
    .stApp {
        background-color: #FAFAFA;
    }
    .agent-badge {
        display: inline-block;
        background-color: #F4B223;
        color: #501214;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .stButton button {
        background-color: #501214;
        color: white;
        border-radius: 8px;
        border: none;
    }
    .stButton button:hover {
        background-color: #6b1a1d;
        color: #F4B223;
    }
</style>
""", unsafe_allow_html=True)

# Header — with logo if available, fallback to emoji if not
logo_path = "assets/txst-logo.png"
col1, col2 = st.columns([1, 4])
with col1:
    if os.path.exists(logo_path):
        st.image(logo_path, width=80)
    else:
        st.markdown("<h1 style='font-size:50px; margin:0;'>🐱</h1>", unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div style="padding-top: 10px;">
        <h1 style="color: #501214; margin: 0; font-size: 26px;">TXST Campus Assistant</h1>
        <p style="color: #666; margin: 0; font-size: 14px;">Your AI guide to academics, campus life, and financial aid</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()

# Sidebar
with st.sidebar:
    if os.path.exists(logo_path):
        st.image(logo_path, width=60)
    st.markdown("### TXST Campus Assistant")
    st.caption("Powered by AI · Built for Bobcats")
    st.divider()
    st.markdown("**What I can help with:**")
    st.markdown("🎓 **Academics** — courses, registration, deadlines")
    st.markdown("🏫 **Campus** — dining, parking, facilities")
    st.markdown("💰 **Financial Aid** — scholarships, FAFSA, grants")
    st.divider()
    if st.button("🗑️ Clear Conversation"):
        st.session_state.history = []
        clear_history(st.session_state.session_id)
        st.rerun()

# Load history
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid4())
if "history" not in st.session_state:
    st.session_state.history = load_history(st.session_state.session_id)

AGENT_ICONS = {
    "ACADEMICS": "🎓",
    "CAMPUS": "🏫",
    "FINANCIAL_AID": "💰"
}

# Display chat history
for msg in st.session_state.history:
    avatar = "🧑‍🎓" if msg["role"] == "user" else "🐱"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(compact_saved_answer(msg["content"]) if msg["role"] == "assistant" else msg["content"])

# Chat input
if prompt := st.chat_input("Ask about academics, campus life, or financial aid..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="🧑‍🎓"):
        st.write(prompt)

    try:
        meta, tokens = answer_stream(prompt, st.session_state.session_id)
    except RateLimitError:
        st.session_state.history.pop()
        st.error("The assistant is temporarily busy. Please try again in a minute.")
        st.stop()
    agent = meta["agent"]
    confidence = meta["confidence"]
    agent_display = agent if confidence >= 0.6 else None

    with st.chat_message("assistant", avatar="🐱"):
        if agent_display:
            st.markdown(
                f'<span class="agent-badge">{AGENT_ICONS.get(agent_display, "🤖")} {agent_display.replace("_", " ").title()}</span>',
                unsafe_allow_html=True
            )
        response = st.write_stream(tokens)

    response = compact_saved_answer(response)
    st.session_state.history.append({"role": "assistant", "content": response})
