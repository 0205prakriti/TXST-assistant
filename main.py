import streamlit as st
from orchestrator import route
from agents import academics, campus

st.title("🤖 TXST Campus Assistant")
st.caption("Ask me anything about Texas State University")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask a question..."):
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    agent = route(prompt)

    if agent == "ACADEMICS":
        response = academics.run(prompt, st.session_state.history)
    else:
        response = campus.run(prompt, st.session_state.history)

    st.session_state.history.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)