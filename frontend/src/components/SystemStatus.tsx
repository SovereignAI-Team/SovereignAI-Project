import type { HealthResponse } from "../types";

interface Props {
  health: HealthResponse | null;
  error: string | null;
}

function Row({ label, ok, detail }: { label: string; ok: boolean | null; detail: string }) {
  const cls = ok === null ? "status-unknown" : ok ? "status-ready" : "status-failed";
  return (
    <div className="status-row" title={detail}>
      <span className={`status-dot ${cls}`} />
      <span className="status-label">{label}</span>
      <span className="status-detail">{detail}</span>
    </div>
  );
}

export default function SystemStatus({ health, error }: Props) {
  return (
    <div className="system-status">
      <div className="section-title">System status</div>
      {error || !health ? (
        <Row label="Backend" ok={false} detail={error ?? "Checking…"} />
      ) : (
        <>
          <Row label="Backend" ok={health.backend.ok} detail={health.backend.detail} />
          <Row label="Local model" ok={health.llm.ok} detail={health.llm.detail} />
          <Row label="Embeddings" ok={health.embedding.ok} detail={health.embedding.detail} />
          {health.ocr && <Row label="OCR (optional)" ok={health.ocr.ok} detail={health.ocr.detail} />}
        </>
      )}
    </div>
  );
}
