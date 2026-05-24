import streamlit as st
from orchestrator import route
from agents import academics, campus, financial_aid
from memory.memory import load_history, save_history

st.title("🤖 TXST Campus Assistant")
st.caption("Ask me anything about Texas State University")

if "history" not in st.session_state:
    st.session_state.history = load_history()

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if st.button("🗑️ Clear History"):
    st.session_state.history = []
    save_history([])
    st.rerun()

if prompt := st.chat_input("Ask a question..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    result = route(prompt)
    agent = result["agent"]
    confidence = result["confidence"]

    # if confidence is low, ask for clarification
    if confidence < 0.6:
        response = "I'm not sure I understood your question. Could you clarify — are you asking about academics, campus facilities, or financial aid?"
    elif agent == "ACADEMICS":
        response = academics.run(prompt, st.session_state.history)
    elif agent == "FINANCIAL_AID":
        response = financial_aid.run(prompt, st.session_state.history)
    else:
        response = campus.run(prompt, st.session_state.history)

    # show which agent answered and confidence
    st.caption(f"🤖 {agent} agent · {int(confidence * 100)}% confidence")

    st.session_state.history.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)

    save_history(st.session_state.history)