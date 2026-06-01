# Chat UI (Persona B — ハルカ)

Vite + React 18 + TS strict. Talks to FastAPI on `http://localhost:8000`.

## Dev

```bash
pnpm install   # or npm install
pnpm dev       # http://localhost:5173
```

Backend must be running: `uvicorn app.main:app --reload --port 8000`.

## Components

- `ChatWindow` — message stream + citation chips
- `SchemaUpdateBanner` — Req 2.7 banner; gates next-turn hearout until acked
- `HearoutModal` — Req 5 non-blocking 5W1H modal (cold start <= 3s lazy)
- `CitationCard` — weight bar + superseded banner
- `ConflictInline` — Req 8 B5 "他に N 件の異なる見解あり"
- `SchemaHistorySidebar` — Req 2.6 read-only recent schema changes
- `RedactToggle` — Req 7 redact indicator
