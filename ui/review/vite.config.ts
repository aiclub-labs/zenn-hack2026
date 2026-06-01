import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5174,
    proxy: {
      "/reviews": "http://localhost:8000",
      "/healthz": "http://localhost:8000",
    },
  },
});
