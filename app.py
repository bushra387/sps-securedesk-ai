import streamlit as st
import requests
import pandas as pd

# --- Page Config & Theme ---
st.set_page_config(page_title="SPS SecureDesk AI", page_icon="🏢", layout="wide")

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
                resp = requests.post("http://127.0.0.1:8000/tickets", json=payload)
                if resp.status_code == 200: 
                    st.success(f"Success! Ticket Created. ID: {resp.json().get('ticket_id')}")
                else: st.error("Failed to create ticket.")
            else: st.warning("Please fill in all mandatory fields.")

# --- TAB 3: Agent Dashboard ---
if user_role == "Support Agent":
    with all_tabs[2]:
        st.header("📋 Agent Queue")
        
        # Session state for AI draft
        if "ai_draft" not in st.session_state: st.session_state.ai_draft = ""

        if st.button("🔄 Refresh Queue"): st.rerun()

        try:
            data = requests.get("http://127.0.0.1:8000/tickets/all").json()
            if data:
                df = pd.DataFrame(data)
                st.dataframe(df[['id', 'subject', 'status', 'priority', 'created_at']], use_container_width=True, hide_index=True)
                
                st.divider()
                selected_id = st.text_input("Select Ticket ID for Details/Action:")
                
                if selected_id:
                    details = requests.get(f"http://127.0.0.1:8000/tickets/{selected_id}").json()
                    st.subheader(f"Ticket: {selected_id}")
                    
                    # 1. Status & Management Section
                    with st.expander("Update Ticket Status & Details"):
                        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved", "Closed"])
                        if st.button("Update Status"):
                            requests.put(f"http://127.0.0.1:8000/tickets/{selected_id}/status", json={"new_status": new_status})
                            st.success(f"Status updated to {new_status}")
                    
                    # 2. Conversation History
                    for msg in details.get('timeline', []):
                        # Simple logic: Highlight internal notes differently if your backend sends 'is_public'
                        sender = msg['sender_type'].upper()
                        with st.chat_message(msg['sender_type']): 
                            st.markdown(f"**{sender}:** {msg['content']}")
                    
                    # 3. AI Drafting & Reply Form
                    st.subheader("Respond to User")
                    
                    # AI Draft Button
                    if st.button("✨ Draft Response with AI"):
                        with st.spinner("AI is analyzing history..."):
                            # Send history to backend to get a suggested reply
                            context = " ".join([m['content'] for m in details.get('timeline', [])])
                            resp = requests.post("http://127.0.0.1:8000/chat", json={"query": f"Draft a professional support response to: {context}"})
                            st.session_state.ai_draft = resp.json().get("response", "Could not generate draft.")
                            st.rerun()

                    # The Reply Form
                    with st.form("reply_form", clear_on_submit=True):
                        reply = st.text_area("Agent Response", value=st.session_state.ai_draft)
                        is_internal = st.checkbox("Mark as Internal Note (Private to Agents)")
                        
                        if st.form_submit_button("Send Response"):
                            requests.post("http://127.0.0.1:8000/tickets/message", json={
                                "ticket_id": selected_id, 
                                "sender_type": "agent", 
                                "content": reply,
                                "is_public": not is_internal # Ensure your backend accepts this
                            })
                            st.session_state.ai_draft = "" # Clear draft
                            st.rerun()
            else: st.info("No tickets found.")
        except Exception as e: st.error(f"Error loading dashboard: {e}")