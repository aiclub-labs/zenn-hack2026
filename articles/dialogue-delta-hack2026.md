---
title: "Dialogue Delta — 対話の最中に「自分は何を知ってるか」を捕まえる AI Agent"
emoji: "🧭"
type: "tech"
topics: ["azure", "openai", "containerapps", "fastapi", "hackathon"]
published: false
---

> 想定読者: 社内に蓄積された個々人の暗黙知を、どう「使える形」に翻訳していくかに悩むエンジニア / PM。Azure AI スタックでのマルチエージェント実装に興味がある方。

## TL;DR

- **Dialogue Delta** は、業務 AI チャットの応答品質を「対話の最中に自己批評 (self-critic) させ、低自信のところで 5W1H を聞き返す」アプローチで底上げする
- 聞き取った内容は **レビュアー承認 → corpus 化 → 次の対話で citation として返ってくる** ループを構成。暗黙知が個人の頭から AI Search index に流れる
- Microsoft Agent Hackathon Japan 2026 (Zenn) 向け、Azure Container Apps + AOAI + Cosmos + AI Search で実装、**1 マスあたりのスキーマ追加 ≤ 5 分** / 新マス開設 ≤ 1 日を達成

## 解こうとした課題

社内ナレッジ共有ツールは溢れている一方、「自分が現場で何と判断したか」「先週の暫定対応の中身」のような **暗黙知** は、本人が言語化する動機もタイミングも無いので、結局誰も書かない。Wiki に書かせる発想だと書く側の負担が重すぎる。

**仮説**: AI チャットボットに業務質問を投げる瞬間こそ、暗黙知が活性化している唯一のタイミング。ここで「自信ありげに答える」のではなく「君のほうが詳しいですよね、教えて」と聞き返すほうが、知識回収の総量が大きいのではないか。

ターゲット 3 ペルソナ:

| | 役割 | 名前 | 主要動作 |
|---|---|---|---|
| A | スキーマ管理者 | シゲル | マス (sector/unit) ごとの定義域を維持 |
| B | 業務ユーザー | ハルカ | 日常の質問・暫定判断の言語化 |
| C | レビュアー | タケシ | 聞き取り内容の真贋判定 → corpus 反映 |

## アーキテクチャ

Azure マネージドサービス縛りで以下構成:

```
ユーザー → Static UI (Container Apps + nginx) ──→ FastAPI (Container Apps)
                                                      │
                                              ┌───────┼────────────┐
                                              │       │            │
                                          AOAI    Cosmos DB     AI Search
                                       (gpt-5,    (NoSQL,      (vector +
                                       embed-3)   8 container) keyword)
```

**主要 Cosmos コンテナ** (partition key = `{sector}#{unit}`):

- `schemas` / `schema_audit_log` — マスごとのフィールド定義 + 改訂履歴
- `dialogue_turns` — 会話ログ (Redact 機密フラグで保存抑制可)
- `delta_events` — gap 検知ログ
- `hearout_records` — 5W1H 聞き取り transcript
- `formalization_queue` — レビュー待ちチケット
- `corpus_meta` — AI Search index と対応する正本メタ
- `truth_judgment_logs` — 真贋判定アンサンブル投票

**Agent 構成** (`app/agents/`):

| Agent | 役割 |
|---|---|
| `delta_detector` | self-critic + corpus 距離で gap を判定 |
| `hearout` | gap を起点に 5W1H を最大 5 ターン聞き出す |
| `formalization` | hearout を weighted ticket 化してキュー投入 |
| `truth_judgment` | 承認時に atomic claims を分解し ensemble で再判定 |
| `schema_gate` / `schema_manager` | スキーマ revision 管理 |
| `notification` | 24h SLA expired → Discord webhook |

## 対話 → スキーマ抽出のしくみ

### 1. self-critic + gap 判定

`POST /turn` で AOAI が応答すると同時に自分の自信を 0-10 で採点させる。`delta_detector` が以下ルールで gap を立てる:

```
gap = (self_critic < 3.0)
   OR (3.0 <= self_critic <= 9.5 AND distance > 0.4)
```

`distance` は応答内容と既存 corpus の embedding 距離。**「知らないことを高自信で答えた場合」も「既存知識から遠い具体事象」も両方拾える** よう、hard-gap と soft-gap の二段構え。

### 2. HearoutModal で 5W1H

gap_detected が true になると、Chat UI に modal が出て who / what / when / where / why / how を最大 5 ターンで聞き取る。ユーザーは「skip」も選べる (skip 率は KPI として観測)。

### 3. Formalization Queue

聞き取り完了で `formalization_queue` に `pending_review` チケットが入る。weight は 3 つの軸の合成:

- `weight_a` ... 内容の具体度 (固有名詞 / 時刻 / 数値の含有)
- `weight_b` ... ユーザー信頼度 (履歴の承認率)
- `weight_c` ... 矛盾度 (既存 corpus との距離)

### 4. レビュアーの承認 → Truth Judgment → corpus

タケシが Review UI で承認すると `truth_judgment` が走る:

- 内容を atomic claims に分解 (LLM)
- 各 claim を ensemble (異なる prompt × N 回) で真偽判定
- 整合性スコア ≥ 0.4 なら corpus.upsert (AI Search に embedding 投入)

### 5. 次の対話で citation

ハルカが「5/22 のクラックで自分が取った暫定対応、もう一度教えて」と聞き返すと、AI Search が hr-XXXX (hearout id) をヒットさせ、Chat 応答に **citation バッジ + weight** が表示される。さらに矛盾 record があれば `ConflictInline` で「他に N 件の異なる見解あり」と並列提示。

## 工夫したところ

### マルチテナント分離

`{sector}#{unit}` を Cosmos partition key にしてテナント間漏洩を構造的にブロック。ハッカソンデモ用に `strategy-poc/auto-mfg` (戦略 PoC) と `manufacturing-s8b/line-A` (製造) の 2 領域で同時運用しても、お互いの schema / record が見えない。

### モバイル対応

Fluent UI v9 の Combobox + `flexBasis: 100%` で 3 つの tenant 入力欄を縦 stack。最初は `flex: 1` で横並びにしていたが、390px だと user_id 欄が squeeze で消えるバグを Playwright UAT で発見、Pass 2 で修正。

### Affordance Map による UAT 防御

UAT シナリオを書く段で「sector/unit/user を切替」と書いただけだと、UI 側に user_id 入力欄が無いことを見落とす。`docs/UAT-SCENARIOS.md` 冒頭に **Affordance Map** を入れ、「シナリオ要求操作」と「対応する UI 要素」を 1:1 で突き合わせるルールにした。

### ハッカソン提出 36h 前の Demo Critical Path

S4.1 デモ通し (起承転結 5 段) を Playwright で自動再生し、74 秒の動画にまとめた。実 chat で hearout modal を出せない不具合があったが、API 経由でテストデータを seed して C1 (承認) + B3 (citation) は通常 UI で証明、B2 (modal) だけ字幕補足する形にして提出物の整合性を保った。

## ハマったところ

### self-critic が高止まりして gap が起動しない

最大の問題。プロンプトが「答えの体裁」を採点しているため、AI が「参考情報には記載がありません」と答えても 9.0/10 と自己評価してしまう。threshold を `6.5 → 9.5` に上げて緩和したが、根本対策は prompt 書き直し (post-提出 TODO)。

### Windows + Docker で `tsc: Permission denied`

ローカル `node_modules` (Windows 権限) が `COPY . .` でコンテナに混入し、Linux 上で `tsc` バイナリの実行権限が落ちる。`.dockerignore` に `node_modules` / `dist` / `**/*.tsbuildinfo` を入れて解決。`tsbuildinfo` が composite project の `.d.ts` 出力を skip させる別バグも踏んだことがあるので、両方一度に防御。

### Azure CLI の cp932 UnicodeEncodeError

ACR build のログストリーミングが `✓` (✓) でクラッシュする (`UnicodeEncodeError: 'cp932' codec can't encode...`)。build 自体は成功するがログが途切れる。`PYTHONIOENCODING=utf-8 PYTHONUTF8=1` を前置することで回避。

### Fluent UI Combobox の onChange

Fluent UI v9 の `Combobox` は `onOptionSelect` (リスト選択) と `onChange` (フリー入力) で別ハンドラを書く必要がある。最初 `onChange` だけ書いてリスト選択で値が反映されない罠を踏んだ。

## デモ

74 秒の通し動画 (1080p):

`output/demo/demo-s41-stand-in.mp4`

| 段 | 内容 |
|---|---|
| 起 (A1) | Admin schemas 一覧 + 新規追加 modal |
| 承1 (B1) | Chat 一般質問 → citation 自動表示 (self-critic 7.0) |
| 承2 (B2) | gap query → critic 1.0 で低自信検知 |
| 転 (C1) | Review queue → weight 0.82 承認 |
| 結 (B3) | citation 2 件 + ConflictInline 「他 2 件の異なる見解あり」 |
| モバイル | 同じ UI が 390px viewport で操作可 |

## チーム / 開発体制

[AI Club](https://x.com/) ラボの 4 名チームで参加。Microsoft 公式の Agent Hackathon Japan 2026 (Zenn ベース) で、運営側が用意した Azure サブスクリプションを使い、無料枠 + 公式 PAYG クレジットの範囲で実装。

開発スタイル:

- **Kiro spec-driven workflow** で Requirements → Design → Tasks → Implementation を段階レビュー
- **Claude Code (Opus 4.8)** をペアプログラマとして全工程で活用、特に UI/UX のモバイル対応と UAT 自動化 (Playwright MCP) が高速化
- ブランチ戦略: feature/domain-pivot-consultant-tacit に集約、main へは提出直前にマージ
- リポジトリ: [aiclub-labs/zenn-hack2026](https://github.com/aiclub-labs/zenn-hack2026)

## おわりに / 今後

「対話の最中に自信を採点させ、低自信のところで聞き返す」というシンプルなアイデアが、ナレッジマネジメントの根本的な摩擦 (=書く動機がない) を回避できる可能性を示せた、と思います。

今後の課題:

1. **self-critic prompt 改修** — 「知らないことを知らないと答えた」を高評価できるよう書き直し
2. **Entra ID 統合** — 現状 `DEV_SKIP_AUTH=true` で素通り、本番では app_role による gating
3. **5W1H の自動充足** — hearout で再質問なしに dialogue 履歴から補完
4. **多言語対応** — 現状 ja-JP 固定、グローバル展開時の翻訳パス検討

> 興味を持っていただけた方、issue / PR お待ちしています。
