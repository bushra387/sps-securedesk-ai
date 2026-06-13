import streamlit as st
import requests

st.set_page_config(page_title="SPS SecureDesk AI", page_icon="🤖")

st.title("🤖 SPS SecureDesk AI")
st.write("Ask anything about our internal procedures!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("How can I help you?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Call your FastAPI backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # This hits your FastAPI endpoint
                response = requests.post("http://127.0.0.1:8000/chat", json={"query": prompt})
                answer = response.json().get("response", "Error: Could not get response.")
                st.markdown(answer)
                st.session_state.messages.append({"role": "assistant", "content": answer})
            except Exception as e:
                st.error("Make sure your FastAPI server is running!")