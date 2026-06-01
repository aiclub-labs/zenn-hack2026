# Review UI (Persona C — タケシ)

Vite + React 18 + TS strict. Port 5174. Backend on `http://localhost:8000`.

## Pages

- `/` — Normal Queue (Req 9): pending_review tickets, weight tooltip, TJ badge, lock indicator, age
- `/conflict` — Conflict Queue (Req 10): parallel comparison, 3 decisions
- `/self-approval` — Dashboard (Req 9.9): 7-day rolling % + warning > 30%

## Components

- `WeightBreakdown` — A×B×C tooltip
- `LockBadge` — 5-min countdown
- `PriorityModeBanner` — Req 9.11 priority-3 mode toggle (median > 3min)

## Dev

```bash
pnpm install
pnpm dev   # http://localhost:5174
```
