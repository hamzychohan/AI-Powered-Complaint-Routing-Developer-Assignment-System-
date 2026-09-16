import os
import logging
from typing import List, Dict, Any

# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException                     
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles         

from backend.config import settings
# pyrefly: ignore [missing-import]
from backend.models import ComplaintRequest, ComplaintResponse, AuditLogItem
from backend.db.embedder import BGEEmbedder, DummyEmbedder
from backend.db.vector_store import ChromaVectorStore
from backend.db.audit_db import AuditDB
from backend.modules.complaint_processor import ComplaintProcessor
from backend.modules.rag_pipeline import RAGPipeline
from backend.modules.llm_decision import LLMDecisionEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Complaint Routing & Developer Assignment API",
    description="Automated complaint triage system using RAG and MCP server tool actions",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core services
logger.info("Initializing Backend Embedder and Vector Store...")
try:
    embedder = BGEEmbedder(model_name=settings.EMBEDDING_MODEL)
except Exception as e:
    logger.warning(f"Could not load BGEEmbedder ({e}). Falling back to DummyEmbedder.")
    embedder = DummyEmbedder()

vector_store = ChromaVectorStore(persist_dir=settings.CHROMA_DB_DIR, embedder=embedder)
audit_db = AuditDB(db_path=settings.SQLITE_DB_PATH)

complaint_processor = ComplaintProcessor(embedder=embedder, vector_store=vector_store)
rag_pipeline = RAGPipeline(embedder=embedder, vector_store=vector_store)
llm_engine = LLMDecisionEngine()

@app.get("/health", summary="Health check endpoint")
def health_check():
    return {
        "status": "healthy",
        "vector_db": settings.VECTOR_DB_TYPE,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL
    }

@app.post("/api/v1/complaints/process", response_model=ComplaintResponse, summary="Process incoming complaint")
def process_complaint(request: ComplaintRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Complaint text cannot be empty.")
    
    try:
        # Step 1: Complaint embedding & historical ticket similarity search
        proc_result = complaint_processor.process_complaint(
            text=request.text,
            customer=request.customer,
            product_area=request.product_area,
            top_k=3
        )
        complaint = proc_result["complaint"]
        embedding = proc_result["embedding"]
        similar_tickets = proc_result["similar_tickets"]

        # Step 2: RAG Pipeline - Documentation retrieval & re-ranking
        retrieved_docs = rag_pipeline.retrieve_docs(
            query_text=request.text,
            query_embedding=embedding,
            top_k=5,
            rerank_top_n=3
        )

        # Step 3: LLM Decision Engine & MCP Tool Execution
        decision = llm_engine.decide_and_execute(
            complaint=complaint,
            similar_tickets=similar_tickets,
            retrieved_docs=retrieved_docs
        )

        return ComplaintResponse(
            complaint=complaint,
            decision=decision,
            similar_tickets=similar_tickets,
            retrieved_docs=retrieved_docs
        )
    except Exception as e:
        logger.error(f"Error processing complaint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal processing failure: {str(e)}")

@app.get("/api/v1/audit-logs", response_model=List[AuditLogItem], summary="Get historical assignment audit logs")
def get_audit_logs(limit: int = 50):
    try:
        logs = audit_db.get_all_logs(limit=limit)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch audit logs: {str(e)}")

@app.post("/api/v1/docs/reindex", summary="Re-index developer documentation")
def reindex_docs():
    try:
        count = rag_pipeline.reindex_docs()
        return {"status": "success", "indexed_chunks": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Re-indexing failed: {str(e)}")

# Mount static React frontend at root URL
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="static")

