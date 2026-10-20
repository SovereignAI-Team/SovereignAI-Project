import type { AskResponse, DocumentInfo, HealthResponse, UploadResponse } from "../types";

const BASE_URL = (import.meta.env.VITE_API_URL as string | undefined) ?? "http://127.0.0.1:8000/api";

async function parseError(res: Response): Promise<string> {
  try {
    const body = await res.json();
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) return body.detail.map((d: { msg: string }) => d.msg).join("; ");
  } catch {
    /* ignore */
  }
  return `Request failed (${res.status})`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${BASE_URL}${path}`, init);
  } catch {
    throw new Error("Cannot reach the backend. Is it running on http://127.0.0.1:8000 ?");
  }
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as T;
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  listDocuments: async (): Promise<DocumentInfo[]> =>
    (await request<{ documents: DocumentInfo[] }>("/documents")).documents,

  deleteDocument: (id: string) => request<{ deleted: boolean }>(`/documents/${id}`, { method: "DELETE" }),

  ask: (question: string, documentIds: string[]) =>
    request<AskResponse>("/chat/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, document_ids: documentIds }),
    }),

  /** Upload with progress (fetch cannot report upload progress, XHR can). */
  uploadDocument(
    file: File,
    onProgress: (percent: number, phase: "uploading" | "processing") => void,
  ): Promise<UploadResponse> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${BASE_URL}/documents/upload`);
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100), "uploading");
      };
      xhr.upload.onload = () => onProgress(100, "processing");
      xhr.onerror = () => reject(new Error("Cannot reach the backend. Is it running?"));
      xhr.onload = () => {
        let body: any = null;
        try {
          body = JSON.parse(xhr.responseText);
        } catch {
          /* ignore */
        }
        if (xhr.status >= 200 && xhr.status < 300) resolve(body as UploadResponse);
        else reject(new Error(typeof body?.detail === "string" ? body.detail : `Upload failed (${xhr.status})`));
      };
      const form = new FormData();
      form.append("file", file);
      xhr.send(form);
    });
  },
};
