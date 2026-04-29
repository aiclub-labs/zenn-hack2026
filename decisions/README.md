# Decisions / ADR Log

> **目的**: Discord で煮詰めた合意を「検索可能・永続的」な形で残す。Discord pin / bookmark を意思決定アーカイブにすると後で読めなくなる ([調査根拠](../../../discord-bot/docs/dev-workflow-research.md#4-非同期スタンドアップ--意思決定ログ))。

## ルール

1. **Discord で議論 → ここに ADR を PR で追加** — 順序は固定。逆向きにしない。
2. **ファイル名**: `YYYY-MM-DD-{kebab-case-slug}.md` （例: `2026-04-30-discord-github-integration.md`）
3. **テンプレ**: [`0000-template.md`](./0000-template.md) をコピーして書き始める
4. **PR レビュー**: CODEOWNERS により `maumao76` + `Suzuki-Sotaro` + `daichinakamura34` のうち 2 名以上の approval を推奨（advisory）
5. **Discord リンク**: ADR 内に必ず議論元の forum thread URL を貼る。逆向きにはしない（Discord → repo を指す）

## 既存 ADR

- [ADR-0001: Discord + GitHub + Claude Code を spec-driven 開発の幹に据える](./2026-04-29-discord-github-integration.md) — 2026-04-29 (Accepted)

