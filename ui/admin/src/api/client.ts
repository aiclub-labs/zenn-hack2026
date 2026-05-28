import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json",
    // OIDC integration lands tomorrow; stub headers for today.
    "X-User-Id": "shigeru.dev",
    "X-User-Role": "schema_admin",
  },
});
