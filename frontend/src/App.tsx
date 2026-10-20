import { useCallback, useEffect, useState } from "react";
import { api } from "./api/client";
import Sidebar from "./components/Sidebar";
import ChatPanel from "./components/ChatPanel";
import type { DocumentInfo, HealthResponse } from "./types";

type Theme = "light" | "dark";

function initialTheme(): Theme {
  const saved = localStorage.getItem("sovereignai-theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export default function App() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [theme, setTheme] = useState<Theme>(initialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("sovereignai-theme", theme);
  }, [theme]);

  const refreshDocuments = useCallback(async () => {
    try {
      const docs = await api.listDocuments();
      setDocuments(docs);
      setLoadError(null);
      // drop selections for documents that no longer exist or are not ready
      setSelected((prev) => prev.filter((id) => docs.some((d) => d.id === id && d.status === "ready")));
    } catch (e) {
      setLoadError((e as Error).message);
    }
  }, []);

  const refreshHealth = useCallback(async () => {
    try {
      setHealth(await api.health());
      setHealthError(null);
    } catch (e) {
      setHealth(null);
      setHealthError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
    refreshHealth();
    const timer = setInterval(refreshHealth, 15000);
    return () => clearInterval(timer);
  }, [refreshDocuments, refreshHealth]);

  const handleUploaded = (doc: DocumentInfo) => {
    refreshDocuments();
    if (doc.status === "ready") setSelected((prev) => (prev.includes(doc.id) ? prev : [...prev, doc.id]));
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteDocument(id);
    } catch (e) {
      setLoadError((e as Error).message);
    }
    refreshDocuments();
  };

  const toggle = (id: string) =>
    setSelected((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));

  return (
    <div className="app">
      <Sidebar
        documents={documents}
        selected={selected}
        onToggle={toggle}
        onDelete={handleDelete}
        onUploaded={handleUploaded}
        health={health}
        healthError={healthError}
        loadError={loadError}
        theme={theme}
        onToggleTheme={() => setTheme(theme === "dark" ? "light" : "dark")}
      />
      <ChatPanel documents={documents} selectedIds={selected} llmReady={health?.llm.ok ?? false} />
    </div>
  );
}
