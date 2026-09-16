import json
import logging
from typing import List, Dict, Any, Optional
from backend.config import settings
from backend.models import Complaint, SimilarTicket, DocChunk, AssignmentDecision
from backend.mcp_server import tools

logger = logging.getLogger(__name__)

class LLMDecisionEngine:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model = settings.LLM_MODEL

    def _build_prompt(self, complaint: Complaint, similar_tickets: List[SimilarTicket], docs: List[DocChunk]) -> str:
        tickets_text = ""
        for idx, t in enumerate(similar_tickets, 1):
            tickets_text += (
                f"{idx}. Ticket ID: {t.ticket_id} (Similarity: {t.similarity_score:.2f})\n"
                f"   Assigned Dev: {t.assigned_developer}\n"
                f"   Resolution: {t.resolution}\n\n"
            )

        docs_text = ""
        for idx, d in enumerate(docs, 1):
            docs_text += (
                f"{idx}. Source: {d.source} (Relevance Score: {d.relevance_score:.2f})\n"
                f"   Content Snippet: {d.content}\n\n"
            )

        prompt = f"""You are an expert AI Operations Engineer responsible for triaging customer complaints, assigning the right software developer/team, and designating the appropriate priority level.

### INCOMING CUSTOMER COMPLAINT
- Ticket ID: {complaint.id}
- Customer: {complaint.customer or 'N/A'}
- Product Area: {complaint.product_area or 'Unspecified'}
- Complaint Text: "{complaint.text}"

### HISTORICAL SIMILAR TICKETS & RESOLUTIONS
{tickets_text or 'No historical similar tickets found.'}

### INTERNAL DEVELOPER DOCUMENTATION & RUNBOOKS
{docs_text or 'No developer documentation retrieved.'}

### TRIAGE INSTRUCTIONS
1. Select the BEST assigned developer/team based on the codebase ownership map, historical ticket assignees, and runbook instructions.
2. Determine the priority level: MUST be one of ["low", "medium", "high", "critical"].
3. Provide a clear, concise rationale (reasoning) explaining why this developer and priority were selected.

Return ONLY a valid JSON object matching this schema:
{{
  "assigned_developer": "Developer Name / Team Lead",
  "priority": "low" | "medium" | "high" | "critical",
  "reasoning": "Explanation of your decision based on context..."
}}
"""
        return prompt

    def decide_and_execute(
        self,
        complaint: Complaint,
        similar_tickets: List[SimilarTicket],
        retrieved_docs: List[DocChunk]
    ) -> AssignmentDecision:
        prompt = self._build_prompt(complaint, similar_tickets, retrieved_docs)
        raw_decision = self._call_llm(prompt)

        developer = raw_decision.get("assigned_developer", "Unassigned Support Team")
        priority = raw_decision.get("priority", "medium").lower()
        if priority not in ["low", "medium", "high", "critical"]:
            priority = "medium"
        reasoning = raw_decision.get("reasoning", "Assigned based on automated triage rules.")

        # Execute MCP Server Tool Actions
        # Tool 1: Assign ticket in Jira / Ticketing System
        jira_res = tools.assign_ticket(
            ticket_id=complaint.id,
            developer=developer,
            priority=priority,
            summary=f"[{complaint.product_area or 'General'}] {complaint.text[:80]}..."
        )
        jira_issue_key = jira_res.get("jira_issue_key")

        # Tool 2: Notify Developer
        tools.notify_developer(
            developer=developer,
            ticket_summary=f"Assigned Complaint Ticket {complaint.id} (Priority: {priority.upper()})"
        )

        # Tool 3: Log Audit Record
        tools.log_assignment(
            ticket_id=complaint.id,
            developer=developer,
            priority=priority,
            reasoning=reasoning,
            jira_issue_key=jira_issue_key
        )

        return AssignmentDecision(
            complaint_id=complaint.id,
            assigned_developer=developer,
            priority=priority,
            reasoning=reasoning,
            jira_issue_key=jira_issue_key,
            notification_sent=True
        )

    def _call_llm(self, prompt: str) -> Dict[str, Any]:
        """Calls the configured LLM API (Groq, OpenAI, or Anthropic) with heuristic fallback."""
        
        # 1. Try Groq API
        if (self.provider == "groq" or settings.GROQ_API_KEY) and settings.GROQ_API_KEY:
            try:
                # pyrefly: ignore [missing-import]
                from groq import Groq
                client = Groq(api_key=settings.GROQ_API_KEY)
                completion = client.chat.completions.create(
                    model=self.model or "llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                content = completion.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                logger.warning(f"Groq API call failed: {e}. Trying secondary provider/fallback.")

        # 2. Try OpenAI API
        if (self.provider == "openai" or settings.OPENAI_API_KEY) and settings.OPENAI_API_KEY:
            try:
                # pyrefly: ignore [missing-import]
                from openai import OpenAI
                client = OpenAI(api_key=settings.OPENAI_API_KEY)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                content = response.choices[0].message.content
                return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenAI API call failed: {e}. Trying secondary provider/fallback.")

        # 3. Try Anthropic API
        if (self.provider == "anthropic" or settings.ANTHROPIC_API_KEY) and settings.ANTHROPIC_API_KEY:
            try:
                # pyrefly: ignore [missing-import]
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
                response = client.messages.create(
                    model="claude-3-5-sonnet-latest",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                text = response.content[0].text
                # Extract json substring
                start = text.find("{")
                end = text.rfind("}") + 1
                if start >= 0 and end > start:
                    return json.loads(text[start:end])
            except Exception as e:
                logger.warning(f"Anthropic API call failed: {e}. Using fallback triage engine.")

        # 4. Fallback Rule-Based Heuristic Decision Engine (for keyless local execution)
        logger.info("Executing rule-based heuristic triage engine (API keys unconfigured or unreachable).")
        return self._heuristic_triage(prompt)

    def _heuristic_triage(self, prompt: str) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        if "checkout" in prompt_lower or "payment" in prompt_lower or "stripe" in prompt_lower or "504" in prompt_lower:
            return {
                "assigned_developer": "Alice Smith (Payments Team)",
                "priority": "high",
                "reasoning": "Matched payments/checkout failure signatures in ownership map and runbook."
            }
        elif "sso" in prompt_lower or "oauth" in prompt_lower or "jwt" in prompt_lower or "login" in prompt_lower:
            return {
                "assigned_developer": "Bob Jones (Auth & Security Team)",
                "priority": "critical" if "invalid jwt" in prompt_lower else "high",
                "reasoning": "Matched authentication and SSO issue signature from auth service postmortem."
            }
        elif "chart" in prompt_lower or "analytics" in prompt_lower or "database" in prompt_lower or "pgbouncer" in prompt_lower:
            return {
                "assigned_developer": "Charlie Brown (Data Platform Team)",
                "priority": "medium",
                "reasoning": "Matched database connection pool & analytics bottleneck patterns."
            }
        elif "email" in prompt_lower or "notification" in prompt_lower or "sendgrid" in prompt_lower or "spam" in prompt_lower:
            return {
                "assigned_developer": "Diana Prince (Infra & Email Team)",
                "priority": "medium",
                "reasoning": "Matched email notification delivery and SPF/DKIM DNS configuration issues."
            }
        else:
            return {
                "assigned_developer": "Ethan Hunt (Integration Platform)",
                "priority": "medium",
                "reasoning": "Assigned to Integration Platform triage team based on semantic context."
            }
