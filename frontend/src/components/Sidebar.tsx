import FileUploader from "./FileUploader";
import DocumentList from "./DocumentList";
import SystemStatus from "./SystemStatus";
import type { DocumentInfo, HealthResponse } from "../types";

interface Props {
  documents: DocumentInfo[];
  selected: string[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onUploaded: (doc: DocumentInfo) => void;
  health: HealthResponse | null;
  healthError: string | null;
  loadError: string | null;
  theme: "light" | "dark";
  onToggleTheme: () => void;
}

export default function Sidebar(p: Props) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">S</div>
        <div>
          <div className="brand-name">SovereignAI</div>
          <div className="brand-sub">Local document assistant</div>
        </div>
        <button className="icon-btn" onClick={p.onToggleTheme} title="Toggle light/dark theme" aria-label="Toggle theme">
          {p.theme === "dark" ? "☀" : "☾"}
        </button>
      </div>

      <FileUploader onUploaded={p.onUploaded} />

      {p.loadError && <div className="banner banner-error">{p.loadError}</div>}

      <div className="section-title">Documents ({p.documents.length})</div>
      <DocumentList documents={p.documents} selected={p.selected} onToggle={p.onToggle} onDelete={p.onDelete} />

      <SystemStatus health={p.health} error={p.healthError} />
    </aside>
  );
}
