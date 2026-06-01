# Problem Statement — Microsoft Agent Hackathon Japan 2026

> 2026-05-11 ミーティング決定を反映した正本。spec / design / 議論はこのドキュメントの As-Is → To-Be → Gap を起点に traceability を取る。
>
> 前バージョン（kickoff 前検討の蓄積、4 候補比較 等）は GitHub 履歴 (`git log -- problem-statement.md`) で辿る。

作成日: 2026-05-12 / ベース: [architecture-cards/idea-f-dialogue-monitoring.md](./architecture-cards/idea-f-dialogue-monitoring.md) §1 + [meetings/2026-05-11.md](./meetings/2026-05-11.md) + [.kiro/steering/product.md](../.kiro/steering/product.md)

---

## メインテーマ

**暗黙知の形式知化を主軸とした AI エージェントシステム**（議事録 L7）。

特定セクター × ユニットの業務対話を MAF + Foundry Agent Service で監視し、**対話差分発生時点で暗黙知を捕捉 → 5W1H ヒアリング → 重み付き形式化 → corpus 蓄積 → 次回対話で参照** の閉ループを 6 週で MVP まで持っていく。

## 採択スコープ

- **対象**: エンタープライズ（対象組織 (例: AI 推進部門)）の 8 セクター × 10 ユニットのうち暗黙知密度が高い **1-2 マス**（推奨: 戦略 × 製造業 / 人材アサイン、`decisions.md` D3 で確定）
- **アーキ**: 多マス展開対応で設計、実装は 1-2 マスに閉じる（`{sector}#{unit}` partition key 統一）
- **MVP 必達 5 機能**: スキーマ定義 / 対話監視 / 差分検知 / 5W1H ヒアリング / 形式化 HITL + 次回参照
- **デモ**: 3 分（「対話差分 → ヒアリング → 形式化 → 次回参照」の場面転換）

## As-Is（議事録 L36-46 + idea-f §1）

| 段階 | 何が起きているか | 痛み |
|------|----------------|------|
| 業務対話 | PM / 営業が AI に判断を聞く → AI は汎用知識で回答 | クライアント固有の暗黙知が反映されない |
| 判断分岐 | 人間と AI の判断が食い違う → 人間がオーバーライドして終わり | 「なぜ違ったか」が記録されず属人化 |
| 次回対話 | 同じパターンで AI が同じ汎用回答 | 暗黙知が組織知化されない |

**共通根因**: AI × 人間の判断差分そのものが暗黙知の在りかなのに、捕まえる仕組みがない。

## To-Be（議事録 L48-54 システムフロー）

| 段階 | 何が起きるか | 解決される痛み |
|------|------------|--------------|
| 業務対話 | 事前定義スキーマに沿って agent が監視 | 対象暗黙知の種類が明示される |
| 判断分岐 | 入出力差分を検知 → 5W1H modal でヒアリング | 「なぜ / どう判断したか」が形式知化される |
| HITL 承認 | 重み付け（自己批評 / 信頼度 / 公開情報照合）後にレビュアー承認 → corpus 投入 | 人間入力を 100% 信頼せず品質ゲートを通す |
| 次回対話 | 蓄積 corpus を AI 応答に注入、引用 ID 明示 | クライアント固有判断ロジックが組織知化 |

## Gap — 埋めるべき 3 点

| ID | ギャップ | 対応する MVP 機能 |
|----|--------|------------------|
| **α 発生時点で捕捉** | 文書化を待たず、対話差分の発生時点で形式化を起動する | 対話監視 + 差分検知 + 5W1H modal |
| **β 事前定義スキーマで暴走防止** | 「欲しいデータ項目」を admin がガードレールとして与える（議事録: 対話の前に必要データを決める） | スキーマ定義 + スキーマ整合チェック |
| **γ 重み付き正誤判定** | 人間入力を 100% 信頼せず、自己批評 / 信頼度 / 公開情報照合で重み付ける | 形式化 HITL + 重み付け + 正誤判定（GraphCheck 型, 冷起動は FactCheck 型） |

## Non-Goals（明示的に外す）

- **多マス全展開**: アーキ対応のみ、実装は 1-2 マス
- **朝刊 push**: 削除済（idea-f §2、アウトプット過多 & デモ尺消費）
- **マルチテナント**: ハッカソン POC は単一テナント
- **Longitudinal 進化追跡**: 6 週枠で扱わない
- **検索 SPA (pull)**: nice-to-have 維持（`decisions.md` D1 で MVP 昇格可否を 5/26 までに判断）

## Value Proposition

Glean 等のエンタープライズ製品は explicit knowledge の検索 / 集約が主軸で、**対話差分からの暗黙知抽出層**は埋められていない（公開資料ベース）。本 POC の差別化は「**対話差分検知 + 5W1H ヒアリングによる externalization の自動化**」自体。理論的根拠は SECI モデル (PKAI BISE 2025) externalization フェーズ + Kunumi (arXiv 2507.03811) self-critique + 5-step protocol。

## 関連ドキュメント

- **アーキ判断カード（採択）**: [architecture-cards/idea-f-dialogue-monitoring.md](./architecture-cards/idea-f-dialogue-monitoring.md)
- **steering（プロジェクト memory）**: [.kiro/steering/product.md](../.kiro/steering/product.md) / [tech.md](../.kiro/steering/tech.md) / [structure.md](../.kiro/steering/structure.md) / [decisions.md](../.kiro/steering/decisions.md)
- **メイン spec**: [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/)
- **5/11 議事録**: [meetings/2026-05-11.md](./meetings/2026-05-11.md)
- **主リサーチ**: [research/tacit-knowledge-ai-prior-art.md](./research/tacit-knowledge-ai-prior-art.md) / [azure-agent-platform-decision.md](./research/azure-agent-platform-decision.md) / [sector-unit-candidates.md](./research/sector-unit-candidates.md) / [sdd-approach-evaluation.md](./research/sdd-approach-evaluation.md)
- **前バージョン（歴史参照）**: `git log -- problem-statement.md`

---
_本文書は安定文書。5/11 以降の決定で As-Is/To-Be/Gap が変わる場合のみ更新し、流動的な未確定論点は `../.kiro/steering/decisions.md` で扱う_
