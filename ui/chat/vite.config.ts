import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/turn": "http://localhost:8000",
      "/retrieve": "http://localhost:8000",
      "/citations": "http://localhost:8000",
      "/hearout": "http://localhost:8000",
      "/schemas": "http://localhost:8000",
      "/healthz": "http://localhost:8000",
    },
  },
});
