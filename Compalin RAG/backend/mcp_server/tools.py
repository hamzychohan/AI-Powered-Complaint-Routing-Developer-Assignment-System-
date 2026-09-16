import logging
from typing import Dict, Any, Optional
from backend.mcp_server.jira_adapter import JiraAdapter
from backend.db.audit_db import AuditDB
from backend.config import settings

logger = logging.getLogger(__name__)

# Singletons for adapter and database
jira_adapter = JiraAdapter()
audit_db = AuditDB(db_path=settings.SQLITE_DB_PATH)

def assign_ticket(developer: str, priority: str, ticket_id: str, summary: Optional[str] = None) -> Dict[str, Any]:
    """
    MCP Tool 1: Assigns ticket in ticketing system (Jira or Mock).
    """
    try:
        result = jira_adapter.assign_ticket(
            ticket_id=ticket_id,
            developer=developer,
            priority=priority,
            summary=summary
        )
        return result
    except Exception as e:
        logger.error(f"Error in assign_ticket tool: {e}")
        return {
            "success": False,
            "error": str(e),
            "jira_issue_key": None
        }

def notify_developer(developer: str, ticket_summary: str) -> Dict[str, Any]:
    """
    MCP Tool 2: Sends notification (email / Slack mock) to assigned developer.
    """
    try:
        logger.info(f"[MCP Tool: notify_developer] Notification sent to {developer}: '{ticket_summary}'")
        return {
            "success": True,
            "developer": developer,
            "message": f"Notification successfully dispatched to {developer}"
        }
    except Exception as e:
        logger.error(f"Error in notify_developer tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def log_assignment(ticket_id: str, developer: str, priority: str, reasoning: str, jira_issue_key: Optional[str] = None) -> Dict[str, Any]:
    """
    MCP Tool 3: Writes audit log record to SQLite database.
    """
    try:
        entry = audit_db.log_assignment(
            ticket_id=ticket_id,
            developer=developer,
            priority=priority,
            reasoning=reasoning,
            jira_issue_key=jira_issue_key
        )
        logger.info(f"[MCP Tool: log_assignment] Audit record #{entry.id} saved for {ticket_id}")
        return {
            "success": True,
            "audit_id": entry.id,
            "message": f"Audit record #{entry.id} written for ticket {ticket_id}"
        }
    except Exception as e:
        logger.error(f"Error in log_assignment tool: {e}")
        return {
            "success": False,
            "error": str(e)
        }
