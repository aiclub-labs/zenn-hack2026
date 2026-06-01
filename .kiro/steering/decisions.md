# Open Decisions & Early Judgment Gates

## Purpose

オープン論点と早期判断ゲートを **async で意思決定可能な形式** に集約する流動文書。安定文書（product / tech / structure）と役割分離し、週次更新前提で運用する。

`product.md` の非交渉原則と `tech.md` の技術決定が決まったあとに残る「未確定だが期限がある判断」を扱う。

## Update Cadence

- **更新タイミング**: 5/19 (Week 1 end-of-week), 5/26 (PAYG 移行前), 必要時随時
- **判断機構**: GitHub Issue / Discord スレッドでチームメンバー async コメント・投票
- **告知**: 判断確定時に Discord に通知 + 当該 D{n} 行を更新（履歴は git log で追跡）
- **不在前提**: maumau は 5 月中の sync セッションに参加不可。判断材料は async で揃える

## Decision Entry Format

各エントリは以下の構造で記述:

```
### D{n}: {タイトル}
- **論点**: 何を決める必要があるか
- **判断材料**: コスト / 工数 / リスク / 出典
- **判断期限**: YYYY-MM-DD
- **暫定結論**: 暫定的にどちらに倒すか（明示する。「未定」禁止）
- **判断主体**: maumau / チーム async / 自動（research 完了時 等）
- **クローズ条件**: この判断を「確定」にするために必要な条件
- **影響範囲**: どの spec / file / cost が動くか
```

---

## Active Decisions

### D6: As-Is 前提の調達方針 — Hypothesize vs Identify 🔴 **TOP PRIORITY**

> **優先度: 最上位** — Requirements (`/kiro:spec-requirements`) 着手の前提条件。本判断未確定下では Requirements の Goals / Stakeholders / Acceptance Criteria が成立しない。

> **視点の明示**: 本判断における「As-Is」は **対象 org の As-Is**（= 本プロジェクトのデプロイ対象である業務組織、対象組織 AI 部 を proxy 想定）。ハッカソン参加チーム = AI club としての視点ではない。3 Path はいずれも「**対象 org の業務実態をどう調達するか**」の選択肢。

- **論点**: idea-f Architecture Card §1 As-Is テーブルが「PM / 営業が業務対話の中で AI に判断を聞く」前提に依存しているが、**対象 org における実態**（**M365 Copilot 導入状況 / PM-AI 対話の日常性**）が未確認。As-Is を想像で書くか、実情ヒアリングで埋めるかを team で合意する必要がある
- **判断材料**:
  - **Path A — Hypothesize**: 一般的なエンタープライズコンサル業務対話シナリオを想定で As-Is に記述（対象 org をモデル化された generic org として扱う）
    - Pros: スコープを動かしやすい / デモシナリオを具体に組める
    - Cons: 実在性が薄く、reviewer から「対象 org での妥当性」を問われると弱い
  - **Path B — Identify**: 対象 org の実情（Copilot 利用状況 / PM-AI 対話の現状）をヒアリングで As-Is に記述（チームメンバーの所属 org 経由でアクセス）
    - Pros: リアリティ高 / デモ説得力強
    - Cons: ヒアリング + 守秘層の障壁 / 5/14 セッション前に間に合うか不明
  - **Path C — Hybrid**: Hypothesize として明示しつつ、5/14 セッションで対象 org 実例の echo を 1-2 マス分回収して反映
    - Pros: 両立 / 柔軟
    - Cons: As-Is に「想定」注記必要 / レビュー観点が +1
  - **M365 Copilot overlap 論点**: Copilot が既に「対象 org で PM が AI に聞く」レイヤーをカバーしているなら、本案 As-Is は **「Copilot は答えるが暗黙知を harvest しない」** に書き換える必要。§11 Differentiation hook にも反映が要る
- **判断期限**: 2026-05-14（entry session、メンバー集合時）
- **暫定結論**: **Path C（Hybrid）** — Hypothesize ベースで spec を進めつつ、5/14 セッションで対象 org 実例を 1-2 マス分回収して As-Is に反映、必要なら Path A or B に倒す
- **判断主体**: チーム async（5/14 entry session で確定）。**判断視点は「対象 org として」**（AI club としてではない）
- **クローズ条件**: 以下のいずれか
  1. 5/14 セッションで A / B / C のいずれかを team が「対象 org として」合意
  2. 対象 org の Copilot 導入状況 + PM-AI 対話実態が判明し、As-Is が実情ベースで書ける状態になる
- **影響範囲**:
  - `../../docs/architecture-cards/idea-f-dialogue-monitoring.md` §1 As-Is テーブル / §11 Differentiation hook
  - `../../.kiro/specs/dialogue-delta-formalization/requirements.md` Project Description (L4-L37) / Introduction (L121-L129)
  - `./product.md` Target Use Cases / Value Proposition
  - **`/kiro:spec-requirements` 実行可否** — Requirements 生成は本判断確定後に着手

---

### D1: 検索 SPA を MVP 昇格 vs nice-to-have 維持

- **論点**: 検索 SPA (pull retrieval UI) を MVP 必達に昇格するか、nice-to-have に留めるか
- **判断材料**:
  - **AI-driven 前提下の wall-clock**: 2-3 day + human review 2-4h（`development-model.md` 換算）→ 人時を理由に却下できない
  - 追加コスト: ~$15（AI Search query 追加分）→ Azure 予算インパクト軽微
  - デモ尺: +30s 程度
  - **判断軸はビジネスインパクトのみ**: 「次回対話で参照」だけで業務改革ナラティブが成立するか、pull 検索が「使ってる感」のために必要か
  - 5/11 議事録 L48-54 のシステムフロー（案）では「次回以降の提案に活用」のみで、検索 UI は明示されていない
- **判断期限**: 2026-05-26（PAYG 移行前）
- **暫定結論**: nice-to-have 維持（**ただし AI-driven 前提下では昇格閾値が下がる。デモストーリーボード review で「弱い」judgment が出たら即昇格**）
- **判断主体**: チーム async（Discord 投票）
- **クローズ条件**: チームから「business impact が次回参照だけで足りる」 or 「pull 検索なしだとデモが弱い」のどちらかで合意
- **影響範囲**: `requirements.md` Req 8 周辺 / `design.md` Retrieval flow / 予算 +$15

### D2: 業務改革ナラティブ強度 / 2nd spec 検討

- **論点**: dialogue-delta-formalization 単独で 3 分デモの業務改革ナラティブが成立するか。不足なら 2 つ目 spec（例: admin schema 管理 / 横断ダッシュボード）を切るか
- **判断材料**:
  - 5/11 議事録 L14「完全実装よりアイデアの革新性と一部実装の完成度を重視」→ preemptive な spec 分割は議事録逸脱リスク
  - 議事録 L48-54 のシステムフローは dialogue-delta-formalization に完全に内包される
  - デモ尺 3 分内に「組織展開示唆」「具体ドメイン課題解決」が映るかが判断軸
  - **AI-driven 前提下**: 2nd spec 追加は wall-clock +1 week + human review 4-8h（`development-model.md` 換算）+ Azure $20-30。人時を理由に却下できない、判断軸はナラティブ強度と wall-clock 残量
- **判断期限**: 2026-05-26
- **暫定結論**: 単独で成立、追加 spec 不要（**AI-driven 前提下でも wall-clock 6 週内に収まるかが追加の制約。ナラティブが弱いと判断されたら追加可**）
- **判断主体**: チーム async（デモストーリーボード review 経由）
- **クローズ条件**: 3 分ストーリーボード初稿レビュー時に「弱い」judgment が出たら再検討
- **影響範囲**: `.kiro/specs/` 配下の構成 / 工数 / 予算

### D3: POC 対象セクター × ユニット 確定

- **論点**: 8 セクター × 10 ユニットのうち POC で扱う 1-2 マスを確定
- **判断材料**:
  - 候補 5 件: `../../docs/research/sector-unit-candidates.md`
  - 推奨: A（戦略 × 製造業 / 人材アサイン）— 議事録例示済 + デモ強度 + 合成 corpus 作成負荷の 3 軸で最有力
  - 代替: D（サステナビリティ × 製造業 / ESG 監査）は同セクター 2 マス展開時の corpus 流用余地
- **判断期限**: 2026-05-19（Week 1 end-of-week）
- **暫定結論**: A 仮置き、D を「2 マス展開で多マス対応を示唆」する場合の併用候補
- **判断主体**: チーム async（5/14 セッション参加メンバーから maumau 不在分のフィードバックを集約）
- **クローズ条件**: 合成 corpus 50-80 件作成主体（Daichi 想定）の合意 + ドメイン妥当性チェック
- **影響範囲**: `requirements.md` Project Description / 合成 corpus 作成タスク / デモストーリー

### D4: Foundry preview vs Container Apps 直接デプロイ 最終確定

- **論点**: Foundry Agent Service Workflow agent (preview) を MVP に組込むか、MAF を Container Apps に直接デプロイするか
- **判断材料**:
  - リサーチ結論: Foundry + MAF + BYO Cosmos ハイブリッドが第一候補（`../../docs/research/azure-agent-platform-decision.md`）
  - 未確認: Foundry Hosted agent の swedencentral リージョン提供状況 / Free Trial enable 可否
  - リスク: preview の breaking change / リージョン不一致
  - バックアップ実行容易性: MAF コードは Container Apps へコード変更なし移植可能（converged runtime）
- **判断期限**: 2026-05-18（Week 1 flag day）
- **暫定結論**: Foundry 採用候補、Week 1 実機検証後最終判断
- **判断主体**: maumau（実機検証主体）
- **クローズ条件**:
  1. swedencentral で Foundry Hosted agent 利用可能であることを実機で確認、OR
  2. 不可なら MAF on Container Apps へ即フォールバック決定
- **影響範囲**: `design.md` Technology Stack 行 / `infra/` Bicep / 認証スコープ設計

### D5: 開発アプローチ — TDD vs 通常開発

- **論点**: 5/11 議事録 L74 のオープン論点。実装フェーズで TDD を強制するか
- **判断材料**:
  - Kiro 流 SDD 自体が spec-first で「要件 → テスト前提の設計」を内包
  - `kiro:spec-impl` は TDD methodology 前提で実装する設計
  - **AI-driven 前提下**: TDD の red-green-refactor コストは AI にとってほぼ同等。「人時負荷高」を理由に却下できない（`development-model.md`）
- **判断期限**: 2026-05-19
- **暫定結論**: Kiro 4 フェーズ承認準拠 + **task 単位で TDD 採用デフォルト**（AI-driven 下でコスト同等のため）、例外時のみ実装先行を選択
- **判断主体**: maumau
- **クローズ条件**: `tasks.md` 生成時に「テスト先行 task」と「実装先行 task」の振り分け方針を明示
- **影響範囲**: `tasks.md` 構造 / 工数試算

---

## Closed Decisions

（判断確定したエントリはここに移動。entry 末尾に確定日と結論サマリを追記）

_現時点なし。_

---

## Decision Triggers (自動アラート想定)

以下の状況発生時に新規 D エントリを切る:

- 予算累積 $120 (M8 burn-rate gate) 超過 → スコープ縮退判断 (Tier A-F)
- 予算累積 $150 超過 → モデル切替 / 機能削減判断
- Foundry preview の breaking change リリース → 移行判断
- 5/11 議事録 L68-75 のオープン論点に追加検討が必要になった場合
- spec 横断の整合性問題発覚時（複数 spec 化した場合）

---
_流動文書。週次でレビュー。安定した決定は product.md / tech.md に昇格させる_
