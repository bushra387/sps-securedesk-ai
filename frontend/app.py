import streamlit as st
import requests
import pandas as pd

# --- Page Config ---
st.set_page_config(page_title="SPS SecureDesk AI", page_icon="🤖", layout="wide")

# --- SPS Styling ---
st.markdown("""
    <style>
    .main-header { 
        background-color: #2C2C54; 
        color: white; 
        padding: 1.5rem; 
        border-radius: 10px; 
        text-align: center; 
        margin-bottom: 20px;
    }
    .stApp { background-color: #F8F9FA; }
    </style>
    <div class="main-header">
        <h1>SPS SecureDesk AI</h1>
        <p>Enterprise Helpdesk | IT, Cloud, Cybersecurity, & Operations</p>
    </div>
""", unsafe_allow_html=True)

# --- Sidebar: Role Selector & System Status ---
with st.sidebar:
    st.header("Settings")
    user_role = st.radio("Select View", ["Intern/Employee", "Support Agent"])
    st.divider()
    st.header("System Status")
    try:
        requests.get("http://127.0.0.1:8000")
        st.success("Backend: Online")
    except:
        st.error("Backend: Offline")

# --- Tab Initialization ---
tabs_names = ["AI Chat Assistant", "Submit a Request"]
if user_role == "Support Agent":
    tabs_names.append("Agent Dashboard")

all_tabs = st.tabs(tabs_names)

# --- TAB 1: Chat ---
with all_tabs[0]:
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])

    if prompt := st.chat_input("How can I help you?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        
        with st.chat_message("assistant"):
            try:
                resp = requests.post("http://127.0.0.1:8000/chat", json={"query": prompt})
                ans = resp.json().get("response", "Error contacting AI.")
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except Exception:
                st.error("Backend unreachable!")

# --- TAB 2: Web Form ---
with all_tabs[1]:
    st.header("Submit a Support Request")
    with st.form("ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject")
            email = st.text_input("Contact Email")
        with col2:
            category = st.selectbox("Category", ["Cloud", "Cybersecurity", "Identity and Access", "DevOps", "Internship/HR", "General IT"])
        
        description = st.text_area("Description")
        
        if st.form_submit_button("Submit Ticket"):
            if not subject or not email or not description:
                st.error("Please fill in all fields.")
            else:
                resp = requests.post("http://127.0.0.1:8000/tickets", json={
                    "subject": subject, 
                    "requester_email": email, 
                    "description": description, 
                    "category": category, 
                    "source": "portal_form"
                })
                if resp.status_code == 200: 
                    st.success(f"Ticket Created! ID: {resp.json().get('ticket_id')}")
                else: 
                    st.error("Failed to create ticket.")

# --- TAB 3: Agent Dashboard (Conditional) ---
if user_role == "Support Agent":
    with all_tabs[2]:
        st.header("Agent Queue")
        
        if st.button("Refresh Queue"):
            try:
                tickets_data = requests.get("http://127.0.0.1:8000/tickets/all").json()
                if tickets_data:
                    df = pd.DataFrame(tickets_data)
                    st.dataframe(df, use_container_width=True)
                    
                    st.subheader("Ticket Details & Timeline")
                    selected_id = st.text_input("Enter Ticket ID from table above to view:")
                    
                    if selected_id:
                        details = requests.get(f"http://127.0.0.1:8000/tickets/{selected_id}").json()
                        st.write(f"**Subject:** {details['ticket'].get('subject')}")
                        
                        for msg in details['timeline']:
                            with st.chat_message(msg['sender_type']):
                                st.markdown(msg['content'])
                                
                        reply = st.text_area("Reply to user or add internal note")
                        if st.button("Send Message"):
                            requests.post("http://127.0.0.1:8000/tickets/message", json={
                                "ticket_id": selected_id,
                                "sender_type": "agent",
                                "content": reply
                            })
                            st.rerun()
                else:
                    st.info("No tickets currently in the queue.")
            except Exception as e:
                st.error(f"Error fetching tickets: {e}")