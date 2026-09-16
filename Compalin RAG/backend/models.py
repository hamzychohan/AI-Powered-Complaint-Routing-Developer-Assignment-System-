from datetime import datetime, timezone
from typing import Literal, List, Optional, Any, Dict
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field

class Complaint(BaseModel):
    id: str = Field(..., description="Unique ticket identifier")
    text: str = Field(..., description="Raw complaint description")
    customer: Optional[str] = Field(None, description="Customer ID or name")
    product_area: Optional[str] = Field(None, description="Affected product module/service")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SimilarTicket(BaseModel):
    ticket_id: str = Field(..., description="Historical ticket ID")
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")
    resolution: str = Field(..., description="Summary of past resolution")
    assigned_developer: str = Field(..., description="Developer who resolved the ticket")
    product_area: Optional[str] = None

class DocChunk(BaseModel):
    source: str = Field(..., description="File name or document title")
    content: str = Field(..., description="Extracted text chunk content")
    relevance_score: float = Field(..., description="Similarity or re-ranking relevance score")

class AssignmentDecision(BaseModel):
    complaint_id: str = Field(..., description="Associated complaint ticket ID")
    assigned_developer: str = Field(..., description="Developer or team assigned")
    priority: Literal["low", "medium", "high", "critical"] = Field(..., description="Assigned priority level")
    reasoning: str = Field(..., description="Detailed rationale explaining the decision")
    jira_issue_key: Optional[str] = Field(None, description="Jira issue key if created")
    notification_sent: bool = Field(False, description="Whether developer was notified")

class ComplaintRequest(BaseModel):
    text: str
    customer: Optional[str] = None
    product_area: Optional[str] = None

class ComplaintResponse(BaseModel):
    complaint: Complaint
    decision: AssignmentDecision
    similar_tickets: List[SimilarTicket]
    retrieved_docs: List[DocChunk]

class AuditLogItem(BaseModel):
    id: int
    ticket_id: str
    developer: str
    priority: str
    reasoning: str
    jira_issue_key: Optional[str] = None
    timestamp: datetime
    raw_inputs: Optional[Dict[str, Any]] = None
