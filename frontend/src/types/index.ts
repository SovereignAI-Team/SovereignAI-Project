export type DocStatus = "processing" | "ready" | "failed";

export interface DocumentInfo {
  id: string;
  original_name: string;
  size_bytes: number;
  page_count: number;
  chunk_count: number;
  status: DocStatus;
  used_ocr: boolean;
  error_message: string | null;
  created_at: string;
}

export interface UploadResponse {
  document: DocumentInfo;
  message: string;
  duplicate: boolean;
}

export interface Citation {
  document_id: string;
  document_name: string;
  page_number: number;
  excerpt: string;
  score: number;
}

export interface AskResponse {
  answer: string;
  answered: boolean;
  citations: Citation[];
  model: string;
}

export interface ComponentStatus {
  ok: boolean;
  detail: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  backend: ComponentStatus;
  database: ComponentStatus;
  embedding: ComponentStatus;
  llm: ComponentStatus;
  ocr: ComponentStatus | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant" | "error";
  text: string;
  answered?: boolean;
  citations?: Citation[];
}
