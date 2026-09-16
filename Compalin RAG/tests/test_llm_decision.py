from datetime import datetime, timezone
from backend.models import Complaint, SimilarTicket, DocChunk
from backend.modules.llm_decision import LLMDecisionEngine

def test_heuristic_triage_decision():
    engine = LLMDecisionEngine()
    
    complaint = Complaint(
        id="TICK-999",
        text="Payment gateway returns 504 gateway timeout error during customer checkout",
        customer="Acme Corp",
        product_area="Checkout & Payments",
        created_at=datetime.now(timezone.utc)
    )

    
    similar_tickets = [
        SimilarTicket(
            ticket_id="TICK-101",
            similarity_score=0.95,
            resolution="Increased timeout setting",
            assigned_developer="Alice Smith (Payments Team)"
        )
    ]
    
    docs = [
        DocChunk(
            source="payment_runbook.md",
            content="Checkout and Payment gateway issues should be assigned to Alice Smith.",
            relevance_score=0.88
        )
    ]
    
    decision = engine.decide_and_execute(complaint, similar_tickets, docs)
    
    assert decision.complaint_id == "TICK-999"
    assert "Alice" in decision.assigned_developer
    assert decision.priority in ["low", "medium", "high", "critical"]
    assert decision.jira_issue_key is not None
    assert decision.notification_sent is True
