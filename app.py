import streamlit as st
import requests
import pandas as pd

# --- Page Config & Theme ---
st.set_page_config(page_title="SPS SecureDesk AI", page_icon="🏢", layout="wide")

# Link the CSS file located in your /static folder
def load_css():
    try:
        with open("static/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("CSS file not found. Ensure 'static/style.css' exists.")

load_css()

# --- Header Section ---
st.markdown("""
    <div class="main-header" style="background-color:#002060; color:white; padding:1.5rem; border-radius:10px; text-align:center; margin-bottom:20px;">
        <h1 style="margin:0;">SPS SecureDesk AI</h1>
        <p style="margin:0;">Enterprise Helpdesk | IT, Cloud, Cybersecurity, & Operations</p>
    </div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    user_role = st.radio("Select View", ["Intern/Employee", "Support Agent"])
    st.divider()
    st.success("System Status: Online")

# --- Tabs ---
tabs_names = ["AI Chat Assistant", "Submit a Request"]
if user_role == "Support Agent":
    tabs_names.append("Agent Dashboard")

all_tabs = st.tabs(tabs_names)

# --- TAB 1: Chat ---
with all_tabs[0]:
    st.subheader("How can we help you today?")
    if "messages" not in st.session_state: st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about SPS policies or IT help..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                resp = requests.post("http://127.0.0.1:8000/chat", json={"query": prompt})
                ans = resp.json().get("response", "Error contacting AI.")
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except: st.error("Backend unreachable!")

# --- TAB 2: Web Form (Updated) ---
with all_tabs[1]:
    st.header("Submit a Support Request")
    
    with st.form("ticket_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input("Subject *")
            email = st.text_input("Contact Email *")
        with col2:
            category = st.selectbox("Category", ["Cloud", "Cybersecurity", "Identity", "DevOps", "Internship/HR", "General IT"])
            priority = st.select_slider("Priority", options=["Low", "Medium", "High", "Critical"])
        
        description = st.text_area("Description *")
        uploaded_file = st.file_uploader("Attach Screenshots/Logs (Optional)", type=['png', 'jpg', 'pdf'])
        
        if st.form_submit_button("Submit Request"):
            if subject and email and description:
                # Prepare data payload
                payload = {
                    "subject": subject, 
                    "requester_email": email, 
                    "description": description, 
                    "category": category, 
                    "priority": priority,
                    "source": "portal_form"
                }
                
                resp = requests.post("http://127.0.0.1:8000/tickets", json=payload)
                
                if resp.status_code == 200: 
                    ticket_id = resp.json().get('ticket_id')
                    st.success(f"Success! Ticket Created. ID: {ticket_id}")
                else: 
                    st.error("Failed to create ticket. Please check backend.")
            else: 
                st.warning("Please fill in all mandatory (*) fields.")

# --- TAB 3: Agent Dashboard ---
if user_role == "Support Agent":
    with all_tabs[2]:
        st.header("📋 Agent Queue")
        
        col_btn1, col_btn2 = st.columns([1, 6])
        with col_btn1:
            if st.button("🔄 Sync"):
                with st.spinner("Syncing emails..."):
                    requests.post("http://127.0.0.1:8000/api/sync-emails")
                st.rerun()
        with col_btn2:
            if st.button("🔄 Refresh"):
                st.rerun()

        try:
            data = requests.get("http://127.0.0.1:8000/tickets/all").json()
            if data:
                df = pd.DataFrame(data)
                # Show key info
                st.dataframe(df[['id', 'subject', 'requester_email', 'status', 'priority', 'created_at']], 
                             use_container_width=True, hide_index=True)
                
                st.divider()
                selected_id = st.text_input("View/Reply to Ticket ID:")
                
                if selected_id:
                    details = requests.get(f"http://127.0.0.1:8000/tickets/{selected_id}").json()
                    st.subheader(f"Conversation: {selected_id}")
                    
                    for msg in details.get('timeline', []):
                        with st.chat_message(msg['sender_type']): 
                            st.markdown(f"**{msg['sender_type'].upper()}:** {msg['content']}")
                    
                    with st.form("reply_form"):
                        reply = st.text_area("Add Agent Response")
                        if st.form_submit_button("Send Response"):
                            requests.post("http://127.0.0.1:8000/tickets/message", json={
                                "ticket_id": selected_id, "sender_type": "agent", "content": reply
                            })
                            st.rerun()
            else: 
                st.info("No tickets found.")
        except Exception as e: 
            st.error(f"Unable to load queue: {e}")
            