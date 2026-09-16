# pyrefly: ignore [missing-import]
import pytest
from backend.db.embedder import DummyEmbedder
from backend.db.vector_store import ChromaVectorStore
from backend.modules.rag_pipeline import RAGPipeline

@pytest.fixture
def dummy_rag_setup(tmp_path):
    embedder = DummyEmbedder()
    db_dir = str(tmp_path / "chroma_test_rag")
    vector_store = ChromaVectorStore(persist_dir=db_dir, embedder=embedder)
    
    vector_store.add_documents(
        collection_name="docs",
        ids=["doc_1", "doc_2"],
        documents=[
            "Checkout and Payment processing is owned by Alice Smith. For 504 errors, increase Stripe timeout.",
            "Authentication service OAuth SSO is owned by Bob Jones. For JWT errors, rotate Keycloak keys."
        ],
        metadatas=[
            {"source": "payment_runbook.md"},
            {"source": "auth_postmortem.md"}
        ]
    )
    return embedder, vector_store

def test_rag_pipeline_retrieval_and_reranking(dummy_rag_setup):
    embedder, vector_store = dummy_rag_setup
    pipeline = RAGPipeline(embedder=embedder, vector_store=vector_store)
    
    query = "Stripe payment 504 timeout error"
    embedding = embedder.embed_text(query)
    
    docs = pipeline.retrieve_docs(query_text=query, query_embedding=embedding, top_k=2, rerank_top_n=2)
    assert len(docs) > 0
    assert docs[0].source in ["payment_runbook.md", "auth_postmortem.md"]
    assert docs[0].relevance_score > 0
