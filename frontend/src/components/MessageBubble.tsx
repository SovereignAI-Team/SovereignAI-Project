import SourceCitation from "./SourceCitation";
import type { ChatMessage } from "../types";

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const cls = isUser ? "bubble user" : message.role === "error" ? "bubble error" : "bubble assistant";
  return (
    <div className={`msg-row ${isUser ? "right" : "left"}`}>
      <div className={cls}>
        <div className="bubble-text">{message.text}</div>
        {message.role === "assistant" && message.answered === false && (
          <div className="bubble-note">No supporting content found in the selected documents.</div>
        )}
        {message.citations && message.citations.length > 0 && (
          <div className="citations">
            <div className="citations-title">Sources</div>
            {message.citations.map((c, i) => (
              <SourceCitation key={`${c.document_id}-${i}`} citation={c} index={i + 1} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
