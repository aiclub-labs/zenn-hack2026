# Product Overview

Microsoft Agent Hackathon Japan 2026 提出物。エンタープライズ（対象組織 AI 部）の業務対話から **暗黙知を検知 → 5W1H ヒアリング → 形式化 → corpus 蓄積 → 次回対話で参照** の閉ループを Microsoft Agent Framework 1.0 + Foundry Agent Service で実装する POC。

対象は 8 セクター × 10 ユニットの組織マトリクスのうち、暗黙知密度が高い 1-2 マス（推奨: 戦略 × 製造業 / 人材アサイン）。アーキは多マス展開対応設計とする。

## Core Capabilities

- **業務対話差分検知** — admin が事前定義したスキーマと AI 出力 / 人間入力の差分をリアルタイム検知
- **5W1H ヒアリングループ** — 差分閾値超で 5W1H 質問を modal で起動、自由回答を構造化
- **重み付き形式化と HITL レビュー** — 自己批評 / アノテータ信頼度 / 公開情報照合の重み付き集約、レビュアー承認後 corpus 投入
- **正誤判定** — atomic claim 分解 + corpus 照合（GraphCheck 型）、冷起動期は 3 LLM 投票（FactCheck 型）
- **次回対話での corpus 参照** — 蓄積 record を AI 応答に注入、引用 ID 明示

## Target Use Cases

- 対象組織 AI 部のような特定セクター × ユニット業務での暗黙知形式知化
- 形式知化対象の典型: 「アサイン判断時の人間関係考慮」「顧客固有の意思決定癖」「過去案件の red-flag パターン」など
- ハッカソン審査向け 3 分デモ: 「対話差分 → ヒアリング → 形式化 → 次回参照」の場面転換

## Value Proposition

Glean 等のエンタープライズ製品は **explicit knowledge の検索 / 集約が主軸**で、対話差分からの暗黙知抽出層は明確に埋められていない（公開資料ベース）。本プロジェクトの差別化ポイントは「**対話差分検知 + 5W1H ヒアリングによる externalization の自動化**」自体。

理論的根拠として SECI モデル (PKAI BISE 2025) の **externalization** フェーズに特化、Kunumi (arXiv 2507.03811) の self-critique + 5-step protocol を採用基準として援用。

## Non-Negotiable Principles (Constitution)

5/11 ミーティング決定および `../../docs/research/sdd-approach-evaluation.md` §3 を踏まえた**非交渉原則**。spec / design / 実装はこれらを満たすこと。

1. **MVP 完走 > 完全実装** — 議事録「完全実装よりアイデアの革新性と一部実装の完成度を重視」を遵守。スコープ追加は MVP 必達 5 機能（スキーマ定義 / 対話監視 / 差分検知 / 5W1H ヒアリング / 形式化 HITL + 次回参照）の完成を脅かさない範囲のみ
2. **想像ベース仕様化の禁止** — 重み付け / 正誤判定 / ヒアリング設計は `../../docs/research/` の先行事例に出典を辿れる形でのみ仕様化する
3. **Wall-clock 6 週 / Azure 予算 $200 厳守** — 実装は AI-driven（`development-model.md` 参照）、判断軸は wall-clock + Azure コストであり「人時」ではない。Tier A-F 段階削減ラダー（idea-f §5b）は累積 $120 (M8) / $150 (warning) でスコープ縮退判断。人時ベースの旧見積もりは本前提下で再評価する
4. **多マス対応の設計だけ担保、実装は 1-2 マス** — 永続化リソースの partition key を `{sector}#{unit}` で統一、agent は `target_sectors` / `target_units` を環境変数で受ける
5. **日本語ドキュメント** — チームメンバーの一部が英語に不慣れ。spec / design / research / decisions / steering 全て日本語
6. **3-phase 承認ワークフロー** — Kiro 流 SDD: Requirements → Design → Tasks → Implementation。`-y` 高速化は信頼できるフェーズ限定

## Feature Scope (現状の Spec 構造)

- **MVP メインシステム** = `.kiro/specs/dialogue-delta-formalization/` 単独で議事録の MVP 全体を内包（サブシステムではない、メインシステム）
- **追加 spec 検討は decisions.md ゲート経由** — preemptive な spec 分割は禁止
- **nice-to-have / 削除済**:
  - 検索 SPA (pull): nice-to-have（ビジネスインパクト判断 = decisions.md D1）
  - 朝刊 push: 削除済

## References

- 5/11 ミーティング議事録: `../../docs/meetings/2026-05-11.md`
- 上流アーキカード: `../../docs/architecture-cards/idea-f-dialogue-monitoring.md`
- 主リサーチ: `../../docs/research/{tacit-knowledge-ai-prior-art, azure-agent-platform-decision, sector-unit-candidates, sdd-approach-evaluation}.md`

---
_Focus on patterns and purpose, not exhaustive feature lists_
