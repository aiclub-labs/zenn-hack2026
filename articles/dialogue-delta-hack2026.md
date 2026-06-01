---
title: "Dialogue Delta — 業務 AI 利用の最中に「自分が再発見した方法論」を捕まえる Agent"
emoji: "🧭"
type: "tech"
topics: ["azure", "openai", "containerapps", "fastapi", "hackathon"]
published: false
---

> 想定読者: 社内に散らばる業務ノウハウ (Excel の数式設計、Power Query 前処理レシピ、Copilot プロンプト型、スライドを HTML で組み直す型、Power Automate フロー…) を、形式知として再利用可能な形に翻訳していくことに悩むエンジニア / PM。Azure AI スタックでのマルチエージェント実装に興味がある方。

## TL;DR

業務の中で「Excel の数式構造を考えた」「PowerPoint を手作業で組まず Marp / HTML で書き直した」「Power Query で日付テキスト揺れを一気に正規化する型を作った」── そういう **方法論 / ナレッジ / 効率化のコツ** は、誰もが頭の中で繰り返し再発見しているのに、Wiki にも勉強会にも残りません。生成系 AI ツールを日常で使うほどこの再発見の機会は増えますが、書く動機がない以上は **個人の頭** に閉じ込められたままです。

**Dialogue Delta** は、社内 AI チャットボットが自分の応答に「自信」を採点 (self-critic) させ、低自信のところで「君のほうが詳しいよね、教えて」と聞き返す仕掛けで、その瞬間にしか取り出せない暗黙知を在席のまま蓄積します。承認されたものは AI Search 経由で次の対話の citation として返り、人気のものは ランキングで「全社で共有する価値あり = `general` 昇格候補」として可視化されます。

Microsoft Agent Hackathon Japan 2026 (Zenn) 向けに、**Azure Container Apps + AOAI (gpt-5.4 + gpt-5.4-mini / embed-3-small) + Cosmos DB + AI Search** で実装しました。

## まずは 90 秒のデモ動画 (overview)

文章を読む前に、何を作ったのか 90 秒で見ていただくのが早いです。**課題提示 → 実物ループ → 拡張ビジョン** の 3 幕構成になっています。

@[youtube](VIDEO_ID_HERE)

以下、この動画で起きていることの裏側を、背景 → アーキテクチャ → 仕組み → 工夫 の順に解説していきます。動画のシーン別ブレークダウンは、本体の後の「デモで何が見られるか」セクションで時刻付きの表に展開しています。

## 解こうとした課題

社内ナレッジ共有ツールは溢れている一方、「**自分は Excel で長い数式をどう可読化したか**」「**Power Query で日付テキストをどう正規化したか**」「**Copilot に議事録 → 1pager を投げるときの prompt 型**」のような **業務効率化の方法論** は、本人が言語化する動機もタイミングもないので、結局誰も書きません。Wiki に書かせる発想だと、書く側の負担が重すぎます。

**仮説**: AI チャットボットに業務質問を投げる瞬間こそ、その方法論が活性化している唯一のタイミングです。ここで AI が「自信ありげに答える」のではなく「君のほうが詳しいですよね、教えて」と聞き返すほうが、知識回収の総量が大きいのではないでしょうか。

ターゲット 3 ペルソナ:

| | 役割 | 名前 | 主要動作 |
|---|---|---|---|
| A | スキーマ管理者 | シゲル | マス (sector/unit) ごとの方法論カテゴリ定義を維持 |
| B | 業務ユーザー | ハルカ | 日常の質問・自分の手順の言語化 |
| C | レビュアー | タケシ | 聞き取り内容の真贋判定 → corpus 反映 |

## アーキテクチャ

Azure マネージドサービス縛りで、以下のような構成になっています。

```
ユーザー → Static UI (Container Apps + nginx) ──→ FastAPI (Container Apps)
                                                      │
                                              ┌───────┼────────────┐
                                              │       │            │
                                          AOAI       Cosmos DB     AI Search
                                       (gpt-5.4,    (NoSQL,      (vector +
                                       embed-3)    8 container)  keyword)
```

**主要 Cosmos コンテナ** (partition key = `{sector}#{unit}`):

- `schemas` / `schema_audit_log` — マスごとのフィールド定義 + 改訂履歴
- `dialogue_turns` — 会話ログ (Redact 機密フラグで保存抑制可)
- `delta_events` — ギャップ検知ログ
- `hearout_records` — 5W1H 聞き取り transcript
- `formalization_queue` — レビュー待ちチケット
- `corpus_meta` — AI Search index と対応する正本メタ
- `truth_judgment_logs` — 真贋判定アンサンブル投票

**partition の階層**:

```
general#general   ← 業務一般 (Excel / Power Query / Copilot / Office Scripts / Power Automate)
{sector}#{unit}   ← セクター・部門固有 (consulting/firm-a 等)
```

Chat の retrieval では **`{current tenant} ∪ general#general`** を `OR` で引きます。汎用 tips は全テナントに自動的に届き、組織固有ノウハウは漏れません。

**Agent 構成** (`app/agents/`):

| Agent | 役割 |
|---|---|
| `delta_detector` | self-critic + corpus 距離でギャップを判定 |
| `hearout` | ギャップを起点に 5W1H を最大 5 ターン聞き出す |
| `formalization` | hearout を weighted ticket 化してキュー投入 |
| `truth_judgment` | 承認時に atomic claims を分解し ensemble で再判定 |
| `schema_gate` / `schema_manager` | スキーマ revision 管理 |
| `notification` | 24h SLA expired → Discord webhook |

**認証 + ネットワーク境界**:

- **UI (Web Chat) Container App** に **Microsoft Easy Auth** (Microsoft Identity Provider) を有効化しています。Entra アプリ登録のサインイン対象 (sign-in audience) は **`AzureADandPersonalMicrosoftAccount`** に設定し、マルチテナントの組織アカウントと個人 Microsoft アカウントの両方を受け付ける構成にしました
- **未認証アクセス** は `RedirectToLoginPage` で `login.microsoftonline.com` に強制リダイレクトします
- **API Container App** は ingress を **internal-only** に変更し、外部 FQDN を消滅させました。UI の nginx が同 Container Apps Environment 内から HTTP で proxy 経由でのみ呼べる構成にし、API 直叩きを物理的に遮断しています
- アプリ内部の sector/unit/user 切替 (Combobox) は **認証通過後** にだけ有効になります。Easy Auth は入り口のみを守る薄い境界として動かしており、内部のテナント分離は別途 partition key で構造的に防御しています

## 対話 → スキーマ抽出のしくみ

### 1. self-critic + ギャップ判定

`POST /turn` で AOAI が応答すると同時に、自分の自信を 0-10 で採点させます。`delta_detector` が以下のルールでギャップを立てます:

```text
gap = (self_critic < 3.0)
   OR (3.0 <= self_critic <= 9.5 AND distance > 0.4)
```

`distance` は応答内容と既存 corpus の embedding 距離です。**「知らないことを高自信で答えた場合」も「既存知識から遠い具体事象」も両方拾える** よう、ハードギャップとソフトギャップの二段構えにしています。

### 2. HearoutModal で 5W1H

gap_detected が true になると、Chat UI に モーダルが出て who / what / when / where / why / how を最大 5 ターンで聞き取ります。ユーザーは「skip」も選べます (skip 率は KPI として観測しています)。

### 3. Formalization Queue

聞き取り完了で `formalization_queue` に `pending_review` チケットが入ります。ウェイトは 3 つの軸の合成です:

- `weight_a` … 内容の具体度 (固有名詞 / 数値 / 手順の含有)
- `weight_b` … ユーザー信頼度 (履歴の承認率)
- `weight_c` … 矛盾度 (既存 corpus との距離)

### 4. レビュアーの承認 → Truth Judgment → corpus

タケシが Review UI で承認すると `truth_judgment` が走ります:

- 内容を atomic claims に分解 (LLM)
- 各 claim を ensemble (異なる prompt × N 回) で真偽判定
- 整合性スコア ≥ 0.4 なら corpus.upsert (AI Search に embedding 投入)

### 5. 次の対話で citation + ランキング

ハルカが「Power Query で日付テキスト揺れを直す自分のレシピ、もう一度教えて」と聞くと、AI Search が該当 record をヒットさせ、Chat 応答に **citation バッジ + ウェイト** が表示されます。矛盾 record があれば `ConflictInline` で「他に N 件の異なる見解あり」と並列提示します。

評価は Good / Bad ボタンで蓄積され、`/popular` ページに **ランキング** として可視化されます。**ランキング上位 = 全社で共有する価値 = `general` 昇格候補** という意味付けにしています。

## 工夫したところ

### a. `general` ↔ テナントの階層モデル

ChatGPT / Copilot のような汎用 LLM は global only ですが、業務利用では「**会社や部門を越えて共通する tips (Excel LET, Power Query レシピ)**」と「**所属組織だけの方法論 (xxx 案件用のスライド雛形)**」が混在します。

これを `partition key = {sector}#{unit}` で構造的に分け、Chat retrieval 時に `{current} ∪ general#general` を OR で引く実装にしました。

```python
# app/util/aisearch.py
tenant_clause = (
    f"(sector eq '{tenant.sector}' and unit eq '{tenant.unit}')"
    " or (sector eq 'general' and unit eq 'general')"
)
```

これだけで「皆で共有する」と「組織に閉じる」が両立します。

### b. マルチエージェントの役割分離

`delta_detector` / `hearout` / `formalization` / `truth_judgment` を独立 Agent として実装し、それぞれが Cosmos の別コンテナを所有しています (`delta_events` / `hearout_records` / `formalization_queue` / `truth_judgment_logs`)。

メリット:

- **デバッグ可能性**: 「なぜこの query で モーダルが開いた / 開かなかった」を `delta_events` の `matched_reason` から逆引きできます
- **責務単一**: hearout の prompt 改修と TJ の prompt 改修が独立に走ります
- **段階的な置換**: hearout を別の LLM に切り替えても他 Agent に影響しません

### c. ランキングによる「個人 → 全社昇格」の自然なパス

`votes` コンテナで Good / Bad の集計を持ち、`/popular` で表示します。上位記事は **「全社で共有する価値あり = general に昇格させる候補」** として意味付けし、reviewer の手動 / 自動移管経路は後述の Phase 3 に設計余白として残しました。

これにより、個人テナントの暗黙知が組織知へ「**ボトムアップで昇格していく**」構造が生まれます。

### d. Cosmos partition で構造的なテナント隔離 + Easy Auth で外部攻撃面の縮減

コンサル業務では「クライアントの方法論を別クライアントに見せない」「法人内でも事業部間で隔離」のガバナンスが必須です。

これを RBAC ではなく **partition key そのもの** で構造的に防いでいます。`pk eq '{sector}#{unit}'` を AI Search filter / Cosmos query の全経路に強制し、誤って別 partition が見える可能性を物理的に消しました。

提出のタイミングでもう 1 段、**Microsoft Easy Auth + Entra アプリ登録 (multi-テナント + MSA)** を Container App 入口に被せ、未認証 URL アクセスを login.microsoftonline.com に強制リダイレクトするようにしました。**API 側 Container App は ingress を internal-only にし、UI の nginx が同 Environment 内から HTTP proxy で呼ぶ経路のみ残した** ことで、API URL の直叩きを物理的に遮断しています。

この 2 層 (入口 = Easy Auth、データ層 = partition key) で、URL の偶発露出から AOAI コスト爆発まで一気に塞ぐ構成にしています。

## デモで何が見られるか

冒頭の動画 (90 秒) を Act 別にブレークダウンしました。実機を触る前にこの順で見ていただくと、流れが入ってきます。

| Act | 時刻 | シーン | 何を確認すべきか |
|---|---|---|---|
| Act 1 (課題提示) | 0:00 - 0:15 | タイトルカード 3 枚 | 「業務 AI 利用で日々浮かぶ方法論」が共有手段なく個人の頭に閉じ込められる、という問題提起 |
| Act 2 - ①開幕 | 0:15 - 0:22 | Chat 待機 → Excel 質問入力 | 業務ユーザーが「Excel で長い数式を可読化したい」と素朴な質問 |
| Act 2 - ②citation | 0:22 - 0:32 | AI が LET 提案 + citation 3 件 | 組織共通 (general) 領域から自動引用される様子 — 汎用 LLM との差別化点 |
| Act 2 - ③ギャップ検知 | 0:32 - 0:42 | 「自分はどう使ったか?」+ self-critic 急落 | AI が知るはずもない個人経験を聞かれた瞬間、critic スコアが急落 = ギャップシグナル |
| Act 2 - ④Review 承認 | 0:42 - 0:52 | reviewer 切替 → ticket → 承認 | ウェイト 0.82 のチケットを reviewer が判定 → Truth Judgment → corpus upsert |
| Act 2 - ⑤ランキング | 0:52 - 0:60 | `/popular` で人気順 | 「全社で共有する価値あり」= `general` 昇格候補としての可視化 |
| Act 2 - ⑥閉ループ | 0:60 - 0:79 | 業務ユーザーに戻して PQ レシピ質問 | いま承認したばかりの自分の暗黙知が citation で返ってくる |
| Act 3 (ビジョン) | 0:79 - 0:89 | アウトロカード | 受動 + 能動 + 社内ソーシャル化 = 社内版 Zenn 構想 |

**動画の最終地点 (0:79)** で「自分の暗黙知が citation として返る」絵が出るところに注目していただきたいです。これが本アプリの核心です。

## できること (機能一覧)

ユーザー視点で 7 つの体験があります。

1. **Chat with citation** — 業務質問に対して、組織内で蓄積済みのノウハウを ウェイト付き citation で根拠提示します。`general` (全社共通) と `{sector}#{unit}` (組織固有) を OR で引いて返します
2. **ギャップ検知 (self-critic)** — AI が応答時に自信を 0-10 で自己採点します。低自信 / 既存 corpus から離れた応答をギャップとして立てます
3. **Hearout (5W1H 聞き取り)** — ギャップ検知時にモーダルを起動し、who / what / when / where / why / how を最大 5 ターンで聞き取ります
4. **Review queue (人間判断)** — 聞き取り内容は ウェイト順にチケット化され、reviewer が真贋判定 → Truth Judgment ensemble を経て corpus に反映されます
5. **ランキング (個人 → 全社昇格パス)** — Good / Bad 評価が集まったノウハウを ウェイト順に表示します。上位は `general` 昇格候補として扱います
6. **スキーマ管理** — マス (`{sector}#{unit}`) ごとのフィールド定義を admin が維持します。改訂は audit log に残ります
7. **テナント切替 + 認証** — Combobox で sector/unit を切替えられ、Microsoft Easy Auth (multi-テナント + 個人 MSA) で入口を守っています

## 今後の構想

### 主柱: 社内版 Zenn / Qiita としての段階拡張

現状は「**受動経路**」(=対話の最中に AI が引き出す) のみです。これと表裏一体で「**能動経路**」(=人が書く動機をもって自発投稿する) を後付けで重ねていく構想です。

| Phase | 範囲 | 達成状態 |
|---|---|---|
| **1 (MVP / 提出時点)** | **受動経路**: Chat 利用中の hearout で暗黙知を引き出し → reviewer 承認 → corpus + ランキング | 本記事時点 |
| **2** | **能動経路追加**: 同一 corpus への直書き UI (Markdown エディタ + スキーマ選択)。自分 partition なら self-publish、別 partition (`general` 等) なら reviewer 承認必須 | hearout と能動投稿が同じ knowledge graph に統合 |
| **3** | **社内ソーシャル化**: いいね / コメント / フォロー / `@user` mention で対話呼び出し / 編集履歴。ランキングが社内 engagement signal にもなる | 真の「社内版 Zenn」完成 |

設計の整合性:

- 受動 (hearout) と能動 (投稿) が **同一スキーマ / 同一 corpus / 同一 reviewer フロー** を使うので、機能重複なく拡張できます
- スキーマが **投稿テンプレ役** として働きます (例: `sf_excel_formula_technique` は「Excel テクニック記事タイプ」のテンプレート)
- 真贋判定 (TJ) は能動投稿ではスキップします (自信のある書き手の意思を尊重)
- 「**人の頭から汲み取る (hearout)**」+「**人が能動的に書く (post)**」+「**皆が引く (chat citation)**」+「**皆が評価する (vote / ランキング)**」の 4 経路で knowledge graph が育っていきます

## 残課題 (post-提出 TODO)

提出時点で意図的に残した、または運用前に解消する必要のある課題です。

1. **self-critic prompt の高止まり問題** — 「参考情報には記載がありません」と答えても 9.0/10 と自己評価してしまいます。threshold を 9.5 に上げて緩和しましたが、根本対策は prompt 書き直しです
2. **「個人 → 全社昇格」のガバナンス設計** — ランキング上位 record の `general` 昇格を reviewer フローに乗せる必要があります (自動 vs 手動の境界設計)
3. **Entra ID `app_role` gating** — 現状 Easy Auth は「ログインしてれば通す」だけです。本番では Persona A/B/C を Entra の `app_role` claim に対応させ、`/admin/*` `/review/*` のアクセス層を分けたいです
4. **5W1H の自動充足** — hearout の再質問を減らせるよう、dialogue 履歴から自動補完したいと考えています
5. **能動投稿 UI の MVP** — Phase 2 の Markdown エディタ + スキーマテンプレを早期に試作し、受動 / 能動の比率を計測する予定です

## 開発中にハマったところ

### H1. self-critic が高止まりしてギャップ検知が起動しない

最大の問題でした。プロンプトが「答えの体裁」を採点しているため、AI が「参考情報には記載がありません」と答えても 9.0/10 と自己評価してしまいます。

threshold を `6.5 → 9.5` に上げて緩和しましたが、根本対策は prompt 書き直しです (post-提出 TODO)。

### H2. Windows + Docker で `tsc: Permission denied`

ローカル `node_modules` (Windows 権限) が `COPY . .` でコンテナに混入し、Linux 上で `tsc` バイナリの実行権限が落ちます。

`.dockerignore` に `node_modules` / `dist` / `**/*.tsbuildinfo` を入れて解決しました。`tsbuildinfo` が composite project の `.d.ts` 出力を skip させる別バグも踏んだことがあるので、両方を一度に防御しています。

### H3. Azure CLI の cp932 UnicodeEncodeError

ACR build のログストリーミングが `✓` (Unicode チェックマーク) でクラッシュします (`UnicodeEncodeError: 'cp932' codec can't encode...`)。build 自体は成功しますがログが途切れます。

`PYTHONIOENCODING=utf-8 PYTHONUTF8=1` を前置することで回避できます。Windows 環境で Azure 系 CLI を回す全コマンドの標準前置にしています。

### H4. Fluent UI Combobox の onChange / onOptionSelect 二系統

Fluent UI v9 の `Combobox` は `onOptionSelect` (リスト選択) と `onChange` (フリー入力) で別ハンドラを書く必要があります。最初 `onChange` だけ書いてリスト選択で値が反映されない罠を踏みました。

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

### H5. 雑な sed scrub が import path まで書き換えて build を壊した

提出前の機密スクラブで `<旧テーマ名> → 法人` を全 tracked files に一括 sed した結果、`main.tsx` の `import { ... } from "./theme/<旧テーマ名>"` まで `"./theme/法人"` に書き換わってしまいました。**ファイル名のほうは `<旧テーマ名>.ts` のまま** だったので TS が module を解決できず、ACR build 失敗 → ImagePullBackOff → Container App revision が unhealthy になり、提出直前にユーザーが「ページが開けない」状態に陥りました。

対策はシンプルで、`<旧テーマ名>.ts` を `corporate.ts` にリネームして import path を揃えるだけですが、教訓は **「一括 sed scrub の後は CI build を必ず通す」** でした。今回はちょうど Easy Auth 設定 + 再ビルドのタイミングで露出して気付けました。

## チーム / 開発体制

AI Club ラボの 4 名チームで参加しました。Microsoft 公式の Agent Hackathon Japan 2026 (Zenn ベース) で、運営側が用意した Azure サブスクリプションを使い、無料枠 + 公式 PAYG クレジットの範囲で実装しています。

開発スタイル:

- **Kiro spec-driven workflow** で Requirements → Design → Tasks → Implementation を段階レビュー
- **Claude Code (Opus 4.8)** をペアプログラマとして全工程で活用、特に UI/UX のモバイル対応と UAT 自動化 (Playwright MCP) が高速化
- ブランチ戦略: `feature/domain-pivot-consultant-tacit` に集約、main へは提出直前にマージ
- リポジトリ: [aiclub-labs/zenn-hack2026](https://github.com/aiclub-labs/zenn-hack2026)

self-critic 文化はチームにも持ち込みました。「これは自信ある / これは曖昧」を PR レビューで明示するよう統一し、self-critic で AI に持たせた規律と人間チームが互いに持つ規律を揃えています。

---

「対話の最中に自信を採点させ、低自信のところで聞き返す」というシンプルなアイデアが、ナレッジマネジメントの根本的な摩擦 (=書く動機がない) を回避できる可能性を示せたのではないか、と思っています。

そして「能動投稿の経路を後付けで重ねる」という方向性が見えたことで、これは単なるハッカソンアプリではなく、**社内版 Zenn / Qiita プラットフォーム** への足場になり得る、というのが今回の最大の収穫でした。

ここまでお読みいただきありがとうございました。Zenn のコメント欄で感想や意見をいただけると普通にうれしいです。

リポジトリも公開しているので、よかったら覗いてみてください:
[aiclub-labs/zenn-hack2026](https://github.com/aiclub-labs/zenn-hack2026)
