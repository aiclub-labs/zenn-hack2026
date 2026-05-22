# Requirements 生成 AI への入力 manifest — dialogue-delta-formalization

> 用途: `/kiro:spec-requirements` または外部生成 AI に「ペルソナ + 業務フロー」を渡して requirements を生成 / 更新するための **入力束ねドキュメント**。
> 出典: 2026-05-20 meeting アクション #3 (@daichinakamura: フローとペルソナを生成 AI に渡して要件をまとめる準備)。
> 配置方針: 本ファイルは入力 manifest であり、本文は既存ファイルを参照する (内容重複を避け、参照先が更新されれば自動追随)。

---

## 0. 生成 AI への指示 (system prompt 想定)

あなたは Kiro spec-driven 開発の requirements 起こし担当。以下の入力束から、`EARS 形式` (Easy Approach to Requirements Syntax) に従った機能要件 / 非機能要件を日本語で生成せよ。

**順守事項**:

1. **想像で要件を作らない**: 入力に書かれていない動作は要件化しない。曖昧箇所は「TBD: 〜」として明示する
2. **persona 単位で章を切る**: Persona A / B / C ごとに、JTBD → 主要 Story → 派生要件、の順で起こす
3. **業務フロー** は §3.User Story Map (timeline × persona) と §5.デモナラティブを critical path として尊重する。MVP 必達は critical path 上のものに限定
4. **既存 requirements.md と矛盾しない**: 既に同意済みの構造 (MVP スコープ / Azure 構成 / 予算) は維持。差分提案がある場合は別途「変更提案」セクションで列挙
5. **リスク台帳との対応付け**: 要件が直接緩和するリスク (R-01 等) があれば「関連リスク: R-XX」を付記
6. **出力言語**: 日本語

**出力フォーマット**:

- `requirements.md` 同等構造 (Project Description / 機能要件 / 非機能要件 / 確認ポイント)
- EARS 形式: 「WHEN [条件], THE SYSTEM SHALL [動作]」形式
- 各要件に ID (`REQ-1.1` 等) を付与

---

## 1. 暗黙知の定義 (用語統一)

> 出典: 2026-05-20 meeting 決定事項

「自分の中で言語化できていないもの」「形式化されていない状態」を暗黙知と定義する。

- 言語化されていない判断パターン / 経験則 / 文脈依存の意思決定
- 「言語化はできるが普段していない」も含む (制約があって出ていないもの)
- 「世界中の誰も言語化していない」レベルではなく、**個人レベルで未形式化** の状態を主対象とする

---

## 2. Persona 入力

**参照ファイル**: [`personas-stories.md`](./personas-stories.md)

| Persona | 役割 | 主要セクション |
|---|---|---|
| **A: 知識管理者** (シゲル) | 暗黙知を形式化したい人 | §1 Persona A / §2.A Story (A1-A3) |
| **B: 業務ユーザー** (ハルカ) | 暗黙知を借りる / 活用する人 (能動的協力者側面あり) | §1 Persona B / §2.B Story (B1-B5) |
| **C: レビュアー** (タケシ) | 矛盾検知 / 品質ゲート担当 (C4 が矛盾検知主担当) | §1 Persona C / §2.C Story (C1-C5) |

**読み込み優先順**:

1. §0 ドキュメント位置付け
2. §1 Persona Cards (3 種)
3. §1.5 価値仮説 (現状 → 体験 → 結果)
4. §2 主要 User Stories (Given/When/Then 形式)

**C1-C3 / C4 の扱い** (2026-05-20 meeting 決定):

- **C1, C2, C3**: レビュー action のバリエーション (承認 / 編集 / 拒否)。1 record に対しいずれかを選択するフロー
- **C4**: 矛盾検知時の人間判断。`conflict_detected` フラグが立った場合の独立ロール
- C5 (SLA expired) は運用イベント、persona の能動アクションではない

---

## 3. 業務フロー / User Story Map 入力

**参照ファイル**: [`personas-stories.md`](./personas-stories.md) §3 User Story Map / §5 デモナラティブ

**critical path** (MVP 必達):

```
A1 (schema 初期定義)
  → B1 (通常対話)
    → B2 (5W1H ヒアリング介入)
      → C1 (レビュー承認)
        → B3 (次対話で過去 record 参照)
```

**業務フロー絞り込み方針** (2026-05-20 meeting 決定):

- 現段階では **汎用アプリケーション** として設計
- 業務フロー (人材マッチング / 資料検索 等) への絞り込みは **仕様 (requirements) 段階で再検討** する
- 入力時点では絞らないが、生成 AI は「汎用設計だがデモは戦略コンサル × 製造業マスを critical path に置く」前提で要件を書く

---

## 4. 既存制約 (生成 AI が踏まえるべき技術 / スコープ前提)

**参照ファイル**: [`requirements.md`](./requirements.md) §Project Description

要点:

- **Microsoft Agent Framework 1.0** ベース (2026-04-03 GA)
- **MVP スコープ**: Delta Detector + Hearout Agent (5W1H) + Formalization HITL + 次回対話での参照
- **Azure 構成**: Foundry Agent Service + MAF 1.0 + BYO Cosmos DB ハイブリッド
- **対象ドメイン**: 8 セクター × 10 ユニットマトリクス。POC は 1-2 マス。多マス展開に対応する設計
- **予算**: 6 週 $143 / $200
- **チーム制約**: 全ドキュメント日本語、3-phase 承認ワークフロー

---

## 5. リスク台帳との対応付け

**参照ファイル**: [`../../docs/risks.md`](../../docs/risks.md)

要件がカバーすべきリスク (要件内で「関連リスク: R-XX」と紐付ける):

- **R-01** (供給側インセンティブ) ← Persona A / B の協力動機を高める要件
- **R-02** (確からしさ / 重み付け) ← 形式化 / Truth Judgment / corpus 重み要件
- **R-03** (矛盾検知 2 パターン) ← Persona B B5 (活用時通知) / Persona C C4 (入力時審査) を分離した要件
- **R-04** (高精度モデル可否) ← モデル切替性 / fallback 要件
- **R-05** (ローカルモデル精度) ← ベンチ / routing 要件
- **R-06** (需要側インセンティブ) ← 介入 UX / skip 自由度要件
- **R-07** (業務フロー絞り込み) ← requirements 完成時の絞り込みゲート

---

## 6. 出力に含めない / 触らない範囲

- 確からしさ検証の具体手法 (お水指し / OMUSUBI 等) は **別フェーズ**。requirements では「複数ソース重み付き集約」程度に留める
- 暗黙知収集 → 検索の一貫フローの中で、検索 SPA は **nice-to-have**
- push 朝刊配信は削除済 (MVP スコープ外)

---

## 7. 利用手順

### A) `/kiro:spec-requirements` で生成 (推奨)

```
/kiro:spec-requirements dialogue-delta-formalization
```

(本 manifest は spec dir 直下にあるため、コマンドが自動参照)

### B) 外部生成 AI に直接渡す場合

1. 本ファイル (`requirements-input.md`)
2. `personas-stories.md` 全文
3. 既存 `requirements.md` (差分判定用)
4. `../../docs/risks.md`

を順に context に投入し、§0 の system prompt 指示で出力させる。

---

**End of requirements-input.md**
