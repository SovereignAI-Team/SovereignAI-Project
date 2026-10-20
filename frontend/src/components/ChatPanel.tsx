import { FormEvent, useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import MessageBubble from "./MessageBubble";
import type { ChatMessage, DocumentInfo } from "../types";

interface Props {
  documents: DocumentInfo[];
  selectedIds: string[];
  llmReady: boolean;
}

let counter = 0;
const nextId = () => `m${++counter}`;

export default function ChatPanel({ documents, selectedIds, llmReady }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const canAsk = selectedIds.length > 0 && !loading && input.trim().length > 0;

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canAsk) return;
    const question = input.trim();
    setInput("");
    setMessages((m) => [...m, { id: nextId(), role: "user", text: question }]);
    setLoading(true);
    try {
      const res = await api.ask(question, selectedIds);
      setMessages((m) => [
        ...m,
        { id: nextId(), role: "assistant", text: res.answer, answered: res.answered, citations: res.citations },
      ]);
    } catch (err) {
      setMessages((m) => [...m, { id: nextId(), role: "error", text: (err as Error).message }]);
    } finally {
      setLoading(false);
    }
  }

  const selectedNames = documents.filter((d) => selectedIds.includes(d.id)).map((d) => d.original_name);

  return (
    <main className="chat">
      <header className="chat-header">
        <div>
          <div className="chat-title">Ask your documents</div>
          <div className="chat-sub">
            {selectedNames.length === 0
              ? "Select one or more ready documents in the sidebar"
              : `Searching: ${selectedNames.join(", ")}`}
          </div>
        </div>
        {messages.length > 0 && (
          <button className="btn btn-ghost" onClick={() => setMessages([])}>
            Clear chat
          </button>
        )}
      </header>

      <div className="chat-scroll">
        {messages.length === 0 && !loading ? (
          <div className="empty-state">
            <div className="empty-icon">📄</div>
            <h2>Private answers from your PDFs</h2>
            <p>
              {documents.length === 0
                ? "Upload a PDF in the sidebar to begin. Everything is processed on this computer."
                : "Tick a document in the sidebar, then ask a question. Answers include page citations."}
            </p>
          </div>
        ) : (
          messages.map((m) => <MessageBubble key={m.id} message={m} />)
        )}
        {loading && (
          <div className="msg-row left">
            <div className="bubble assistant typing">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
              <span className="typing-label">Searching documents and thinking…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {!llmReady && <div className="banner banner-warn chat-banner">The local model looks unavailable (see System status). Questions may fail until Ollama is running.</div>}

      <form className="composer" onSubmit={onSubmit}>
        <input
          className="composer-input"
          placeholder={selectedIds.length === 0 ? "Select a document first…" : "Ask a question about the selected documents…"}
          value={input}
          maxLength={2000}
          disabled={selectedIds.length === 0}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="btn btn-primary" type="submit" disabled={!canAsk}>
          {loading ? "…" : "Send"}
        </button>
      </form>
    </main>
  );
}
