import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server runs on localhost:5173; the API lives on localhost:8000 (CORS is enabled there).
export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173, strictPort: true },
});
