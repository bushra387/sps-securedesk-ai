import streamlit as st
import requests
import pandas as pd
from auth import login_screen # Ensure auth.py exists

# --- Page Config & Theme ---
st.set_page_config(page_title="SPS SecureDesk AI", page_icon="🏢", layout="wide")

def load_css():
    try:
        with open("static/style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass # CSS optional for functionality

load_css()

# --- Header Section ---
st.markdown("""
    <div style="background-color:#002060; color:white; padding:1.5rem; border-radius:10px; text-align:center; margin-bottom:20px;">
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

# --- Tabs Setup ---
tabs_names = ["AI Chat Assistant", "Submit a Request"]
if user_role == "Support Agent":
    tabs_names.append("Agent Dashboard")

all_tabs = st.tabs(tabs_names)

# --- TAB 1: Chat ---
with all_tabs[0]:
    st.subheader("How can we help you today?")
    if "messages" not in st.session_state: 
        st.session_state.messages = []
    
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]): 
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about SPS policies or IT help..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"): 
            st.markdown(prompt)
        with st.chat_message("assistant"):
            try:
                resp = requests.post("http://127.0.0.1:8000/chat", json={"query": prompt}, timeout=5)
                ans = resp.json().get("response", "Error contacting AI.")
                st.markdown(ans)
                st.session_state.messages.append({"role": "assistant", "content": ans})
            except: 
                st.error("Backend unreachable!")

# --- TAB 2: Web Form ---
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
        if st.form_submit_button("Submit Request"):
            if subject and email and description:
                payload = {"subject": subject, "requester_email": email, "description": description, "category": category, "priority": priority, "source": "portal_form"}
                try:
                    resp = requests.post("http://127.0.0.1:8000/tickets", json=payload, timeout=5)
                    if resp.status_code == 200: 
                        st.success(f"Success! Ticket Created. ID: {resp.json().get('ticket_id')}")
                    else: 
                        st.error("Failed to create ticket.")
                except:
                    st.error("Backend unreachable.")
            else: 
                st.warning("Please fill in all mandatory fields.")

# --- TAB 3: Agent Dashboard ---
if user_role == "Support Agent":
    with all_tabs[2]:
        st.header("📋 Agent Queue")
        
        if "ai_draft" not in st.session_state: 
            st.session_state.ai_draft = ""

        if st.button("🔄 Refresh Queue"): 
            st.rerun()

        try:
            data = requests.get("http://127.0.0.1:8000/tickets/all", timeout=5).json()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df[['id', 'subject', 'status', 'priority', 'created_at']], use_container_width=True, hide_index=True)
                
                st.divider()
                selected_id = st.text_input("Select Ticket ID for Details/Action:")
                
                if selected_id:
                    details = requests.get(f"http://127.0.0.1:8000/tickets/{selected_id}", timeout=5).json()
                    st.subheader(f"Ticket: {selected_id}")
                    
                    with st.expander("Update Ticket Status"):
                        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved", "Closed"])
                        if st.button("Apply Status Change"):
                            requests.put(f"http://127.0.0.1:8000/tickets/{selected_id}/status", json={"new_status": new_status}, timeout=5)
                            st.success(f"Status updated to {new_status}")
                            st.rerun()
                
                    for msg in details.get('timeline', []):
                        with st.chat_message(msg['sender_type']): 
                            st.markdown(f"**{msg['sender_type'].upper()}:** {msg['content']}")
                    
                    st.subheader("Respond to User")
                    if st.button("✨ Draft Response with AI"):
                        with st.spinner("AI drafting..."):
                            context = " ".join([m['content'] for m in details.get('timeline', [])])
                            resp = requests.post("http://127.0.0.1:8000/chat", json={"query": f"Draft a professional support response to: {context}"}, timeout=10)
                            st.session_state.ai_draft = resp.json().get("response", "Could not generate draft.")
                            st.rerun()

                    with st.form("reply_form"):
                        reply = st.text_area("Agent Response", value=st.session_state.ai_draft)
                        is_internal = st.checkbox("Mark as Internal Note (Private)")
                        
                        if st.form_submit_button("Send Response"):
                            requests.post("http://127.0.0.1:8000/tickets/message", json={
                                "ticket_id": selected_id, 
                                "sender_type": "agent", 
                                "content": reply,
                                "is_public": not is_internal
                            }, timeout=5)
                            st.session_state.ai_draft = "" 
                            st.success("Response Sent!")
                            st.rerun()
            else: 
                st.info("No tickets found.")
        except Exception as e: 
            st.error(f"Error loading dashboard: {e}")