import { useEffect, useState } from "react";

interface Upsell {
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
}

interface SummaryData {
  summary: string;
  upsells: Upsell[];
}

interface Props {
  kundenummer: number;
}

function priorityIcon(priority: string): string {
  switch (priority) {
    case "high":
      return "!!!";
    case "medium":
      return "!!";
    case "low":
      return "!";
    default:
      return "";
  }
}

export default function CustomerSummary({ kundenummer }: Props) {
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const res = await fetch("/api/customer-summary", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kundenummer }),
        });
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const json = await res.json();
        if (!cancelled) setData(json);
      } catch {
        if (!cancelled) setError("Kunne ikke generere AI-analyse.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [kundenummer]);

  const highCount = data?.upsells.filter((u) => u.priority === "high").length ?? 0;

  if (loading) {
    return (
      <div className="card summary-card">
        <div className="summary-header">
          <h3>AI Kundeanalyse</h3>
          <span className="ai-badge">GPT 5.3</span>
        </div>
        <div className="summary-loading">
          <div className="pulse-dot" />
          Analyserer kundedata...
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="card summary-card">
        <div className="summary-header clickable" onClick={() => setCollapsed(!collapsed)}>
          <h3>AI Kundeanalyse</h3>
          <span className="ai-badge">GPT 5.3</span>
          <span className="collapse-toggle">{collapsed ? "+" : "\u2212"}</span>
        </div>
        {!collapsed && (
          <p className="empty-state">{error || "Ingen analyse tilgjengelig"}</p>
        )}
      </div>
    );
  }

  return (
    <div className={`card summary-card ${collapsed ? "summary-collapsed" : ""}`}>
      <div className="summary-header clickable" onClick={() => setCollapsed(!collapsed)}>
        <h3>AI Kundeanalyse</h3>
        <span className="ai-badge">GPT 5.3</span>
        {collapsed && highCount > 0 && (
          <span className="summary-mini-badge">{highCount} viktig{highCount > 1 ? "e" : ""}</span>
        )}
        <span className="collapse-toggle">{collapsed ? "+" : "\u2212"}</span>
      </div>

      {!collapsed && (
        <>
          <div className="summary-text">{data.summary}</div>

          {data.upsells.length > 0 && (
            <div className="upsell-section">
              <h4>Salgsanbefalinger</h4>
              <div className="upsell-list">
                {data.upsells.map((u, i) => (
                  <div key={i} className={`upsell-item upsell-${u.priority}`}>
                    <div className="upsell-priority">
                      <span className={`priority-dot priority-${u.priority}`}>
                        {priorityIcon(u.priority)}
                      </span>
                    </div>
                    <div className="upsell-content">
                      <strong>{u.title}</strong>
                      <p>{u.description}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
