import { useState } from "react";
import type { Citation } from "../types";

export default function SourceCitation({ citation, index }: { citation: Citation; index: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`citation ${open ? "open" : ""}`}>
      <button className="citation-head" onClick={() => setOpen(!open)} aria-expanded={open}>
        <span className="citation-num">{index}</span>
        <span className="citation-title">{citation.document_name}</span>
        <span className="citation-page">p. {citation.page_number}</span>
        <span className="citation-chevron">{open ? "▾" : "▸"}</span>
      </button>
      {open && (
        <blockquote className="citation-excerpt">
          {citation.excerpt}
          <div className="citation-score">similarity {citation.score.toFixed(2)}</div>
        </blockquote>
      )}
    </div>
  );
}
