# AI-Powered Complaint Routing & Developer Assignment System

An end-to-end intelligent complaint intake, routing, and developer assignment platform. The system processes raw customer complaints, performs semantic similarity search over resolved historical tickets, retrieves relevant internal developer documentation/runbooks using a **RAG pipeline**, and makes automated assignment decisions with an **MCP Server** that writes to Jira, dispatches notifications, and logs audit records.

---

## 🏛️ Architecture Overview

```
Client (Streamlit Frontend) ──> Python Backend (FastAPI)
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        ▼                              ▼                              ▼
  Complaint Processor            RAG Pipeline                    MCP Server
        │                              │                              │
        ▼                              ▼                              ▼
    Embedder                    Vector Store                   Assignment Tools
  (BAAI/bge-m3)                (Chroma / pgvector)          (Jira / Email / SQLite)
        │                              │                              │
        ▼                              ▼                              ▼
  Similar Tickets              Developer Docs                   Audit Database
        │                              │                              │
        └──────────────────────────────┼──────────────────────────────┘
                                       ▼
                             LLM Decision Engine
                                       │
                                       ▼
                       Assigned Developer + Priority Level
```

---

## 🛠️ Tech Stack & Components

1. **Frontend**: Streamlit UI (custom modern dark mode styling, intake form, decision cards, audit log history table)
2. **Backend**: FastAPI (async support, structured Pydantic models)
3. **LLM Engine**: Groq / OpenAI / Anthropic (`llama-3.3-70b-versatile` / `claude-3-5-sonnet` / `gpt-4o-mini`) with heuristic triage fallback
4. **Embeddings**: `BAAI/bge-m3` via `sentence-transformers` behind an abstract `Embedder` interface
5. **Vector Store**: `ChromaDB` (default persistent local store) behind a modular `VectorStore` interface (with `pgvector` adapter)
6. **MCP Server**: FastMCP / Python MCP SDK tools (`assign_ticket`, `notify_developer`, `log_assignment`) with dual-mode Jira integration (Mock & Jira Cloud REST API)
7. **Audit DB**: SQLite & SQLAlchemy persistent database

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10 or higher
- `pip` package manager

### 2. Installation
Clone the repository and install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your API keys (optional for local mock execution):
```bash
cp .env.example .env
```

Key environment variables:
- `GROQ_API_KEY`: Groq API key for Llama 3.3 70B model execution.
- `OPENAI_API_KEY`: (Optional) OpenAI API key.
- `ANTHROPIC_API_KEY`: (Optional) Anthropic Claude API key.
- `EMBEDDING_MODEL`: `BAAI/bge-m3` (default).
- `JIRA_SERVER_URL` & `JIRA_API_TOKEN`: (Optional) Credentials for real Jira Cloud integration. Leave empty to use built-in Mock Adapter.

### 4. Seed Data & Index Vector Database
Run the seed script to populate sample historical tickets (`data/sample_tickets.json`) and index developer runbooks (`data/docs/`):
```bash
python scripts/seed_data.py
```

### 5. Launch FastAPI Backend
```bash
uvicorn backend.main:app --port 8000 --reload
```
API Documentation will be accessible at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 6. Launch Streamlit Frontend
In a new terminal window:
```bash
streamlit run frontend/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🧪 Running Unit Tests

Run the test suite using `pytest`:
```bash
pytest tests/
```

---

## 📁 Repository Structure

```
├── backend/
│   ├── config.py             # Pydantic Settings
│   ├── models.py             # Data models & schemas
│   ├── main.py               # FastAPI app endpoints
│   ├── db/
│   │   ├── embedder.py       # Abstract Embedder & BGEEmbedder
│   │   ├── vector_store.py   # Abstract VectorStore, Chroma & PGVector
│   │   └── audit_db.py       # SQLite Audit Database
│   ├── modules/
│   │   ├── complaint_processor.py # Embedding & ticket similarity search
│   │   ├── rag_pipeline.py    # Documentation retrieval & re-ranking
│   │   └── llm_decision.py   # Prompt assembly & MCP tool invoker
│   └── mcp_server/
│       ├── jira_adapter.py   # Dual-mode Jira adapter
│       └── tools.py          # MCP Tools: assign, notify, log
├── frontend/
│   └── app.py                # Streamlit UI
├── data/
│   ├── sample_tickets.json   # Historical resolved tickets dataset
│   └── docs/                 # Developer runbooks & ownership map
├── scripts/
│   └── seed_data.py          # Seeding script
├── tests/                    # Pytest test suite
├── requirements.txt
├── .env.example
└── README.md
```
