/**
 * API client for communicating with the Azure AI chat backend.
 * Used by AiChat component for free-form questions and proff.no/at.no lookups.
 */

const AGENT_API_URL = import.meta.env.VITE_AGENT_API_URL || "/api";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AgentResponse {
  message: string;
  threadId: string;
}

let currentThreadId: string | null = null;

export async function sendMessage(
  message: string,
  threadId?: string
): Promise<AgentResponse> {
  const response = await fetch(`${AGENT_API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      threadId: threadId || currentThreadId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Agent API error: ${response.status}`);
  }

  const data = await response.json();
  currentThreadId = data.threadId;
  return data;
}

export function resetThread() {
  currentThreadId = null;
}
