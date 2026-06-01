# Impact Assessment — dialogue-delta-formalization

> 作成: 2026-05-28 / 用途: Microsoft Agent Hackathon 提出向け Responsible AI 自己評価。MS RAI Standard v2 / Trusted AI / NIST AI RMF (Map) の Impact Assessment 要件を 1 枚に圧縮。
> 関連: `personas-stories.md`, `risks.md` (R-01〜R-07), `framework-review.md` (gap matrix #4)

---

## 1. システム概要

**目的**: 業務対話 (Persona B) の最中に AI が自己批評で「自身の応答が弱い」と判定した瞬間を捕まえ、Hearout エージェントが 5W1H ヒアリングで暗黙知を引き出し、Truth Judgment + 人間レビューを経て組織 corpus に形式化する。

**意図する利用**: エンタープライズコンサル業務における特定セクター × ユニットでの (a) 業務対話補助、(b) ベテラン知見の組織資産化、(c) 後続対話への引用提示。

**意図しない利用 (out-of-scope)**:
- 採用判断、人事評価、業績考課への流用
- 医療診断、法的助言、安全クリティカル操作の自動化
- 個人の生産性スコアリング / サーベイランス用途
- 公開 AI チャットボット / 一般消費者向け応答生成
- ハッカソン提出時点では実顧客データへの接続なし、すべて seed data

---

## 2. ステークホルダー × Harm × Mitigation マトリクス

| # | ステークホルダー | 想定 Harm | 重大度 | 確度 | 主たる Mitigation | コード/設計の根拠 |
|---|---|---|---|---|---|---|
| H1 | **Persona B (業務ユーザー / 供給側)** | ヒアリング介入が連続して業務リズム破壊 → 全 skip → 暗黙知収集失敗 (R-06) | M | M | 介入は skip 自由、5 ターン上限、自己批評スコア閾値による発火制御 | `requirements.md:189-192`, `requirements.md:312` |
| H2 | Persona B | 機密案件の発話が redact 漏れで corpus 化 → 監査懸念 | H | M | redact フラグ UI + emit 直前 PII scrubber + 論理削除 (`is_active=false`) + 引用先連鎖 | `requirements.md:215-219, 375, 387`, `app/util/pii.py` |
| H3 | Persona B | 自分の判断が誤って novel/conflict 判定され、後続応答に引用されない | L | M | 編集後の Truth Judgment 再実行 + reviewer 編集後の差分 audit log | `requirements.md:342`, `tasks.md:36` |
| H4 | **Persona A (Admin / シゲル)** | スキーマ変更が業務側に通知されず認識ズレ → ヒアリング過剰 → 業務離脱 | M | M | Schema 更新の同期 push 通知 + 履歴 view (Req 2.6-2.7) | `design.md:447-471` |
| H5 | **Persona C (Reviewer / タケシ)** | 24h SLA 超過 → expired → 業務側に redo 負担 | M | M | SLA タイマー UI 表示 + expired 後の自動再投入 + reviewer scope RBAC | `requirements.md:251-256, 288, 389` |
| H6 | Persona C | 重み breakdown 不可解で全件承認 → corpus 汚染 | H | M | Self-approval 率 > 30% で warning、breakdown tooltip (A×B×C)、TJ verdict バッジ、Citation ID で出典 turn 表示 | `requirements.md:252-254, 247, 206` |
| H7 | **供給側 (R-01)** | 「自分の知見を共有 → 自分の希少性低下」懸念で協力拒否 → corpus 不毛 | H | M | Citation 数の可視化 (Phase 2)、完全匿名化オプション、共有しない選択を許容 | `risks.md:R-01`, `design.md` (Phase 2) |
| H8 | **組織 / 経営層** | Corpus が偏ったベテラン view に固定化 → 多様な意見が排除 → 組織意思決定の単一化 | M | L | sector×reviewer 別 approval/reject 率 KPI、conflict_detected の coexist 選択肢 (`requirements.md:271`) | `requirements.md:254, 271`, T3 (Phase 2 で監視ダッシュボード) |
| H9 | **AI モデル (gpt-4o / gpt-4o-mini)** | プロンプトインジェクションで PII 流出 or 不正な corpus 投入 | H | L | Foundry content filter + Truth Judgment 検証 + 3 段 HITL ゲート | `design.md:117-127, 489-499` |
| H10 | **個人 (一般)** | 言語固定 ja-JP、accessibility 未検証 → スクリーンリーダー利用者・非日本語話者が排除 | M | H | 提出時は scope 限定 (3 persona × ja-JP) を明示、WCAG 監査は Phase 2 | `spec.json` language=ja, `handoff-uat.md:108` |
| H11 | **データ (Cosmos partition)** | テナント越境で他マスの corpus が混入 | H | L | partition key `{sector}#{unit}` を全 12 collection で強制 + AI Search filter | `requirements.md:357, 360`, `contracts.md:228` |
| H12 | **コスト / 環境** | AOAI トークン暴発で予算超過 / carbon footprint 増 | M | M | $200 上限 + forecast budget + Tier A/C 縮退 + scale-to-zero + serverless | `budget.bicep:17-42`, `requirements.md:36, 396-398` |

---

## 3. 残存リスクと開示

### 残る重要な不確実性 (提出時点で未解決)

1. **Fairness audit の本格実装は Phase 2** — H8 に対する monitoring は self-approval 率 > 30% warning のみ。sector × demographic 別の bias 検知は post-hack
2. **PII scrubber は regex MVP** — H2 の mitigation 強度は中程度。Req 16.6 の「LLM scrubbing」は Phase 2 (詳細: `framework-review.md` gap #2)
3. **Real-LLM eval は未実施** — Truth Judgment の品質は scripted golden 10 件 (`tests/test_tj_golden.py`) で aggregation 決定論のみ検証済。precision/recall は実トラフィック収集後 (詳細: `framework-review.md` gap #1)
4. **Red-team / Prompt injection 検証は未実施** — H9 は設計上の多層防御で対応、adversarial test は post-hack
5. **Adversarial fairness probe (例: 同一内容を異なる sector で投入し reject 率を比較) 未実施**

### 利用者への開示 (Transparency)

- **Persona B 向け**: chat UI に「この応答は AI が生成、自己批評スコアで品質評価」表示 (T6 で実装予定)
- **Persona C 向け**: 重み breakdown tooltip + TJ verdict バッジ + Citation ID で「なぜこの record か」を 1 画面提示済 (`requirements.md:206, 247, 252`)
- **組織管理者向け**: 本ドキュメント + `framework-review.md` を README 経由で公開、自己評価結果と Phase 2 ロードマップを開示

---

## 4. 適用フレームワークとの対応

| フレームワーク | 該当要件 | 本 doc 対応セクション |
|---|---|---|
| MS RAI Standard v2 | Accountability / Impact Assessment | §1 (意図利用)、§2 (Harm × Mitigation)、§3 (残存リスク) |
| Trusted AI | Accountability / Safety / Fairness | §2 H1-H8, §3.1 |
| NIST AI RMF | Map function (context, risks, stakeholders) | §1, §2 全体 |
| Azure WAF AI Workload | Responsible AI 統合 | §2 H9, H11 (Security / Reliability) |
| AWS GenAI Lens | Impact scoping phase | §1, §2 (responsibilities) |

---

## 5. レビュー責任と更新サイクル

- **本 doc の owner**: オペレータ (Mao)
- **次回見直し契機**: (a) ドメイン乗り換え時 (D1/D2/D3 投票結果による)、(b) Phase 2 着手時、(c) 重大インシデント発生時
- **チーム合意プロトコル**: 本 doc を `#hack-chat` で共有、24h 異論なければ「審査時点での RAI 自己評価」として確定

---

**End of impact-assessment.md** — 12 harm × mitigation × file:line 出典付き。`framework-review.md` gap #4 を解消。
