import type { DocumentInfo } from "../types";

interface Props {
  documents: DocumentInfo[];
  selected: string[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
}

function formatSize(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function DocumentList({ documents, selected, onToggle, onDelete }: Props) {
  if (documents.length === 0) {
    return <div className="empty-small">No documents yet. Upload a PDF to get started.</div>;
  }
  return (
    <ul className="doc-list">
      {documents.map((d) => {
        const ready = d.status === "ready";
        return (
          <li key={d.id} className={`doc-item ${selected.includes(d.id) ? "selected" : ""}`}>
            <label className="doc-main">
              <input type="checkbox" disabled={!ready} checked={selected.includes(d.id)} onChange={() => onToggle(d.id)} />
              <div className="doc-text">
                <div className="doc-name" title={d.original_name}>
                  {d.original_name}
                </div>
                <div className="doc-meta">
                  <span className={`status-dot status-${d.status}`} />
                  {d.status === "ready" && `${d.page_count} pages · ${d.chunk_count} chunks · ${formatSize(d.size_bytes)}`}
                  {d.status === "processing" && "Processing…"}
                  {d.status === "failed" && "Failed"}
                  {d.used_ocr && " · OCR"}
                </div>
                {d.status === "failed" && d.error_message && <div className="doc-error">{d.error_message}</div>}
              </div>
            </label>
            <button
              className="icon-btn danger"
              title="Remove document and its data"
              aria-label={`Remove ${d.original_name}`}
              onClick={() => {
                if (window.confirm(`Remove "${d.original_name}" and all its indexed data?`)) onDelete(d.id);
              }}
            >
              ✕
            </button>
          </li>
        );
      })}
    </ul>
  );
}
