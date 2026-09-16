# pyrefly: ignore [missing-import]
import pytest
from backend.db.embedder import DummyEmbedder
from backend.db.vector_store import ChromaVectorStore
from backend.modules.complaint_processor import ComplaintProcessor

@pytest.fixture
def dummy_setup(tmp_path):
    embedder = DummyEmbedder()
    db_dir = str(tmp_path / "chroma_test")
    vector_store = ChromaVectorStore(persist_dir=db_dir, embedder=embedder)
    
    # Add dummy historical tickets
    vector_store.add_documents(
        collection_name="tickets",
        ids=["T-1", "T-2"],
        documents=[
            "Stripe payment gateway timeout error during checkout",
            "OAuth login invalid token signature"
        ],
        metadatas=[
            {"resolution": "Increased timeout", "assigned_developer": "Alice", "product_area": "Payments"},
            {"resolution": "Rotated keys", "assigned_developer": "Bob", "product_area": "Auth"}
        ]
    )
    return embedder, vector_store

def test_complaint_processor_similarity_search(dummy_setup):
    embedder, vector_store = dummy_setup
    processor = ComplaintProcessor(embedder=embedder, vector_store=vector_store)
    
    result = processor.process_complaint(
        text="Payment gateway timeout when processing card",
        customer="Test Customer",
        product_area="Payments",
        top_k=2
    )
    
    assert result["complaint"].customer == "Test Customer"
    assert len(result["similar_tickets"]) == 2
    assert result["similar_tickets"][0].assigned_developer in ["Alice", "Bob"]
