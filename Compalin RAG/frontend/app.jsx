const { useState, useEffect } = React;

const PRESETS = [
  {
    label: "💳 Payment 504 Timeout",
    customer: "Acme Corp",
    productArea: "Checkout & Payments",
    text: "Customer is experiencing 504 gateway timeout on payments endpoint when paying with international Stripe credit cards."
  },
  {
    label: "🔐 OAuth SSO JWT Error",
    customer: "FinTech Global",
    productArea: "Authentication & SSO",
    text: "Users are unable to log in using OAuth2 SSO (Google / Okta). Server returns 'Invalid JWT signature' error on public key verify."
  },
  {
    label: "📊 DB Connection Pool Exhaustion",
    customer: "DataViz Inc",
    productArea: "Analytics & Reporting",
    text: "Dashboard analytics charts load extremely slowly or fail with database pool exhaustion exception during morning peak hours."
  },
  {
    label: "✉️ SendGrid Email Spam",
    customer: "Retail Plus",
    productArea: "Notification Service",
    text: "Automated email notifications for invoice receipts are not being delivered to customers or are ending up in spam folders."
  },
  {
    label: "⚡ Webhook 429 Rate Limit",
    customer: "LogiCorp",
    productArea: "Webhooks & API Gateway",
    text: "Webhook delivery fails intermittently with status 429 Too Many Requests when syncing bulk inventory updates."
  }
];

function App() {
  const [health, setHealth] = useState(null);
  const [complaintText, setComplaintText] = useState("");
  const [customer, setCustomer] = useState("");
  const [productArea, setProductArea] = useState("");
  
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState(null);
  const [error, setError] = useState(null);
  
  const [auditLogs, setAuditLogs] = useState([]);
  const [reindexing, setReindexing] = useState(false);

  // Check health on mount
  useEffect(() => {
    fetchHealth();
    fetchAuditLogs();
  }, []);

  const fetchHealth = async () => {
    try {
      const res = await fetch("/health");
      if (res.ok) {
        const data = await res.json();
        setHealth(data);
      }
    } catch (e) {
      console.warn("Backend health check failed:", e);
    }
  };

  const fetchAuditLogs = async () => {
    try {
      const res = await fetch("/api/v1/audit-logs?limit=50");
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (e) {
      console.warn("Failed to fetch audit logs:", e);
    }
  };

  const handleSelectPreset = (preset) => {
    setComplaintText(preset.text);
    setCustomer(preset.customer);
    setProductArea(preset.productArea);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!complaintText.trim()) return;

    setLoading(true);
    setError(null);
    setResponse(null);

    try {
      const res = await fetch("/api/v1/complaints/process", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: complaintText,
          customer: customer || null,
          product_area: productArea || null
        })
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to process complaint");
      }

      const data = await res.json();
      setResponse(data);
      // Refresh audit logs
      fetchAuditLogs();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReindexDocs = async () => {
    setReindexing(true);
    try {
      const res = await fetch("/api/v1/docs/reindex", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        alert(`Successfully re-indexed ${data.indexed_chunks} documentation chunks!`);
      } else {
        alert("Re-indexing failed.");
      }
    } catch (e) {
      alert("Error re-indexing docs: " + e.message);
    } finally {
      setReindexing(false);
    }
  };

  const getPriorityBadgeClass = (priority) => {
    switch (priority?.toLowerCase()) {
      case "critical": return "badge-priority badge-critical";
      case "high": return "badge-priority badge-high";
      case "medium": return "badge-priority badge-medium";
      default: return "badge-priority badge-low";
    }
  };

  return (
    <div className="app-container">
      {/* Header Navbar */}
      <header className="header-navbar">
        <div className="brand-logo">
          <div className="brand-icon">⚡</div>
          <div>
            <div className="brand-title">Compalin RAG Triage Engine</div>
            <div className="brand-subtitle">AI Complaint Routing & Developer Assignment Platform</div>
          </div>
        </div>
        <div className="header-actions">
          <button 
            id="reindex-docs-btn" 
            className="btn-secondary" 
            onClick={handleReindexDocs} 
            disabled={reindexing}
          >
            {reindexing ? "Indexing..." : "🔄 Re-Index Docs"}
          </button>
          <div className="status-pill" id="health-status-pill">
            <span className="status-dot"></span>
            {health ? `${health.embedding_model}` : "Backend Connected"}
          </div>
        </div>
      </header>

      {/* Main Grid */}
      <div className="main-grid">
        {/* Left Column: Complaint Intake Form */}
        <div className="glass-panel">
          <div className="section-header">
            <h2 className="section-title">📥 Customer Complaint Intake</h2>
          </div>

          {/* Quick Presets */}
          <div className="form-group">
            <label className="form-label">Quick Sample Presets</label>
            <div className="preset-chips">
              {PRESETS.map((preset, idx) => (
                <button
                  key={idx}
                  id={`preset-btn-${idx}`}
                  type="button"
                  className="chip-btn"
                  onClick={() => handleSelectPreset(preset)}
                >
                  {preset.label}
                </button>
              ))}
            </div>
          </div>

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label className="form-label">Complaint Description *</label>
              <textarea
                id="complaint-text-input"
                className="form-textarea"
                placeholder="Describe the technical issue, error codes, stack traces, or customer bug details..."
                value={complaintText}
                onChange={(e) => setComplaintText(e.target.value)}
                required
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Customer Name</label>
                <input
                  id="customer-input"
                  type="text"
                  className="form-input"
                  placeholder="e.g. Acme Corp"
                  value={customer}
                  onChange={(e) => setCustomer(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label className="form-label">Product Area</label>
                <select
                  id="product-area-select"
                  className="form-select"
                  value={productArea}
                  onChange={(e) => setProductArea(e.target.value)}
                >
                  <option value="">Unspecified</option>
                  <option value="Checkout & Payments">Checkout & Payments</option>
                  <option value="Authentication & SSO">Authentication & SSO</option>
                  <option value="Analytics & Reporting">Analytics & Reporting</option>
                  <option value="Notification Service">Notification Service</option>
                  <option value="Webhooks & API Gateway">Webhooks & API Gateway</option>
                </select>
              </div>
            </div>

            {error && (
              <div style={{ color: "#EF4444", fontSize: "0.85rem", marginBottom: "1rem" }}>
                ⚠️ {error}
              </div>
            )}

            <button
              id="submit-triage-btn"
              type="submit"
              className="btn-primary"
              disabled={loading || !complaintText.trim()}
            >
              {loading ? (
                <>
                  <div className="spinner"></div>
                  <span>Running RAG & MCP Pipeline...</span>
                </>
              ) : (
                <span>🚀 Triage & Assign Developer</span>
              )}
            </button>
          </form>
        </div>

        {/* Right Column: AI Triage Decision & RAG Context */}
        <div>
          {response ? (
            <div>
              {/* Decision Panel */}
              <div className="decision-card" id="decision-card-panel">
                <div className="decision-header">
                  <div className="dev-info">
                    <div className="dev-avatar">
                      {response.decision.assigned_developer.charAt(0)}
                    </div>
                    <div>
                      <div className="dev-name" id="assigned-developer-name">
                        {response.decision.assigned_developer}
                      </div>
                      <div className="dev-meta">
                        Assigned Developer / Team Lead
                      </div>
                    </div>
                  </div>
                  <span className={getPriorityBadgeClass(response.decision.priority)} id="priority-level-badge">
                    {response.decision.priority} Priority
                  </span>
                </div>

                <div className="decision-meta-grid">
                  <div className="meta-box">
                    <div className="meta-label">Jira Issue Key</div>
                    <div className="meta-value" id="jira-issue-key-val">
                      {response.decision.jira_issue_key || "PROJ-101"}
                    </div>
                  </div>
                  <div className="meta-box">
                    <div className="meta-label">MCP Notification</div>
                    <div className="meta-value" style={{ color: "#10B981" }}>
                      ✓ Dispatched
                    </div>
                  </div>
                </div>

                <div className="reasoning-box">
                  <div style={{ fontWeight: 600, color: "#FFF", marginBottom: "0.25rem" }}>
                    🧠 AI Triage Reasoning:
                  </div>
                  <p id="decision-reasoning-text">{response.decision.reasoning}</p>
                </div>
              </div>

              {/* Similar Tickets */}
              <div className="glass-panel" style={{ marginBottom: "1.5rem" }}>
                <h3 className="section-title" style={{ marginBottom: "1rem" }}>
                  🔎 Similar Resolved Historical Tickets ({response.similar_tickets?.length || 0})
                </h3>
                {response.similar_tickets?.map((t, idx) => (
                  <div key={idx} className="ticket-item">
                    <div className="item-header">
                      <span className="item-title">{t.ticket_id} ({t.product_area || "General"})</span>
                      <span className="score-badge">
                        {(t.similarity_score * 100).toFixed(1)}% Match
                      </span>
                    </div>
                    <div className="item-body">
                      <div><strong>Assigned Dev:</strong> {t.assigned_developer}</div>
                      <div><strong>Resolution:</strong> {t.resolution}</div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Retrieved Runbooks */}
              <div className="glass-panel">
                <h3 className="section-title" style={{ marginBottom: "1rem" }}>
                  📚 Retrieved Runbooks & Ownership Docs ({response.retrieved_docs?.length || 0})
                </h3>
                {response.retrieved_docs?.map((doc, idx) => (
                  <div key={idx} className="doc-item">
                    <div className="item-header">
                      <span className="item-title">📄 {doc.source}</span>
                      <span className="score-badge">
                        Score: {doc.relevance_score}
                      </span>
                    </div>
                    <div className="item-body" style={{ fontStyle: "italic" }}>
                      "{doc.content.slice(0, 200)}..."
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="glass-panel empty-state">
              <div className="empty-icon">🤖</div>
              <h3>Ready for Complaint Triage</h3>
              <p style={{ fontSize: "0.9rem", color: "var(--text-muted)", marginTop: "0.5rem" }}>
                Select a quick preset or type a customer complaint to run semantic ticket search, RAG runbook retrieval, and automated MCP tool assignment.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Audit Log Table */}
      <div className="glass-panel">
        <div className="section-header">
          <h2 className="section-title">📜 System Audit Log History</h2>
          <button id="refresh-audit-logs-btn" className="btn-secondary" onClick={fetchAuditLogs}>
            🔄 Refresh History
          </button>
        </div>

        <div className="table-wrapper">
          <table className="custom-table" id="audit-logs-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Ticket ID</th>
                <th>Assigned Developer</th>
                <th>Priority</th>
                <th>Jira Issue Key</th>
                <th>Reasoning</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <tr key={log.id}>
                    <td>#{log.id}</td>
                    <td style={{ fontFamily: "var(--font-mono)", fontWeight: 600 }}>{log.ticket_id}</td>
                    <td style={{ color: "#FFF", fontWeight: 600 }}>{log.developer}</td>
                    <td>
                      <span className={getPriorityBadgeClass(log.priority)}>
                        {log.priority}
                      </span>
                    </td>
                    <td style={{ fontFamily: "var(--font-mono)", color: "var(--primary-500)" }}>
                      {log.jira_issue_key || "N/A"}
                    </td>
                    <td style={{ maxWidth: "300px" }}>{log.reasoning}</td>
                    <td style={{ fontSize: "0.8rem", color: "var(--text-subtle)" }}>
                      {log.timestamp ? new Date(log.timestamp).toLocaleString() : "N/A"}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: "center", color: "var(--text-subtle)", padding: "2rem" }}>
                    No audit records logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// Mount React App
const rootElement = document.getElementById("root");
const root = ReactDOM.createRoot(rootElement);
root.render(<App />);
