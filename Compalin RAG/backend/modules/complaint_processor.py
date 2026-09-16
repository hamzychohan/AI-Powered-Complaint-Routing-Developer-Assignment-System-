import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from backend.models import Complaint, SimilarTicket
from backend.db.embedder import Embedder
from backend.db.vector_store import VectorStore

class ComplaintProcessor:
    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def process_complaint(
        self,
        text: str,
        customer: Optional[str] = None,
        product_area: Optional[str] = None,
        top_k: int = 3
    ) -> Dict[str, Any]:
        """
        Embeds incoming complaint text, creates Complaint model,
        and searches vector DB for top-k similar historical tickets.
        """
        ticket_id = f"TICK-{uuid.uuid4().hex[:6].upper()}"
        complaint = Complaint(
            id=ticket_id,
            text=text,
            customer=customer,
            product_area=product_area,
            created_at=datetime.now(timezone.utc)
        )


        # Generate embedding
        embedding = self.embedder.embed_text(text)

        # Search vector DB for similar historical tickets
        filter_meta = {"product_area": product_area} if product_area else None
        results = self.vector_store.similarity_search(
            collection_name="tickets",
            query_embedding=embedding,
            top_k=top_k,
            filter_metadata=None  # search across all tickets for semantic similarity
        )

        similar_tickets: List[SimilarTicket] = []
        for res in results:
            meta = res.get("metadata", {})
            similar_tickets.append(
                SimilarTicket(
                    ticket_id=res["id"],
                    similarity_score=res["score"],
                    resolution=meta.get("resolution", "N/A"),
                    assigned_developer=meta.get("assigned_developer", "Unassigned"),
                    product_area=meta.get("product_area")
                )
            )

        return {
            "complaint": complaint,
            "embedding": embedding,
            "similar_tickets": similar_tickets
        }
