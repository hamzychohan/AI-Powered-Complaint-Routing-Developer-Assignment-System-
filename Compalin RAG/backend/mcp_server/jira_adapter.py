import logging
import random
from typing import Dict, Any, Optional
# pyrefly: ignore [missing-import]
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)

class JiraAdapter:
    """
    Dual-mode Jira adapter.
    Uses Jira REST API v3 when credentials exist in settings,
    otherwise defaults to local mock adapter.
    """
    
    def __init__(self):
        self.server_url = settings.JIRA_SERVER_URL.rstrip('/') if settings.JIRA_SERVER_URL else None
        self.user_email = settings.JIRA_USER_EMAIL
        self.api_token = settings.JIRA_API_TOKEN
        self.project_key = settings.JIRA_PROJECT_KEY or "COMP"
        self.is_real_jira = bool(self.server_url and self.api_token)
        self._mock_jira_tickets: Dict[str, Dict[str, Any]] = {}

    def assign_ticket(self, ticket_id: str, developer: str, priority: str, summary: Optional[str] = None) -> Dict[str, Any]:
        """
        Creates or assigns a Jira issue.
        Returns dict with status and jira_issue_key.
        """
        if self.is_real_jira:
            return self._real_jira_assign(ticket_id, developer, priority, summary)
        else:
            return self._mock_jira_assign(ticket_id, developer, priority, summary)

    def _mock_jira_assign(self, ticket_id: str, developer: str, priority: str, summary: Optional[str]) -> Dict[str, Any]:
        mock_issue_key = f"{self.project_key}-{random.randint(1000, 9999)}"
        ticket_record = {
            "jira_issue_key": mock_issue_key,
            "ticket_id": ticket_id,
            "developer": developer,
            "priority": priority,
            "summary": summary or f"Complaint Ticket {ticket_id}",
            "mode": "MOCK"
        }
        self._mock_jira_tickets[ticket_id] = ticket_record
        logger.info(f"[JiraAdapter - MOCK] Created issue {mock_issue_key} for {developer} with priority {priority}")
        return {
            "success": True,
            "jira_issue_key": mock_issue_key,
            "message": f"Successfully created mock Jira issue {mock_issue_key} assigned to {developer}"
        }

    def _real_jira_assign(self, ticket_id: str, developer: str, priority: str, summary: Optional[str]) -> Dict[str, Any]:
        endpoint = f"{self.server_url}/rest/api/3/issue"
        auth = (self.user_email, self.api_token)
        payload = {
            "fields": {
                "project": {"key": self.project_key},
                "summary": summary or f"[{ticket_id}] Customer Complaint",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": f"Assigned to {developer} with priority {priority}."}
                            ]
                        }
                    ]
                },
                "issuetype": {"name": "Bug"}
            }
        }
        try:
            with httpx.Client(auth=auth, timeout=10.0) as client:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                data = response.json()
                issue_key = data.get("key", f"{self.project_key}-UNKNOWN")
                logger.info(f"[JiraAdapter - REAL] Created Jira issue {issue_key}")
                return {
                    "success": True,
                    "jira_issue_key": issue_key,
                    "message": f"Created Jira Cloud issue {issue_key}"
                }
        except Exception as e:
            logger.error(f"[JiraAdapter - REAL] Error creating Jira issue: {e}")
            # Fallback to mock on error
            return self._mock_jira_assign(ticket_id, developer, priority, summary)
