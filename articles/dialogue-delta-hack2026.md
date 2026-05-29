---
title: "Dialogue Delta — 暗黙知を citation 必須で形式知化する Azure × SK エージェント"
emoji: "💬"
type: "tech"
topics: ["azure", "openai", "semantickernel", "fastapi", "msahack2026"]
published: false
---

> [!NOTE]
> **執筆 in progress (5/31 night 完成目標)**。本記事は Microsoft Agent Hackathon Japan 2026 への応募エントリです。
> 構成は `docs/zenn-article-outline.md` 準拠。各章は (TODO) マーカー位置に本文を流し込みます。

## 0. TL;DR

自社 corpus を LLM の grounding 必須にしつつ、応答時に立ち上がる暗黙知を **Hearout → 形式知化 → corpus に還す** ループ。

(TODO: アーキ図 1 枚 — Chat → Critic → Gap → Hearout → Formalize → Review → Corpus)

## 1. 解こうとした問題

(TODO)

## 2. アプローチの 3 軸

(TODO)

## 3. 設計の trade-off

(TODO)

## 4. 実装ハイライト

(TODO)

## 5. 観測した挙動と驚き

(TODO)

## 6. コスト

PoC 実測 ¥1,491 (3日) → 推定 ¥14,000 (全期間)。Enterprise 100 user 投影 ¥175,000/月 = **¥1,750/user/月**。

(TODO: 競合比較 + 未実装の cost 制御)

## 7. デモ & リンク

- 動画: (TODO)
- 動く App: <https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/>
- GitHub: <https://github.com/aiclub-labs/zenn-hack2026>
- Team: aiclub-labs (Microsoft Agent Hackathon Japan 2026)

## 8. 学び・残課題

(TODO)
