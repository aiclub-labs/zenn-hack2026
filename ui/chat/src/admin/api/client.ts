import axios from "axios";

// Unified UI: same-origin so nginx proxies to API. Keep stub user headers.
export const api = axios.create({
  baseURL: "",
  headers: {
    "Content-Type": "application/json",
    "X-User-Id": "shigeru.dev",
    "X-User-Role": "schema_admin",
  },
});
