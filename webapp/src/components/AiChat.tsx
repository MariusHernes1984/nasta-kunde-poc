import { useState, useRef, useEffect, forwardRef, useImperativeHandle } from "react";
import { sendMessage, type ChatMessage } from "../api/agent";

export interface AiChatHandle {
  send: (message: string) => void;
}

interface Props {
  initialContext?: string;
}

export default forwardRef<AiChatHandle, Props>(function AiChat({ initialContext }, ref) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const hasInitialized = useRef(false);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    if (initialContext && !hasInitialized.current) {
      hasInitialized.current = true;
      handleSend(initialContext);
    }
  }, [initialContext]);

  useImperativeHandle(ref, () => ({
    send: (message: string) => handleSend(message),
  }));

  async function handleSend(text?: string) {
    const messageText = text || input.trim();
    if (!messageText || loading) return;

    if (!text) setInput("");

    const userMsg: ChatMessage = { role: "user", content: messageText };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const response = await sendMessage(messageText);
      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: response.message,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      const errorMsg: ChatMessage = {
        role: "assistant",
        content: `Feil: Kunne ikke kontakte AI-agenten. ${err instanceof Error ? err.message : ""}`,
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="card chat-card">
      <h3>AI Assistent</h3>
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="empty-state">
            Still spørsmål om kunden, maskinene eller ordrene...
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message chat-${msg.role}`}>
            <div className="chat-bubble">
              <span className="chat-role">
                {msg.role === "user" ? "Du" : "AI"}
              </span>
              <div className="chat-content">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="chat-message chat-assistant">
            <div className="chat-bubble">
              <span className="chat-role">AI</span>
              <div className="chat-content loading-dots">Tenker...</div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="chat-input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Skriv et spørsmål..."
          rows={2}
          disabled={loading}
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !input.trim()}
          className="btn btn-primary"
        >
          Send
        </button>
      </div>
    </div>
  );
});
