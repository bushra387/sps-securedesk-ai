
# SPS SecureDesk AI

**Enterprise Helpdesk Portal | Software Productivity Strategists (SPS)**

SPS SecureDesk AI is an enterprise-grade helpdesk solution designed to centralize technical support requests from multiple channels into a single, auditable, and AI-assisted workflow. This project demonstrates the integration of three distinct intake pipelines—**Email, Web Form, and AI Chat**—into one unified ticket system.

---

## 🚀 Project Overview

This application streamlines the support process by using AI for ticket classification and draft generation, while ensuring all activity is logged for compliance and security.

### Key Features

* **Unified Intake:** Tickets originating from email, web forms, and AI chat are unified into a single database with a shared timeline and unique `SPS-YYYY-ID` format.
* **AI-Driven Assistance:** Powered by Google Gemini, the system provides knowledge base (KB) retrieval for chat users and smart draft responses for support agents.
* **Agent Dashboard:** A dedicated interface for support staff to manage the ticket queue, update statuses, and perform internal notes/public replies.
* **Compliance & Audit:** Every action is tracked in the `audit_logs` table, ensuring a complete trail for all ticket modifications.
* **Security:** Input sanitization is applied to all incoming content to prevent common web injection vulnerabilities.

---

## 🛠 Tech Stack

* **Frontend:** Streamlit (Python)
* **Backend:** FastAPI (Python)
* **Database:** Supabase (PostgreSQL)
* **AI/LLM:** Google Gemini (LangChain integration)
* **Security:** CORS Middleware, Environment Variable management, Input Sanitization

---

## 📋 Architecture: The Three Pipelines

1. **Email Intake:** An IMAP-based listener monitors incoming emails. If the subject contains a known ticket ID, it appends to the timeline; otherwise, it initiates a new ticket.
2. **Web Form:** A secure form in the portal sanitizes inputs and classifies the ticket category before insertion, ensuring accurate queue routing.
3. **AI Chat:** A RAG (Retrieval-Augmented Generation) pipeline that searches the SPS knowledge base to answer user queries immediately or escalates to a formal support request.

---

## ⚙️ Setup Instructions

### 1. Prerequisites

* Python 3.10+
* Supabase Account & Project
* Google Gemini API Key
* Gmail Account (with App Password for IMAP/SMTP)

### 2. Environment Configuration

Create a `.env` file in the root directory:

```text
EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_app_password
GEMINI_API_KEY=your_key_here
SUPABASE_URL=your_url
SUPABASE_KEY=your_key

```

### 3. Running the Application

1. **Start the Backend:**
Open a terminal in the project root and run:
```bash
python -m uvicorn backend.main:app --reload

```


2. **Start the Frontend:**
Open a second terminal in the project root and run:
```bash
streamlit run app.py

```


3. **Access:** Navigate to `http://localhost:8501` in your browser.

---

## 📝 Success Criteria Walkthrough

* **Create Tickets:** Use the "Submit a Request" tab for forms or the "AI Chat" for chat-originated tickets.
* **Manage Queue:** Agents can view the "Agent Dashboard," select a ticket, update the status, and draft AI responses.
* **Audit Trail:** Verify in the database that all actions are recorded in the `audit_logs` table with the correct `source` channel.

---

*Project developed as an Intern Capstone for Software Productivity Strategists (SPS).*