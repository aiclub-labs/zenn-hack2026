# Dialogue Delta — Admin UI (WT-C)

React 18 + Vite + TS strict. Persona A (シゲル, 知識管理者) 向け管理画面。

## 開発手順

```bash
cd ui/admin
pnpm install        # or npm install
pnpm dev            # http://localhost:5174
```

`.env.local` で API base URL を上書き可:

```
VITE_API_BASE_URL=http://localhost:8000
```

## ページ

- `/schemas` — スキーマ一覧 + 編集 + is_active トグル + reject率カード (mock)
- `/history` — Req 2.6 read-only 監査履歴 (時刻 JST 表示)
- `/import` — Req 3 cross-tenant bulk import + dry-run プレビュー
- `/self-approval` — Req 9.9 自己承認 KPI スタブ (明日 reviews API 結線)

## 認証

今日は header stub (`X-User-Id`, `X-User-Role=schema_admin`)。
Entra ID OIDC 統合は明日 (WT-A 完了後)。

## 注意

- 全時刻 JST 表示 (`src/lib/jst.ts`)
- 型は `src/types.ts` で zod ガード、サーバレスポンスを必ず parse
- `GET /schemas` がコントラクトに無いため、現状は `/schemas/history` を再生して一覧化（report.md flagged）
