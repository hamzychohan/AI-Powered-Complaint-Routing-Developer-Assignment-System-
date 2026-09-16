from backend.mcp_server import tools

def test_mcp_assign_ticket():
    res = tools.assign_ticket(
        developer="Alice Smith",
        priority="high",
        ticket_id="TICK-TEST-1"
    )
    assert res["success"] is True
    assert "jira_issue_key" in res
    assert res["jira_issue_key"].startswith("COMP-")

def test_mcp_notify_developer():
    res = tools.notify_developer(
        developer="Alice Smith",
        ticket_summary="Assigned complaint TICK-TEST-1"
    )
    assert res["success"] is True
    assert res["developer"] == "Alice Smith"

def test_mcp_log_assignment(tmp_path):
    res = tools.log_assignment(
        ticket_id="TICK-TEST-1",
        developer="Alice Smith",
        priority="high",
        reasoning="Payment checkout failure match"
    )
    assert res["success"] is True
    assert "audit_id" in res
