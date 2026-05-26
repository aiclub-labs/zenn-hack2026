# UI 機能性 / 洗練性 監査メモ

> 2026-05-27 / Author: Mao+Claude
>
> Admin URL 洗練後の追跡監査。Chat / Review / 共通部品で残る生 HTML と機能不足を列挙し、デモ録画前に潰す。

## 1. Fluent 化状況スナップショット

| 区分 | ファイル | 状態 |
|---|---|---|
| Shell | `shell/AppShell.tsx` | ✅ Fluent 済 (sidebar + header) |
| Admin | `admin/pages/SchemaList.tsx` | ✅ Fluent 済 (KPI + Table + Dialog) |
| Admin | `admin/pages/SchemaHistory.tsx` | ✅ Fluent 済 |
| Admin | `admin/pages/SchemaImport.tsx` | ✅ Fluent 済 |
| Admin | `admin/pages/SelfApprovalDashboard.tsx` | ✅ Fluent 済 (5 KPI cards) |
| Chat | `pages/Chat.tsx` | ✅ Fluent (枠のみ) |
| Chat | `components/ChatWindow.tsx` | ⚠ 生 inline style — bubbles 配色・self-critic 表示が雑 |
| Chat | `components/HearoutModal.tsx` | ❌ 完全に生 HTML (button/textarea/div) — デモ最大山場 |
| Chat | `components/SchemaUpdateBanner.tsx` | ❌ 生のオレンジ箱、Fluent MessageBar 使ってない |
| Chat | `components/CitationCard.tsx` | ⚠ 生 border + 自作 weight bar |
| Chat | `components/ConflictInline.tsx` | ⚠ 生 box (件数のみ) |
| Chat | `components/RedactToggle.tsx` | ⚠ checkbox + label のみ、Fluent Switch にすべき |
| Chat | `components/SchemaHistorySidebar.tsx` | ⚠ 生 aside |
| Review | `review/pages/NormalQueue.tsx` | ❌ 生 table + 自作 aside drawer |
| Review | `review/pages/ConflictQueue.tsx` | ❌ 生 table |
| Review | `review/components/WeightBreakdown.tsx` | ⚠ 生 |
| Review | `review/components/LockBadge.tsx` | ⚠ 生 |
| Review | `review/components/PriorityModeBanner.tsx` | ⚠ 生 |
| Dead? | `review/pages/SelfApprovalDashboard.tsx` | ❓ Admin タブ側と重複、要削除確認 |

## 2. 機能不足 (洗練性 ≠ Fluent 化、UX 層)

### Chat
- **F1**: メッセージ送信後 auto-scroll なし → 長い対話で発言が画面外
- **F2**: 送信失敗時の表示無し (catch しても画面に出ない) → デモ中に黙って固まる
- **F3**: タイムスタンプ / コピー / 再送ボタン無し
- **F4**: redact ON 時の視覚マーカー無し (toggle のみ)
- **F5**: 「履歴を見る」リンクが新タブで開く → SPA 内 Admin タブにルーティングすべき

### Hearout
- **F6**: 進捗 N/5 がテキストのみ → Fluent ProgressBar で視覚化
- **F7**: 過去 turn の質問/回答が見えない → 「以前何答えたか」を確認不可
- **F8**: スキップ時の確認ダイアログ無し → 誤クリックで離脱
- **F9**: AI 提案 (次の質問) を「読みやすく」するためのカード化なし

### Review (Normal Queue)
- **F10**: ID 8 文字切り捨てだけで full ID 確認手段なし
- **F11**: 並び替え (weight / age / lock 順) なし
- **F12**: 検索/フィルタ (sector#unit / priority / pk) なし
- **F13**: 承認/編集/却下時の reason 任意入力フィールド無し
- **F14**: aside drawer が手作りで閉じる×しか無い (Fluent Drawer/InlineDrawer 使うべき)
- **F15**: 関連 turn が `(hearoutから辿る — WT-D連携TODO)` のままハードコード

### Conflict
- **F16**: ConflictInline は件数のみ表示 → 中身に飛べない (Citation との接続が無い)
- **F17**: ConflictQueue で adopt_new / keep_existing / coexist 3 決定の意味解説 tooltip 無し

### 共通
- **F18**: 全画面通して toast / error notification 無し → 失敗が user に届かない
- **F19**: ブラウザリロードで state ロスト (sessionId, messages, tenant) → セッション復元なし
- **F20**: 多くの一覧画面で row hover ハイライト無し
- **F21**: `index.html` の OG / favicon 未設定

## 3. 優先度マトリクス (デモ録画前)

| 優先 | 項目 | 工数 |
|---|---|---|
| **P0** | ChatWindow Fluent 化 (bubbles, scroll, self-critic chip) | 30min |
| **P0** | HearoutModal Fluent Dialog 化 + ProgressBar + 履歴表示 | 60min |
| **P0** | SchemaUpdateBanner Fluent MessageBar 化 + 内部 routing | 20min |
| **P0** | CitationCard Fluent Card + ProgressBar 化 | 30min |
| **P0** | NormalQueue Fluent Table + Drawer 化 + filter/sort | 60min |
| **P1** | F1 auto-scroll / F2 送信失敗 toast | 20min |
| **P1** | ConflictInline → Citation 接続 | 30min |
| **P1** | Review 部品 (Weight/Lock/Priority) Fluent 化 | 30min |
| **P1** | RedactToggle → Switch | 5min |
| **P2** | F7 Hearout turn history / F13 reason 任意入力 | 30min |
| **P2** | F19 セッション復元 (localStorage) | 30min |
| **P2** | F21 favicon / OG | 5min |
| **P2** | dead `review/pages/SelfApprovalDashboard.tsx` 削除確認 | 5min |

> 提出 24h 前で P0 全消化、P1 半分、P2 録画後送りを推奨。

## 4. ドメイン確定後に再考が必要な箇所

`scope-candidates.md` 完了後、以下のテキスト/プレースホルダがドメイン依存で書き直し必要:

- `Chat.tsx` placeholder「質問・確認したい内容を書いてください…」
- `Chat.tsx` Hearout 初期質問「この事象について 5W1H で教えてください。まず who…」
- `SchemaList.tsx` subtitle「ライン暗黙知の定義域。1 つの欠落がそのまま Δ 検出の死角になる。」
- Tenant プリセット (`manufacturing-s8b#line-A` 等)

→ 配色・配置・コンポーネント選定は domain agnostic なので polish は先行可能。
