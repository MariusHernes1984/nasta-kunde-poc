import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

export default function PromptEditor() {
  const navigate = useNavigate();
  const [prompt, setPrompt] = useState("");
  const [defaultPrompt, setDefaultPrompt] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await fetch("/api/prompt");
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        const data = await res.json();
        setPrompt(data.prompt);
        setDefaultPrompt(data.default);
      } catch {
        setStatus({
          type: "error",
          message: "Kunne ikke hente prompt. Sjekk at backend kjører.",
        });
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function handleSave() {
    setSaving(true);
    setStatus(null);
    try {
      const res = await fetch("/api/prompt", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt }),
      });
      if (!res.ok) throw new Error(`API error: ${res.status}`);
      setStatus({ type: "success", message: "Prompt lagret!" });
    } catch {
      setStatus({ type: "error", message: "Kunne ikke lagre prompt." });
    } finally {
      setSaving(false);
    }
  }

  function handleReset() {
    setPrompt(defaultPrompt);
    setStatus(null);
  }

  const isModified = prompt !== defaultPrompt;

  if (loading) {
    return (
      <div className="detail-page">
        <div className="loading">Henter prompt...</div>
      </div>
    );
  }

  return (
    <div className="detail-page">
      <button onClick={() => navigate("/")} className="btn btn-back">
        Tilbake til søk
      </button>

      <div className="card prompt-editor-card">
        <div className="prompt-editor-header">
          <h2>AI Prompt Editor</h2>
          <span className="ai-badge">GPT 5.3</span>
        </div>
        <p className="prompt-description">
          Rediger system-prompten som styrer AI Kundeanalysen. Endringer trer i
          kraft umiddelbart for alle nye analyser.
        </p>

        {status && (
          <div
            className={
              status.type === "success" ? "success-banner" : "error-banner"
            }
          >
            {status.message}
          </div>
        )}

        <textarea
          className="prompt-textarea"
          value={prompt}
          onChange={(e) => {
            setPrompt(e.target.value);
            setStatus(null);
          }}
          rows={20}
          spellCheck={false}
        />

        <div className="prompt-footer">
          <div className="prompt-meta">
            {prompt.length} tegn
            {isModified && <span className="prompt-modified"> — endret</span>}
          </div>
          <div className="prompt-actions">
            <button
              onClick={handleReset}
              className="btn btn-secondary"
              disabled={!isModified || saving}
            >
              Tilbakestill standard
            </button>
            <button
              onClick={handleSave}
              className="btn btn-primary"
              disabled={saving || !prompt.trim()}
            >
              {saving ? "Lagrer..." : "Lagre prompt"}
            </button>
          </div>
        </div>
      </div>

      <div className="card">
        <h3>Tips</h3>
        <ul className="prompt-tips">
          <li>
            Prompten må instruere AI-en om å returnere JSON med{" "}
            <code>summary</code> og <code>upsells</code>-felter.
          </li>
          <li>
            AI-en mottar kundedata, maskinpark og ordrehistorikk automatisk.
          </li>
          <li>
            Endringer gjelder umiddelbart, men tilbakestilles ved omstart av
            tjenesten.
          </li>
          <li>Bruk «Tilbakestill standard» for å gå tilbake til originalen.</li>
        </ul>
      </div>
    </div>
  );
}
