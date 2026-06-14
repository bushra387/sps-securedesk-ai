import streamlit as st

def login_screen():
    st.markdown("<h1 style='text-align: center;'>SPS Enterprise Portal</h1>", unsafe_allow_html=True)
    role = st.selectbox("Role", ["Intern/Employee", "Support Agent"])
    if st.button("Enter Portal"):
        st.session_state.logged_in = True
        st.session_state.role = role
        st.rerun()