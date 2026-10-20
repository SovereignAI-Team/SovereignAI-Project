import { useRef, useState } from "react";
import { api } from "../api/client";
import type { DocumentInfo } from "../types";

interface Props {
  onUploaded: (doc: DocumentInfo) => void;
}

const MAX_MB = 25; // mirrors the backend default; the backend is the real authority

export default function FileUploader({ onUploaded }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);
  const [phase, setPhase] = useState<"uploading" | "processing">("uploading");
  const [message, setMessage] = useState<{ kind: "error" | "info"; text: string } | null>(null);

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    setMessage(null);
    for (const file of Array.from(files)) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setMessage({ kind: "error", text: `${file.name}: only PDF files are supported.` });
        continue;
      }
      if (file.size > MAX_MB * 1024 * 1024) {
        setMessage({ kind: "error", text: `${file.name}: larger than ${MAX_MB} MB.` });
        continue;
      }
      setBusy(true);
      setProgress(0);
      setPhase("uploading");
      try {
        const res = await api.uploadDocument(file, (pct, ph) => {
          setProgress(pct);
          setPhase(ph);
        });
        onUploaded(res.document);
        setMessage({
          kind: res.document.status === "ready" ? "info" : "error",
          text: `${file.name}: ${res.message}`,
        });
      } catch (e) {
        setMessage({ kind: "error", text: `${file.name}: ${(e as Error).message}` });
      } finally {
        setBusy(false);
      }
    }
    if (inputRef.current) inputRef.current.value = "";
  }

  return (
    <div>
      <div
        className={`dropzone ${dragging ? "dragging" : ""} ${busy ? "busy" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (!busy) handleFiles(e.dataTransfer.files);
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          multiple
          hidden
          onChange={(e) => handleFiles(e.target.files)}
        />
        {busy ? (
          <div className="progress-wrap">
            <div className="progress-label">
              {phase === "uploading" ? `Uploading… ${progress}%` : "Extracting, embedding and indexing…"}
            </div>
            <div className={`progress-bar ${phase === "processing" ? "indeterminate" : ""}`}>
              <div style={{ width: phase === "uploading" ? `${progress}%` : "40%" }} />
            </div>
          </div>
        ) : (
          <>
            <button className="btn btn-primary" onClick={() => inputRef.current?.click()}>
              Upload PDF
            </button>
            <div className="dropzone-hint">or drag &amp; drop here</div>
          </>
        )}
      </div>
      {message && <div className={`banner ${message.kind === "error" ? "banner-error" : "banner-info"}`}>{message.text}</div>}
    </div>
  );
}
