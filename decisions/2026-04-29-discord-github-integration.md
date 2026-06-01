# ADR-0001: Discord + GitHub + Claude Code を spec-driven 開発の幹に据える

- **Date**: 2026-04-29
- **Status**: Accepted
- **Driver**: operator (`operator`); team (`member-a`, `member-b`)
- **Discord thread**: TBD (この ADR を merge した後に `#hack-dev-log` でアナウンス予定)

## Context

ハッカソン 3 名チーム (`aiclub-labs/zenn-hack2026`、提出 2026-06-01) は、議論 → 設計 → レビュー → merge の動線が手動運用で、摩擦が大きい。

[`discord-bot/docs/dev-workflow-research.md`](../../../discord-bot/docs/dev-workflow-research.md) の調査結論:
- 業界標準は **GitHub = system of record / Discord = pre-flight room**（Bevy / Rust / Astro / Bun / Cloudflare Workers）
- Discord で意見集約、GitHub で意思決定。順序を逆にした成功例なし
- 「Claude-Code-in-Discord ループ」は現エコシステムの空白で差別化候補

## Decision

以下 4 層構成で連携を組む:

1. **Discord (議論層)** — 既存サーバーの `🏆 Hackathon: MS Agent 2026` カテゴリに `#hack-dev-log` (forum) / `#hack-chat` / `#github-feed` (webhook) を持つ
2. **GitHub (意思決定層)** — `aiclub-labs/zenn-hack2026` で spec-driven (`.kiro/specs/`) + ADR (`decisions/`) + CODEOWNERS + 2 SME approval (advisory)
3. **Bridge (3 つだけ)**:
   - GitHub → Discord webhook (PR opened / review-requested / merged の **3 イベントのみ**)
   - Claude Code GitHub App (`@claude-review` for PR レビュー)
   - Discord → Claude Code ブリッジ (既存 `ai-club/discord-bot/` を拡張、`/spec` `/review` slash commands)
4. **Workflow ループ** — Discord 議論 → `/spec` ドラフト生成 → GitHub PR → `@claude-review` + 2 approval → merged 通知 → 週次 digest commit

## Consequences

### Positive
- **手動運用が消える**: PR 状態がリアルタイムで Discord に届く、レビューも AI が下書き
- **意思決定が永続化**: Discord pin に頼らず ADR + GitHub PR で検索可能
- **ハッカソン差別化**: `/spec` `/review` の Discord 駆動 Claude Code ループは未充足領域、デモ映え

### Negative
- **3 つの bridge bot を維持する負荷**（最小化のため bot 数を 3 に制限）
- **Claude 利用枠の消費**:
  - **Claude Code GitHub Action**: operator の **Claude Max ($200/月) サブスクリプション** に OAuth で紐付ける運用とする (`CLAUDE_CODE_OAUTH_TOKEN`)。1 コール = pay-per-use の Anthropic API 課金は発生せず、operator の Max quota を消費する。3 名 × ハッカソン期間（6 週）× Markdown 中心レビューの規模では Max plan で十分まかなえる見込み。`@claude-review` の濫用は quota 圧迫リスクとなるため、重要な PR でのみ呼ぶ運用に留める。
  - **Discord bot 側**: Anthropic API key 経由で別途課金が発生（Max サブスクとは独立）。
- **discord-bot の拡張コスト** — Phase 3 で `/spec` `/review` を実装、~3 日

### Neutral
- 既存 `ai-club/discord-bot/` のアーキテクチャ (per-channel history, tool interface) を per-thread に拡張するだけで済む

## Alternatives considered

- **Discord で完結 (Discord 絵文字 vote = merge)** — Rejected: CODEOWNERS と監査ログをバイパスする。Bevy も SME 投票は GitHub PR 上に記録している。
- **`ebibibi/claude-code-discord-bridge` をそのまま採用** — Rejected: 既存 `discord-bot/` の資産（admin tools 9 個、per-channel history、tool interface）を活かすほうが効率的。fork ではなく拡張。
- **GitHub Discussions で代替** — Rejected: 同期煮詰めには Discord forum のほうが速い。GitHub Discussions は批准済み議論のアーカイブ用。

## Verification

- [ ] Phase 1 完了時: テスト PR で `#github-feed` に通知 1 件のみ届く（3 イベント以外は届かない）
- [ ] Phase 2 完了時: テスト PR で `@claude-review` がレビューコメント返却
- [ ] Phase 3 完了時: Discord で `/spec test` → GitHub PR が自動作成される
- [ ] Phase 4 完了時: 金曜 cron で `decisions/YYYY-Www.md` digest PR が自動生成

## References

- [Plan: Discord + GitHub + Claude Code Collaborative Dev Setup](../../microsoft-agent-hackathon-2026/HANDOFF.md#d-discord-already-designed-execution-open) — Phase 別ロールアウト
- [`discord-bot/docs/dev-workflow-research.md`](../../../discord-bot/docs/dev-workflow-research.md) — 業界先行事例調査
- [`discord-bot/docs/dev-discord-patterns-research.md`](../../../discord-bot/docs/dev-discord-patterns-research.md) — Discord forum 運用パターン
- [`discord-bot/docs/server-structure-plan.md`](../../../discord-bot/docs/server-structure-plan.md) — チャンネル構成 v3
