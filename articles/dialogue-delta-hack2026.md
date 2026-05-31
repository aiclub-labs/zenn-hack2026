---
title: "Dialogue Delta — 業務 AI 利用の最中に「自分が再発見した方法論」を捕まえる Agent"
emoji: "🧭"
type: "tech"
topics: ["azure", "openai", "containerapps", "fastapi", "hackathon"]
published: false
---

> 想定読者: 社内に散らばる業務ノウハウ (Excel の数式設計、Power Query 前処理レシピ、Copilot プロンプト型、スライドを HTML で組み直す型、Power Automate フロー…) を、形式知として再利用可能な形に翻訳していくことに悩むエンジニア / PM。Azure AI スタックでのマルチエージェント実装に興味がある方。

## TL;DR

業務の中で「Excel の数式構造を考えた」「PowerPoint を手作業で組まず Marp / HTML で書き直した」「Power Query で日付テキスト揺れを一気に正規化する型を作った」── そういう **方法論 / ナレッジ / 効率化のコツ** は、誰もが頭の中で繰り返し再発見しているのに、Wiki にも勉強会にも残らない。生成系 AI ツールを日常で使うほどこの再発見の機会は増えるが、書く動機がない以上は **個人の頭** に閉じ込められる。

**Dialogue Delta** は、社内 AI チャットボットが自分の応答に「自信」を採点 (self-critic) させ、低自信のところで「君のほうが詳しいよね、教えて」と聞き返す仕掛けで、その瞬間にしか取り出せない暗黙知を在席のまま蓄積する。承認されたものは AI Search 経由で次の対話の citation として返り、人気のものは ranking で「全社で共有する価値あり = `general` 昇格候補」として可視化される。

Microsoft Agent Hackathon Japan 2026 (Zenn) 向け、**Azure Container Apps + AOAI (gpt-5 / embed-3-small) + Cosmos DB + AI Search** で実装。

## 解こうとした課題

社内ナレッジ共有ツールは溢れている一方、「**自分は Excel で長い数式をどう可読化したか**」「**Power Query で日付テキストをどう正規化したか**」「**Copilot に議事録 → 1pager を投げるときの prompt 型**」のような **業務効率化の方法論** は、本人が言語化する動機もタイミングも無いので、結局誰も書かない。Wiki に書かせる発想だと、書く側の負担が重すぎる。

**仮説**: AI チャットボットに業務質問を投げる瞬間こそ、その方法論が活性化している唯一のタイミング。ここで AI が「自信ありげに答える」のではなく「君のほうが詳しいですよね、教えて」と聞き返すほうが、知識回収の総量が大きいのではないか。

ターゲット 3 ペルソナ:

| | 役割 | 名前 | 主要動作 |
|---|---|---|---|
| A | スキーマ管理者 | シゲル | マス (sector/unit) ごとの方法論カテゴリ定義を維持 |
| B | 業務ユーザー | ハルカ | 日常の質問・自分の手順の言語化 |
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

**partition の階層**:

```
general#general   ← 業務一般 (Excel / Power Query / Copilot / Office Scripts / Power Automate)
{sector}#{unit}   ← セクター・部門固有 (consulting/kpmg-genai 等)
```

Chat の retrieval は **`{current tenant} ∪ general#general`** を `OR` で引く。汎用 tips は全テナントに自動的に届き、組織固有ノウハウは漏れない。

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

`POST /turn` で AOAI が応答すると同時に、自分の自信を 0-10 で採点させる。`delta_detector` が以下ルールで gap を立てる:

```
gap = (self_critic < 3.0)
   OR (3.0 <= self_critic <= 9.5 AND distance > 0.4)
```

`distance` は応答内容と既存 corpus の embedding 距離。**「知らないことを高自信で答えた場合」も「既存知識から遠い具体事象」も両方拾える** よう、hard-gap と soft-gap の二段構え。

### 2. HearoutModal で 5W1H

gap_detected が true になると、Chat UI に modal が出て who / what / when / where / why / how を最大 5 ターンで聞き取る。ユーザーは「skip」も選べる (skip 率は KPI として観測)。

### 3. Formalization Queue

聞き取り完了で `formalization_queue` に `pending_review` チケットが入る。weight は 3 つの軸の合成:

- `weight_a` … 内容の具体度 (固有名詞 / 数値 / 手順の含有)
- `weight_b` … ユーザー信頼度 (履歴の承認率)
- `weight_c` … 矛盾度 (既存 corpus との距離)

### 4. レビュアーの承認 → Truth Judgment → corpus

タケシが Review UI で承認すると `truth_judgment` が走る:

- 内容を atomic claims に分解 (LLM)
- 各 claim を ensemble (異なる prompt × N 回) で真偽判定
- 整合性スコア ≥ 0.4 なら corpus.upsert (AI Search に embedding 投入)

### 5. 次の対話で citation + ranking

ハルカが「Power Query で日付テキスト揺れを直す自分のレシピ、もう一度教えて」と聞くと、AI Search が該当 record をヒットさせ、Chat 応答に **citation バッジ + weight** が表示される。矛盾 record があれば `ConflictInline` で「他に N 件の異なる見解あり」と並列提示。

評価は Good / Bad ボタンで蓄積され、`/popular` ページに **ranking** として可視化される。**Ranking 上位 = 全社で共有する価値 = `general` 昇格候補** という意味付け。

## 工夫したところ

### a. `general` ↔ tenant の階層モデル

ChatGPT / Copilot のような汎用 LLM は global only だが、業務利用では「**会社や部門を越えて共通する tips (Excel LET, Power Query レシピ)**」と「**所属組織だけの方法論 (xxx 案件用のスライド雛形)**」が混在する。

これを `partition key = {sector}#{unit}` で構造的に分け、Chat retrieval 時に `{current} ∪ general#general` を OR で引く実装にした。

```python
# app/util/aisearch.py
tenant_clause = (
    f"(sector eq '{tenant.sector}' and unit eq '{tenant.unit}')"
    " or (sector eq 'general' and unit eq 'general')"
)
```

これだけで「皆で共有する」と「組織に閉じる」が両立する。

### b. マルチエージェントの役割分離

`delta_detector` / `hearout` / `formalization` / `truth_judgment` を独立 Agent として実装し、それぞれが Cosmos の別コンテナを所有 (`delta_events` / `hearout_records` / `formalization_queue` / `truth_judgment_logs`)。

メリット:

- **デバッグ可能性**: 「なぜこの query で modal が開いた / 開かなかった」を `delta_events` の `matched_reason` から逆引きできる
- **責務単一**: hearout の prompt 改修と TJ の prompt 改修が独立に走る
- **段階的な置換**: hearout を別の LLM に切り替えても他 Agent に影響なし

### f. Ranking による「個人 → 全社昇格」の自然なパス

`votes` コンテナで Good / Bad の集計を持ち、`/popular` で表示。上位記事は **「全社で共有する価値あり = general に昇格させる候補」** と意味付けし、reviewer の手動 / 自動移管経路を後述の Phase 3 で実装する設計余白を作った。

これにより、個人テナントの暗黙知が組織知に「**ボトムアップで昇格していく**」 構造が生まれる。

### g. Cosmos partition で構造的なテナント隔離

コンサル業務だと「クライアントの方法論を別クライアントに見せない」「法人内でも事業部間で隔離」のガバナンスが必須。

これを RBAC ではなく **partition key そのもの** で構造的に防ぐ。`pk eq '{sector}#{unit}'` を AI Search filter / Cosmos query の全経路に強制し、誤って別 partition が見える可能性を物理的に消した。`DEV_SKIP_AUTH=true` を切れば Entra ID app_role による gating も入る (現状デモ環境は素通り)。

## ハマったところ

### H1. self-critic が高止まりして gap が起動しない

最大の問題。プロンプトが「答えの体裁」を採点しているため、AI が「参考情報には記載がありません」と答えても 9.0/10 と自己評価してしまう。

threshold を `6.5 → 9.5` に上げて緩和したが、根本対策は prompt 書き直し (post-提出 TODO)。

### H2. Windows + Docker で `tsc: Permission denied`

ローカル `node_modules` (Windows 権限) が `COPY . .` でコンテナに混入し、Linux 上で `tsc` バイナリの実行権限が落ちる。

`.dockerignore` に `node_modules` / `dist` / `**/*.tsbuildinfo` を入れて解決。`tsbuildinfo` が composite project の `.d.ts` 出力を skip させる別バグも踏んだことがあるので、両方を一度に防御。

### H3. Azure CLI の cp932 UnicodeEncodeError

ACR build のログストリーミングが `✓` (Unicode チェックマーク) でクラッシュする (`UnicodeEncodeError: 'cp932' codec can't encode...`)。build 自体は成功するがログが途切れる。

`PYTHONIOENCODING=utf-8 PYTHONUTF8=1` を前置することで回避。Windows 環境で Azure 系 CLI を回す全コマンドの標準前置にしている。

### H4. Fluent UI Combobox の onChange / onOptionSelect 二系統

Fluent UI v9 の `Combobox` は `onOptionSelect` (リスト選択) と `onChange` (フリー入力) で別ハンドラを書く必要がある。最初 `onChange` だけ書いてリスト選択で値が反映されない罠を踏んだ。

```tsx
<Combobox
  freeform
  value={tenant.sector}
  selectedOptions={[tenant.sector]}
  onOptionSelect={(_, d) => d.optionValue && setTenant({...tenant, sector: d.optionValue})}
  onChange={(e) => setTenant({...tenant, sector: (e.target as HTMLInputElement).value})}
>
  {SECTOR_OPTIONS.map((s) => <Option key={s} value={s}>{s}</Option>)}
</Combobox>
```

## デモ

60 秒の通し動画 (1440×900 / live capture):

`output/demo/demo-s41-live-v2.mp4`

| 段 | 内容 |
|---|---|
| 起 (A) | Admin で 5 schema (Excel数式 / PowerQuery / OfficeScripts / Copilot / PowerAutomate) を確認 |
| 承1 (B) | Chat「Excel で長い数式を可読化するコツは?」→ LET / LAMBDA を citation 3 件付きで応答 |
| 承2 (B) | Chat「先週の KPMG 案件で自分は LET をどう使ったか?」→ gap 検知 |
| Ranking | `/popular` で人気ノウハウを weight 順表示 |
| Cutaway | tenant を `consulting/kpmg-genai` に切替 → 組織固有領域も存在することを瞬間提示 |
| 転 (C) | Review queue で 1 件承認 → corpus 反映 |
| 結 (B) | Chat「Power Query で日付テキスト揺れを直す自分のレシピは?」→ 自分の暗黙知が citation で返る |

## チーム / 開発体制

AI Club ラボの 4 名チームで参加。Microsoft 公式の Agent Hackathon Japan 2026 (Zenn ベース) で、運営側が用意した Azure サブスクリプションを使い、無料枠 + 公式 PAYG クレジットの範囲で実装。

開発スタイル:

- **Kiro spec-driven workflow** で Requirements → Design → Tasks → Implementation を段階レビュー
- **Claude Code (Opus 4.8)** をペアプログラマとして全工程で活用、特に UI/UX のモバイル対応と UAT 自動化 (Playwright MCP) が高速化
- ブランチ戦略: `feature/domain-pivot-consultant-tacit` に集約、main へは提出直前にマージ
- リポジトリ: [aiclub-labs/zenn-hack2026](https://github.com/aiclub-labs/zenn-hack2026)

self-critic 文化はチームにも持ち込んだ。「これは自信ある / これは曖昧」を PR レビューで明示するよう統一し、agent が AI に対して持つ規律と人間チームが互いに持つ規律を揃えた。

## 今後

### 主柱: 社内版 Zenn / Qiita としての段階拡張

現状は「**受動経路**」(=対話の最中に AI が引き出す) のみ。これと表裏一体で「**能動経路**」(=人が書く動機をもって自発投稿する) を後付けで重ねていく構想。

| Phase | 範囲 | 達成状態 |
|---|---|---|
| **1 (MVP / 提出時点)** | **受動経路**: Chat 利用中の hearout で暗黙知を引き出し → reviewer 承認 → corpus + ranking | 本記事時点 |
| **2** | **能動経路追加**: 同一 corpus への直書き UI (markdown editor + schema 選択)。自分 partition なら self-publish、別 partition (`general` 等) なら reviewer 承認必須 | hearout と能動投稿が同じ knowledge graph に統合 |
| **3** | **社内ソーシャル化**: いいね / コメント / フォロー / `@user` mention で対話呼び出し / 編集履歴。ranking が社内 engagement signal にもなる | 真の「社内版 Zenn」完成 |

設計の整合性:

- 受動 (hearout) と能動 (投稿) が **同一 schema / 同一 corpus / 同一 reviewer フロー** を使う → 機能重複なく拡張可能
- schema が **投稿テンプレ役** として働く (= `sf_excel_formula_technique` は「Excel テクニック記事タイプ」のテンプレート)
- 真贋判定 (TJ) は能動投稿では skip (自信ある書き手の意思を尊重)
- 「**人の頭から汲み取る (hearout)**」+「**人が能動的に書く (post)**」+「**皆が引く (chat citation)**」+「**皆が評価する (vote / ranking)**」の 4 経路で knowledge graph が育つ

### その他の改善

1. **self-critic prompt 改修** — 「知らないことを知らないと答えた」を高評価できるよう書き直し
2. **「個人 → 全社昇格」のガバナンス設計** — ranking 上位 record の `general` 昇格を reviewer フローに乗せる (自動 vs 手動の境界設計)
3. **Entra ID 統合** — 現状 `DEV_SKIP_AUTH=true` で素通り、本番では app_role による gating
4. **5W1H の自動充足** — hearout で再質問なしに dialogue 履歴から補完

---

「対話の最中に自信を採点させ、低自信のところで聞き返す」というシンプルなアイデアが、ナレッジマネジメントの根本的な摩擦 (=書く動機がない) を回避できる可能性を示せた、と思います。

そして「能動投稿の経路を後付けで重ねる」という方向性が見えたことで、これは単なるハッカソンアプリではなく、**社内版 Zenn / Qiita プラットフォーム** への足場になり得る、というのが今回の最大の収穫でした。

> 興味を持っていただけた方、issue / PR お待ちしています。 [aiclub-labs/zenn-hack2026](https://github.com/aiclub-labs/zenn-hack2026)
