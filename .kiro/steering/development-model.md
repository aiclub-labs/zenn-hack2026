# Development Model — AI-Driven Implementation Premise

## Why this steering exists

本プロジェクトの実装は **Claude Code / Codex / Copilot による AI-driven 開発を前提**とする。手動コーディング前提の工数見積もり（「200h 純実装」「+60h で追加 spec 不可」等）は本プロジェクトに**不適用**。

ボトルネックは**人間レビュー帯域 / 設計明瞭度 / async 決定速度 / Azure quota** であり、typing 時間ではない。

## Execution Model

### 実装インターフェース

1. **Claude Code / Codex セッション** — spec 単位で AI が実装。1 spec の wall-clock ≈ 数日〜1週間
2. **Discord bot コマンド経由実行** — `/deploy`, `/az status`, `/gh status` 等で Azure / GitHub 操作を async 化（`scaffold/discord-bot/` で実装中、Phase B/C 完了）
3. **GitHub Actions + claude.yml** — PR レビュー / CI / 自動修正
4. **HITL surfaces** — Discord reaction 承認（B3 で実装済）/ MAF `RequestInfoEvent`（spec 内）

### 人間が担う作業（これ「だけ」が時間制約）

| 作業 | 内容 | 想定時間 |
|------|------|---------|
| **構想 / 仕様化** | problem-statement, As-Is/To-Be/Gap, EARS requirements, design 検討 | 高（プロジェクト品質を決める） |
| **レビュー** | PR review, design review, spec phase approval, HITL 承認 | 中（per PR / phase で数十分） |
| **async 決定** | `decisions.md` の D{n} ゲートを期限内に閉じる | 低（投票 / 短いコメント） |
| **デモ収録** | 3 分動画の演出 / ナラティブ調整 | 中（最終週） |

### AI が担う作業（時間制約から外れる）

- 実装コード（TS / Python / .NET / Bicep）
- テスト記述（unit / integration / E2E）
- ドキュメント更新（spec, design, ADR, README）
- リファクタ / 型整備 / lint 対応
- バグ修正 / build error 解消
- 議事録要約 / Discord 通知文案

## Effort Estimation Framework

工数見積もりは **二軸**で書く:

| 軸 | 単位 | 何を測る |
|----|------|---------|
| **Wall-clock** | days / weeks | AI session の iteration を含む実暦時間 |
| **Human review** | hours | 人間が能動的に費やす時間（review + 承認 + 構想） |

旧来の「純実装 hours」表記は**廃止**。残っているドキュメント（`../../docs/architecture-cards/idea-f-*.md` §10, `decisions.md` D1/D2/D5 等）は次回更新時に二軸表記に書き換える。

### 換算ヒント（rough）

- 旧 30-40h "純実装" → 概ね wall-clock 2-3 day + human review 2-4h（AI が回しやすい部位）
- 旧 60-80h "純実装" → 概ね wall-clock 1 week + human review 4-8h
- 旧 200h "純実装" → 概ね wall-clock 5-6 week + human review 30-50h（プロジェクト全体）

ただし**スコープ削減判断の主軸は「Azure $200 予算」と「wall-clock 6 週」**であり、上記人時はあくまで参考。

## What this changes vs prior assumptions

| 旧前提 | 新前提 |
|--------|--------|
| 検索 SPA +30-40h は重い → nice-to-have（D1） | AI なら 2-3 day + 数h review → **MVP 昇格判定の閾値を下げる** |
| 2nd spec +60-80h は不可（D2） | AI なら +1 week wall-clock → **業務改革ナラティブが弱いなら追加可** |
| 純粋 TDD は 6週/200h で負荷高（D5） | AI にとって TDD コストはほぼ同じ → **採用しやすい** |
| Tier A-F 削減ラダーは人時前提 | 削減判断は Azure コスト + wall-clock 主軸に再評価 |

## Binding Constraints (不変)

AI-driven 化しても以下は不変:

1. **Azure 予算 $200 / 6 週** — token / SKU / Search query 課金は AI driven でも同等
2. **Wall-clock 6 週** — Azure 提供期限 + デモ日 (`./product.md` §Non-Negotiable #3)
3. **人間レビュー必須フェーズ** — Requirements / Design / Tasks 承認 + HITL 承認は AI 委譲不可
4. **構想 / ナラティブ品質** — 業務改革ストーリーは人間の仕事（議事録 L14: 「アイデアの革新性」を重視）
5. **想像ベース仕様化禁止** — AI に研究させても出典は `../../docs/research/` に必ず置く

## How to apply

- **新規見積もり**: 二軸（wall-clock + human review）で書く
- **decisions.md ゲート判断**: 「実装 hours」を根拠にしない、ナラティブ強度 / Azure コスト / wall-clock で判断
- **scope 追加判断**: 人時ボトルネック理由での却下は無効、wall-clock / 構想時間 / Azure コストでのみ却下
- **タスク割当**: 担当者名は「review 主体」「構想主体」を指す（実装そのものは AI セッションが回す）

## References

- `scaffold/discord-bot/` — Discord 経由 async 実行基盤（実装中）
- `scaffold/.github/workflows/claude.yml` — PR レビュー / 自動応答
- `scaffold/.claude/agents/` — repo 固有 subagent 定義
- 5/11 ミーティング L14 — 「完全実装よりアイデアの革新性と一部実装の完成度を重視」

---
_本前提は spec / design / decisions の判断軸に直接効く。旧来の「人時」前提の判断は本ドキュメント基準で再評価する_
