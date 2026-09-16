# pyrefly: ignore [missing-import]
import streamlit as st
# pyrefly: ignore [missing-import]
import httpx
import pandas as pd
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Complaint Router & Triage Platform",
    page_icon=":material/smart_toy:",
    layout="wide",
    initial_sidebar_state="expanded"
)

BACKEND_URL = "http://127.0.0.1:8000"

# Custom CSS for glassmorphism styling and glowing accents
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@500;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgba(15, 23, 42, 0.98) 0%, rgba(9, 13, 22, 1) 100%);
        color: #f8fafc;
    }
    
    h1, h2, h3 {
        font-family: 'Outfit', sans-serif;
        letter-spacing: -0.02em;
    }
    
    .main-header {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    
    .jira-pill {
        background: rgba(14, 165, 233, 0.15);
        border: 1px solid rgba(14, 165, 233, 0.4);
        color: #38bdf8;
        padding: 4px 12px;
        border-radius: 8px;
        font-family: monospace;
        font-weight: 700;
        font-size: 0.9rem;
    }
    
    .reasoning-panel {
        background: rgba(30, 41, 59, 0.6);
        border-left: 4px solid #6366f1;
        padding: 16px;
        border-radius: 0 12px 12px 0;
        font-size: 1rem;
        line-height: 1.6;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to check backend health
def check_backend_health():
    try:
        res = httpx.get(f"{BACKEND_URL}/health", timeout=3.0)
        return res.status_code == 200, res.json() if res.status_code == 200 else {}
    except Exception:
        return False, {}

# Sidebar Navigation & System Status
with st.sidebar:
    st.markdown("## :material/tune: System status")
    is_healthy, health_data = check_backend_health()
    
    if is_healthy:
        st.badge("Backend online", icon=":material/check_circle:", color="green")
        
        with st.container(border=True):
            st.caption("Active configuration")
            st.markdown(f"**Vector DB:** `{health_data.get('vector_db', 'ChromaDB')}`")
            st.markdown(f"**Embedder:** `{health_data.get('embedding_model', 'BAAI/bge-m3')}`")
            st.markdown(f"**LLM:** `{health_data.get('llm_provider', 'Groq').upper()}` (`{health_data.get('llm_model', 'llama-3.3-70b')}`)")
    else:
        st.badge("Backend offline", icon=":material/error:", color="red")
        st.warning("Ensure backend API is running (`uvicorn backend.main:app --port 8000`).", icon=":material/warning:")
    
    st.space("medium")
    
    if st.button("Re-index documentation", icon=":material/refresh:", width="stretch"):
        with st.spinner("Re-indexing runbook markdown docs..."):
            try:
                res = httpx.post(f"{BACKEND_URL}/api/v1/docs/reindex", timeout=10.0)
                if res.status_code == 200:
                    st.toast(f"Successfully re-indexed {res.json().get('indexed_chunks')} chunks!", icon="✅")
                else:
                    st.error("Failed to re-index docs.")
            except Exception as e:
                st.error(f"Error: {e}")

# Header
st.markdown("<div class='main-header'>AI Complaint Router & Triage Platform</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Automated RAG-driven triage, developer allocation, and MCP tool execution engine</div>", unsafe_allow_html=True)

# Navigation Tabs
tab_triage, tab_audit = st.tabs([
    ":material/assignment: Complaint intake & triage", 
    ":material/history: Assignment audit history"
])

# Preset complaints dataset
PRESET_SAMPLES = {
    "💳 Payment 504 Timeout": {
        "text": "Customer is experiencing 504 gateway timeout on payments endpoint when paying with international Stripe credit cards.",
        "customer": "Acme Corp",
        "product_area": "Checkout & Payments"
    },
    "🔐 OAuth SSO JWT Error": {
        "text": "Users are unable to log in using OAuth2 SSO (Google / Okta). Server returns 'Invalid JWT signature' error on public key verify.",
        "customer": "FinTech Global",
        "product_area": "Authentication & SSO"
    },
    "📊 DB Pool Exhaustion": {
        "text": "Dashboard analytics charts load extremely slowly or fail with database pool exhaustion exception during morning peak hours.",
        "customer": "DataViz Inc",
        "product_area": "Analytics & Reporting"
    },
    "✉️ SendGrid Email Spam": {
        "text": "Automated email notifications for invoice receipts are not being delivered to customers or are ending up in spam folders.",
        "customer": "Retail Plus",
        "product_area": "Notification Service"
    },
    "⚡ Webhook 429 Rate Limit": {
        "text": "Webhook delivery fails intermittently with status 429 Too Many Requests when syncing bulk inventory updates.",
        "customer": "LogiCorp",
        "product_area": "Webhooks & API Gateway"
    }
}

with tab_triage:
    col_input, col_output = st.columns([1, 1], gap="medium")
    
    with col_input:
        with st.container(border=True):
            st.subheader("📥 Submit new complaint", anchor=False)
            
            st.caption("Quick sample presets")
            selected_preset_key = st.pills(
                "Sample presets",
                options=list(PRESET_SAMPLES.keys()),
                label_visibility="collapsed"
            )
            
            # Default values
            default_text = ""
            default_customer = ""
            default_area_index = 0
            
            areas = ["None", "Checkout & Payments", "Authentication & SSO", "Analytics & Reporting", "Notification Service", "Webhooks & API Gateway"]
            
            if selected_preset_key and selected_preset_key in PRESET_SAMPLES:
                p_data = PRESET_SAMPLES[selected_preset_key]
                default_text = p_data["text"]
                default_customer = p_data["customer"]
                if p_data["product_area"] in areas:
                    default_area_index = areas.index(p_data["product_area"])

            with st.form(key="complaint_intake_form"):
                complaint_text = st.text_area(
                    "Complaint description *",
                    value=default_text,
                    placeholder="Describe the issue reported by the customer (e.g. Payment gateway throws 504 timeout on checkout...)",
                    height=140
                )
                
                c1, c2 = st.columns(2)
                with c1:
                    customer = st.text_input(
                        "Customer name / ID",
                        value=default_customer,
                        placeholder="e.g. Acme Corp"
                    )
                with c2:
                    product_area = st.selectbox(
                        "Product area",
                        options=areas,
                        index=default_area_index
                    )
                
                submit_btn = st.form_submit_button(
                    "Triage & assign developer",
                    icon=":material/send:",
                    width="stretch"
                )
                
            if submit_btn:
                if not complaint_text.strip():
                    st.error("Please enter a valid complaint description.")
                else:
                    with st.spinner("Analyzing complaint, querying ChromaDB vector store, and running MCP tool actions..."):
                        payload = {
                            "text": complaint_text,
                            "customer": customer.strip() if customer.strip() else None,
                            "product_area": product_area if product_area != "None" else None
                        }
                        try:
                            response = httpx.post(f"{BACKEND_URL}/api/v1/complaints/process", json=payload, timeout=30.0)
                            if response.status_code == 200:
                                st.session_state["last_result"] = response.json()
                                st.toast("Ticket successfully triaged & assigned!", icon="🎉")
                            else:
                                st.error(f"Backend error: {response.text}")
                        except Exception as e:
                            st.error(f"Could not connect to backend server: {e}")

    with col_output:
        st.subheader("🎯 Triage & assignment decision", anchor=False)
        result = st.session_state.get("last_result")
        
        if result:
            decision = result["decision"]
            complaint = result["complaint"]
            similar_tickets = result["similar_tickets"]
            retrieved_docs = result["retrieved_docs"]
            
            p_val = decision.get("priority", "medium").lower()
            jira_key = decision.get("jira_issue_key") or "COMP-101"
            
            with st.container(border=True):
                # Header row: Priority badge & Jira ticket tag
                h_col1, h_col2 = st.columns([1, 1])
                with h_col1:
                    if p_val == "critical":
                        st.badge("CRITICAL PRIORITY", icon=":material/report_problem:", color="red")
                    elif p_val == "high":
                        st.badge("HIGH PRIORITY", icon=":material/warning:", color="orange")
                    elif p_val == "medium":
                        st.badge("MEDIUM PRIORITY", icon=":material/info:", color="orange")
                    else:
                        st.badge("LOW PRIORITY", icon=":material/check_circle:", color="blue")
                with h_col2:
                    st.markdown(f"<div style='text-align: right;'><span class='jira-pill'>JIRA: {jira_key}</span></div>", unsafe_allow_html=True)
                
                st.space("small")
                
                # Assigned Dev
                st.caption("Assigned Lead Developer")
                st.markdown(f"### 👤 {decision['assigned_developer']}")
                
                st.space("small")
                
                # Reasoning
                st.caption("AI Triage Rationale")
                st.markdown(f"<div class='reasoning-panel'>{decision['reasoning']}</div>", unsafe_allow_html=True)
                
                st.space("medium")
                
                # Footer metrics
                m1, m2 = st.columns(2)
                with m1:
                    st.caption("Ticket ID")
                    st.code(complaint['id'])
                with m2:
                    st.caption("MCP Notification Dispatch")
                    if decision.get('notification_sent'):
                        st.badge("Dispatched", icon=":material/check_circle:", color="green")
                    else:
                        st.badge("Failed", icon=":material/cancel:", color="red")

            # Context Expanders
            with st.expander(f"🔎 Similar historical tickets ({len(similar_tickets)})", icon=":material/search:"):
                for t in similar_tickets:
                    with st.container(border=True):
                        st.markdown(f"**Ticket `{t['ticket_id']}`** · Similarity: `:blue-badge[{(t['similarity_score'] * 100):.1f}% match]`")
                        st.markdown(f"- **Assigned Developer:** {t['assigned_developer']}")
                        st.markdown(f"- **Past Resolution:** {t['resolution']}")

            with st.expander(f"📚 Retrieved developer runbooks ({len(retrieved_docs)})", icon=":material/description:"):
                for d in retrieved_docs:
                    with st.container(border=True):
                        st.markdown(f"📄 **Source:** `{d['source']}` · Relevance: `:purple-badge[{d['relevance_score']:.2f}]`")
                        st.caption(d['content'])

        else:
            with st.container(border=True):
                st.markdown("### 🤖 Ready for triage")
                st.caption("Select a sample preset above or describe a customer complaint to run semantic ticket search, RAG runbook retrieval, and automated MCP developer assignment.")

with tab_audit:
    st.subheader("📜 Assignment audit history", anchor=False)
    
    if st.button("Refresh audit log", icon=":material/refresh:"):
        st.rerun()
        
    try:
        res = httpx.get(f"{BACKEND_URL}/api/v1/audit-logs", timeout=5.0)
        if res.status_code == 200:
            logs = res.json()
            if logs:
                df = pd.DataFrame(logs)
                df = df[["id", "ticket_id", "developer", "priority", "jira_issue_key", "reasoning", "timestamp"]]
                
                st.dataframe(
                    df,
                    column_config={
                        "id": st.column_config.NumberColumn("Audit #", format="%d"),
                        "ticket_id": st.column_config.TextColumn("Ticket ID"),
                        "developer": st.column_config.TextColumn("Assigned Developer"),
                        "priority": st.column_config.TextColumn("Priority"),
                        "jira_issue_key": st.column_config.TextColumn("Jira Key"),
                        "reasoning": st.column_config.TextColumn("Triage Reasoning", width="large"),
                        "timestamp": st.column_config.DatetimeColumn("Timestamp", format="YYYY-MM-DD HH:mm:ss")
                    },
                    hide_index=True,
                    width="stretch"
                )
            else:
                st.info("No audit logs recorded yet.", icon=":material/info:")
        else:
            st.error("Failed to fetch audit logs from backend.")
    except Exception as e:
        st.error(f"Could not connect to backend server: {e}")
