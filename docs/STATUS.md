# ハッカソン — ステータス

> **ライブ実行状態。** 毎セッション更新。タイムラインは [ROADMAP.md](./ROADMAP.md) を、ナビゲーションは [INDEX.md](./INDEX.md) を参照。

**最終更新:** 2026-05-12（M6 テーマ確定: 暗黙知形式化 dialogue-monitoring 方式 + idea-f 作成 + Kiro spec init + 先行事例リサーチ #1 完了）

## 完了したこと

- **M0** ✅ 部門選択: 法人部門 (法人 AI部) — 2026-04-23
- **M1** ✅ Azure アカウント開設; $200 クレジットを portal の Cost Management → Credits で確認済
- **M2** ✅ GitHub リポジトリ `aiclub-labs/zenn-hack2026`（private）作成; scaffold を `main` に push（58 ファイル、77 オブジェクト、~59 KiB）
- **M2.1** ✅ 3 名分の GitHub collaborator 配線完了（オペレータ + `member-a` + メンバー 3）on `aiclub-labs/zenn-hack2026` — 2026-04-29
- **ツールチェーン** ✅ `az` / `azd` / `gh` / `jq` / `bicep` / `bun` を Windows + PowerShell 7+（WezTerm）で導入
- **Pre-push レビュー** ✅ code-reviewer agent が 7 件指摘 + Bicep 関連 3 件追加修正 — すべて適用; Bicep はクリーンにコンパイル（warning ゼロ、error ゼロ）
- **ドキュメント整理** ✅ このファイル + ROADMAP + INDEX を新規作成; 既存 4 ドキュメントから重複ステートを削除
- **M4 step 1（phase0 partial）** ✅ Sub を `Azure subscription 1` → `hack2026` にリネーム; タグマージ（`project=hack2026`、`event=microsoft-agent-hackathon-2026`、`managedBy=bicep`）; オペレータを sub scope の **Owner** にアサイン。Spending limit On。テナント displayName は "Default Directory" のまま — 個人 MSA ルートのテナントは read-only（化粧上の話、許容）。スクリプトのバグ修正:（a）`az account update` は存在しない → sub rename を `az rest` POST `/providers/Microsoft.Subscription/rename` に切替;（b）Windows-PowerShell-az で Graph `--body` JSON が壊れる → tempfile body 渡しに切替。両方 `scaffold/scripts/bootstrap-phase0.ps1` に landing 済み
- **M4 step 2（phase0 re-run）** ✅ 2026-04-29。M2/M3 の UPN を渡して `bootstrap-phase0.ps1` を再実行。両 teammate のゲストユーザーオブジェクトがテナントに作成（`PendingAcceptance` 状態、UPN サフィックスは `#EXT#@...onmicrosoft.com`）。OID は Graph フィルタ `userType eq 'Guest'` で解決可能。Sub-scope Contributor RBAC ステップは意図的に **スキップ** — スクリプトの `az ad user show --id <email>` がゲスト UPN マングリングで失敗する既知の癖、かつオペレータの「自分のみ admin auth」の意向を踏まえ、`rbac.bicep` で適用される RG-scope のみの Contributor のほうが厳しめ。結果: 招待を accept + `azd provision` 実行までは teammate に権限ゼロ
- **M4 step 3（phase1）** ✅ 2026-04-29。`bootstrap-phase1.ps1` 実行: Resource Provider を 10 個登録、OID（ゲスト UPN ルックアップの癖を回避するため OID を直接渡す形に）を `infra/main.parameters.json` に書込、what-if プレビューはクリーン（25 Create / 0 Modify / 0 Delete）。最終パラメータ: `memberObjectIds=[df9f49d3-..., 36fc9993-..., 0648cd6b-...]`、`ownerObjectId=df9f49d3-...`（オペレータ）、`budgetContactEmails=[tenant-redacted@gmail.com]`
- **M4 step 4（azd provision 相当）** ✅ 2026-04-29 21:00 JST。`az deployment sub create` を直接使用（azd 認証が初期化されていないため。同じ Bicep、同じ結果、`azd auth login` 不要）。プラットフォーム側の 2 つの問題で 3 回の試行が必要 — postmortem は下の「Recent decisions」を参照。最終 deployment `hack2026-init-3` が 1m36s で成功。**25 リソース / 3 RG / 12 RBAC アサイン / 1 budget / 1 policy / 1 lock すべて landing。** 確認済: 3 名分の RG-scope Contributor on dev、3 名分の KV Secrets Officer + Storage Blob Data Contributor on shared、sub-scope はオペレータのみ（Owner）。`rg-hack2026-shared` には `CanNotDelete` lock があり、Contributor 権限であっても shared インフラの誤削除をブロック
- **Discord onboarding（D1）** ✅ 解決済 — 3 名とも `Hackathon Team` ロール付与済、`#hack-chat` 等アクセス可。D2–D4 は引き続き open
- **M6 テーマ確定** ✅ 2026-05-11 ミーティングで **暗黙知形式化（dialogue-monitoring 方式）** を採択。idea-e（文書 ingestion 中心）から構造シフト
- **idea-f 作成** ✅ 2026-05-12 — `architecture-cards/idea-f-dialogue-monitoring.md`（12 セクション、対話差分監視 + 5W1H ヒアリングを正本構成として確定）
- **Kiro spec init** ✅ 2026-05-12 — `scaffold/.kiro/specs/dialogue-delta-formalization/` を初期化（spec.json + requirements.md の Project Description）。phase: `initialized`
- **先行事例リサーチ #1** ✅ 2026-05-12 — `research/tacit-knowledge-ai-prior-art.md`。Kunumi (arXiv 2507.03811) の自己批評スコア + EffiARA の信頼度集約 + GraphCheck/FactCheck の正誤判定方式を spec ベースラインに反映済
- **対象セクター×ユニット候補マトリクス** ✅ 2026-05-12 — `research/sector-unit-candidates.md`。5 候補（A/D/B 推奨順）。5/14 セッション議論材料
- **リサーチ #2 Azure Agent Platform 選定** ✅ 2026-05-12 — `research/azure-agent-platform-decision.md`。**Microsoft Agent Framework 1.0 (2026-04-03 GA、SK + AutoGen 統合後継) + Foundry Agent Service (本体無料) のハイブリッド構成**を採用候補に確定。HITL は MAF 標準機能 (`RequestInfoEvent`) で自前実装不要。Week 1 flag day (2026-05-18) で Hosted agent 実機検証後に最終判断。requirements.md + idea-f §4 に反映済

## デプロイ済 Azure リソース（カノニカル名一覧）

> すべてサブスクリプション `hack2026`（`2c29a97c-08b6-4bc3-88ea-266eb1cfd730`）、リージョン `swedencentral`。確認は `az resource list --subscription 2c29a97c-08b6-4bc3-88ea-266eb1cfd730 -o table`。

| 名前 | 種別 | RG |
|---|---|---|
| `cae-hack2026-tyu3o4` | Container Apps Environment | `rg-hack2026-shared` |
| `kv-hack2026-tyu3o4` | Key Vault | `rg-hack2026-shared` |
| `appi-hack2026-tyu3o4` | Application Insights | `rg-hack2026-shared` |
| `law-hack2026-tyu3o4` | Log Analytics Workspace | `rg-hack2026-shared` |
| `sthack2026tyu3o4` | Storage account | `rg-hack2026-shared` |
| `hack2026-budget` | Consumption Budget（¥180/月） | sub-scope |
| `nodelete-shared` | CanNotDelete lock | `rg-hack2026-shared` |
| `deny-storage-public` | Policy assignment（DoNotEnforce） | sub-scope |
| `rg-hack2026-dev` | Resource group |（空 — 今後 Container Apps を入れる） |
| `rg-hack2026-prod` | Resource group |（空 — 提出時用） |
| `aoai-hack2026` | Azure OpenAI account（S0、custom-domain、System-assigned MI） | `rg-hack2026-shared` |
| `aoai-hack2026/gpt-4o-mini` | AOAI deployment（gpt-4o-mini 2024-07-18、GlobalStandard、cap=50） | `rg-hack2026-shared` |

`tyu3o4` サフィックスは `shared.bicep:7` の `substring(uniqueString(resourceGroup().id), 0, 6)` から来る決定論的 ID。RG ごとに同じものが出てくる。

## 今週の次アクション（2026-W20, 2026-05-11 → 2026-05-17）

Track A — Spec 固め（オペレータ）:

1. ✅ idea-f 作成 + Kiro spec init 完了（2026-05-12）
2. ⏳ **Azure Foundry Agent Service リサーチ**（background 中、本日完了見込）→ `research/azure-agent-platform-decision.md`
3. ⏳ **チームへの spec 提示 → 合意**（5/14 セッション or 事前 async）
4. ⏸️ **`/kiro:spec-requirements` EARS 化** — チーム合意後に実行

Track B — 5/14 エントリーセッション準備（オペレータ）:

1. M7 参加（12:30–14:30）+ グレーゾーン質問リスト準備
2. 対象セクター×ユニット 1-2 マスの確定議論（候補は `research/sector-unit-candidates.md`）
3. spec design ベースライン（GraphCheck / Kunumi / 5-step ヒアリング）のチーム共有

Track C — 並行（オペレータ）:

- A1 Zenn エントリーフォーム登録 — 5/14 セッション後の URL 受領待ち
- 残リサーチ TODO（PKAI 本文精読 / エンタープライズ製品調査）は design フェーズ前

## 旧 今週の次アクション（2026-W18, 2026-04-27 → 2026-05-03、参考保持）

Track A — インフラ（オペレータ）:

1. ~~**Phase 0 / Phase 1 / Phase 2** インフラデプロイ。~~ ✅ 2026-04-29 完了。M4 完了。「完了したこと」セクションとデプロイ済リソース表を参照
2. **Bicep 修正 2 件を commit + push**（`shared.bicep:19` purge protection、`rbac.bicep` ownerAssignment 削除）— チームのリポジトリチェックアウトを実デプロイ済みの状態に揃える。差分は scaffold で uncommitted のまま
3. **`bootstrap-verify.ps1`** — M4 終端の正式検証（RG 数、deployment 状態、App Insights 接続文字列の export）。任意だが正式サインオフ用に 1 回実行する価値あり
4. **`setup-gitops.ps1`** — App Reg + federated credentials + gh variables/secrets。今後のインフラ変更で CI が OIDC 経由で `az login` できるように。今週は任意。M5 以降で gated deploy が必要になるまで延期可

Track B — アイデア出し（チーム並行）:

- メンバー 2 & 3: ideation-workbook.md _(pre-kickoff, archived off-repo)_ を読み、オペレータの「PPT Polish Agent」ドラフトに対するガットチェックを提供。Steps 1–2 への入力がまだ無い
- オペレータ: kickoff-meeting-agenda.md _(pre-kickoff, archived off-repo)_ を使ってキックオフをスケジュール — 2026-05-10（M6 freeze）以前を目標

Track C — 管理（オペレータ）:

- **チームメンバーの招待受諾** — M2/M3 とも `PendingAcceptance`（Microsoft からメール送信済、クリック待ち）。受諾するまで `az login` 不可。RBAC とリソースは既にセットアップ済 — クリックだけがゲート。30 分経ってもメールが来なければ迷惑メール確認（送信元: `invites@microsoft.com`）
- ~~**Discord ユーザー ID 収集**~~ ✅ 解決済 — 3 名とも `Hackathon Team` ロール付与済
- **A1** Zenn エントリーフォーム登録（法人名義、法人部門） — 成果物提出フォーム URL + 5/14 entry-session 案内が届く。iPad 可。[HANDOFF.md §A](./HANDOFF.md)
- **A2** Zenn org ハンドル `ai-club`（または代替）の確保
- **A3** 社内確認のフォローアップ（4 件未確定: 表記 / 登壇 / IP / 利益相反）
- **D2–D4** Discord サーバー構築の残タスク per [discord-bot/docs/server-setup-execution-guide.md](../../../../discord-bot/docs/server-setup-execution-guide.md)（D1 ロール付与は完了済）

## ブロック中 / 待ち

- ~~**チームメンバーの MS UPN**~~ ✅ 2026-04-29 解決。両 UPN 収集済、招待送信済、ゲストユーザーオブジェクトはテナントに存在（ただし 2026-05-05 に member-a 分は outlook.jp → outlook.com で再招待・OID 変更）
- **チームメンバーの招待受諾** — 純粋に「招待 URL を踏む」待ち。オペレータ作業はブロックしないが、teammate の `az login` はブロック。**member-a は 2026-05-05 の再招待 URL を手渡し配布済み、踏むのを待ち**
- ~~**PR #22 マージ + Bicep 再 deploy**~~ ✅ 2026-05-11 完了。PR #22 を squash-merge（`03a0c5b`）、`az deployment sub create --name hack2026-member-a-oid-20260511-1844` が 1m47s で成功。新 member-a OID `20f478f8-...` に対し RBAC 4 件 stamping 済（dev RG Contributor / shared RG Contributor + KV Secrets Officer + Storage Blob Data Contributor）を `az role assignment list` で確認
- ~~**phantom OID `36fc9993-...` の orphan RBAC 4 件削除**~~ ✅ 2026-05-11 完了。`az role assignment delete --ids` は `MissingSubscription` で失敗するため `az rest --method DELETE` で直接呼出。shared RG は `nodelete-shared` lock で `ScopeLocked` ブロックされたため、一時的に `az lock delete` → 30s 伝播待ち → 3 件削除 → `az lock create` で再適用。dev RG の 1 件はロック対象外なので即削除。合計 4 件削除済、新 member-a OID `20f478f8-...` の RBAC 4 件は無傷を再確認
- ~~**テーマ確定**~~ ✅ 2026-05-11 解決。idea-f（dialogue-monitoring 方式 暗黙知形式化）採択。詳細は [problem-statement.md](./problem-statement.md) / [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/)
- ~~**D7（AOAI リージョン）** — `swedencentral` がデフォルトだが gpt-4o-mini + gpt-4o + text-embedding-3-small の availability 未確認。M5（2026-05-05）前に確認。~~ ✅ **2026-04-28 確定** via `az cognitiveservices model list --location swedencentral`。3 モデルすべて存在。注意点: このリージョンの `text-embedding-3-small` は `GlobalStandard`/`DataZoneStandard` SKU のみ — `azure-setup.md` §6.1 を `--sku-name Standard` → `--sku-name GlobalStandard` にパッチ。容量クォータ（`--sku-capacity 50`）は未確認 — 初回デプロイ失敗時にポータルからリクエスト（24h リードタイム）
- **社内確認 #2–#5** — 法人 マーケ部門が確認中。開発はブロックしないが、提出時の表記 / 登壇 / IP の選択肢に影響

## オープンクエスチョン（Top 5; 全リストは [dev-prep.md §9](./dev-prep.md) §12）

1. `swedencentral` での AOAI クォータ `--sku-capacity 50`（モデル別） — リージョン availability ✅ 2026-04-28 確認済だが、アカウント別クォータがデフォルトで低い可能性あり。リクエストリードタイム 24h。初回デプロイで 429 / `InsufficientCapacity` が出たらポータル申請。`gpt-4o` Standard tier で発生しやすい想定
2. `hello_agent.py` の Managed Identity auth フォールバックは今すぐ入れる？それともテーマ確定 + 実エージェント着手まで待つ？（pre-push レビューの S2）
3. デモ後（6/1 以降）、Zenn ショーケース用にリポジトリを public 化する？する場合は branch-protection ルールセットが無料化
4. ~~メンバー 3 名全員が 2026-05-04（M4）までに Microsoft + GitHub アカウントを準備できる？~~ ✅ 解決済（M4 done 2026-04-29、member-a 5/11 で再招待後 RBAC stamping 済）
5. PAYG vs let-expire: MVP 統合が 2026-05-26 までに終われば、PAYG 変換をスキップして Free Trial を expire させる？（カード課金 ~$10 を節約）

## 直近の意思決定

- 2026-04-28: branch protection を意図的にスキップ（free-tier private repo は classic + rulesets API がブロックされる）。社内norm + 助言的 CI で代替。デモ後にリポジトリが public 化するなら見直し
- 2026-04-28: リポジトリ名は `aiclub-labs/zenn-hack2026` に決定（`hack2026` は汎用すぎとして却下）
- 2026-04-28: AI-club Microsoft アカウント = ユーザーの個人 Gmail を MSA 化したもの（意図的: Azure-virgin 要件を満たす。fresh aiclub email を作る必要なし）。同日いったん再検討 — AI-club Gmail で新規 MSA を試したが Microsoft が新 MSA への $200 クレジットを拒否（原因不明）。元の personal-Gmail MSA プランに戻し、Free Trial sub + $200 クレジットを保持
- 2026-04-29: **チームメンバーの sub-scope Contributor をスキップ**、RG-scope のみで運用（オペレータの「自分のみ admin auth」の意向）。Phase0 の sub-RBAC ステップは M2/M3 で no-op、`rbac.bicep` がより厳しい RG-scope のアサインを適用。結果: teammate は `rg-hack2026-dev` + `rg-hack2026-shared` の Contributor（shared には `CanNotDelete` lock があり誤削除をブロック）、sub scope の権限はゼロ。オペレータが sub-scope Owner を単独保持
- 2026-04-29: **Bicep プラットフォーム側修正 #1 — Key Vault `enablePurgeProtection`。** Azure が新 Key Vault に対する明示的な `enablePurgeProtection: false` を拒否するようになった（プラットフォーム側のバリデーション強化、ドキュメント上の発効日不明だが本日観測）。`infra/modules/shared.bicep:19` を `false` → `true` に変更。含意: KV は `az keyvault delete` 後 7 日間ハード削除不可（`softDeleteRetentionInDays: 7` と一致）。6/2 teardown では KV 名が ~2026-06-09 まで予約。ハッカソン範囲では許容（同名再デプロイしない）
- 2026-04-29: **Bicep プラットフォーム側修正 #2 — `rbac.bicep` の ownerAssignment 削除。** Bicep が `ownerObjectId` 用に決定論的 GUID で sub scope の Owner role assignment を打っていたが、サブスクリプション作成時に Azure が自動で作る Owner assignment（ランダム GUID `fdba5b6c-...`）と衝突。ARM は `(principal, role, scope)` の重複を `RoleAssignmentExists` で拒否。冗長ブロックを削除。`ownerObjectId` パラメータは documentation / 将来の再designation 用に保持されているが、もうリソースを駆動しない。signup 時の Owner assignment は sub のライフ中安定
- 2026-04-29: **`azd provision` ではなく `az deployment sub create` でデプロイ。** `azd` は `azd auth login`（`az login` とは別の認証状態）が必要。`az deployment sub create` を直接使うことで二重ログインを回避しつつ同じ Bicep テンプレートを適用。今後どちらでも OK だが、ドキュメント上の `azd provision` 参照は有効、`az` ルートが検証済パスとして documented
- 2026-05-05: **`parameters.json` drift PR #21 マージ。** scaffold/infra のテンプレートと `hack2026-init-3` 実デプロイの差分（実 OID、owner、budget email、policy.bicep の post-M4 TODO コメント）が main に landing。詳細は merge commit `e688f89`。
- 2026-05-05: **ROADMAP critical/high 修正コミット `ada3305`。** 4件の重大な timing 問題を修正: (1) M13 Teardown を 2026-06-02 固定 → 6/10〜 conditional に変更（審査期間 6/2〜6/9 中の URL 死亡を防ぐ）、(2) M11 を 5/31 → 5/30 に前倒しして M11.5 を予備日として 5/31 に追加（提出 24h バッファ → 48h バッファ）、(3) M5 を分割（M5a 5/5 = gpt-4o-mini のみ / M5b 5/11 = gpt-4o + text-embedding-3-small を M6 後に追加）、(4) M10 PAYG 移行を 5/26 → 5/28 に後倒し（M9 から 3 日バッファ）。残る medium/low 修正（M3 状態更新、M9 ← M3 依存、RACI 表記、キックオフ M5.5）は別コミット予定。
- 2026-05-05: **member-a の MS account 訂正 — outlook.jp → outlook.com。** 旧アドレスで送った招待が誤りだったため、(a) 旧ゲストオブジェクト `6176c325-a817-41f4-b571-f9955fac050d` を `az ad user delete` で削除（cascade で RBAC も消滅）、(b) outlook.com で再招待、新 OID `20f478f8-3337-4895-bf25-2fdb9f41c7c5` を取得（PendingAcceptance）、(c) 招待 URL は member-a へ手渡しで配布（このテナントは招待メールが届かない既知問題、2 度確認済）。新 OID への RBAC 再 stamping は PR #22（`infra/member-a-oid-correction`）マージ後の `az deployment sub create` 再実行で行う。
- 2026-05-05: **`parameters.json` の member-a 用 slot OID `36fc9993-3996-4749-b72e-cd8ebea41844` は phantom 判明。** `az ad user show --id` がエラー (`Resource ... does not exist`) を返すが、dev RG / shared RG には対応する RBAC が 4 件 stamping 済（Contributor / Storage Blob Data Contributor / KV Secrets Officer / Contributor）。デプロイ時には実在したものの後で削除されたか、当初から間違って入っていた可能性。PR #22 で parameters から除外、orphaned な 4 件の role assignment 削除は別 PR で `az role assignment delete` 手動実行予定。
- 2026-05-05: **bootstrap-phase0.ps1 修正（PR #22 同梱）。** `az rest` で発行した招待 API レスポンスを `Out-Null` で破棄していたが、本テナントは招待メール配信が不安定なため、`inviteRedeemUrl` / OID / UPN を `Write-Host` で出力するよう変更。今後の招待操作で URL の手渡し配布が確実にできるようになる。
- 2026-05-11: **PR #22 マージ + Bicep 再デプロイ完了。** `gh pr merge 22 --squash --delete-branch` でマージ（`03a0c5b`、CI clean）、origin/main の `parameters.json` を `/tmp/main.parameters.json` 経由で `az deployment sub create` に渡してデプロイ実行（scaffold は feature branch + uncommitted のままなのでブランチ切替を避けた）。what-if 結果: 新 RBAC 4 件 Create + Azure 側メタプロパティ補完 13 件 Modify（破壊的でない idempotent-redeploy noise）。デプロイ名 `hack2026-member-a-oid-20260511-1844`、1m47s で Succeeded。
- 2026-05-11: **M5a — AOAI gpt-4o-mini プロビジョン完了。** `aoai-hack2026` (S0, swedencentral, custom-domain, system-assigned MI) を `rg-hack2026-shared` に作成、deployment `gpt-4o-mini` (model 2024-07-18, cap=50) をデプロイ、API key + endpoint を `kv-hack2026-tyu3o4` に格納（secret 名 `AZURE-OPENAI-API-KEY` / `AZURE-OPENAI-ENDPOINT`）。**重要な発見:** SKU `Standard` (regional) は `ServiceModelDeprecated` (cutoff 2026-03-31) で新規デプロイを拒否されたため `GlobalStandard` に切替。`az cognitiveservices model list` は同モデルを GA (inference deprecation 2026-10-01) と返すが、deployment endpoint 側のバリデーションは別レイヤで先行して deprecation を効かせている模様。`scripts/aoai-provision.{ps1,sh}` の gpt-4o-mini / gpt-4o SKU を全て `GlobalStandard` に修正済（uncommitted。M5b で gpt-4o + text-embedding-3-small を追加デプロイする際の事故防止のため）。
- 2026-05-11: **phantom OID `36fc9993-...` の orphan RBAC 4 件を削除。** Graph に存在しない principalId なので `az role assignment delete --assignee` も `--ids` も `MissingSubscription` で失敗 → `az rest --method DELETE` を直接呼出する形に切替。shared RG の 3 件は `nodelete-shared` (CanNotDelete) lock で `ScopeLocked` ブロックされたため、`az lock delete` → 30s 伝播待ち → 3 件削除 → `az lock create` でロック再適用、という手順で対応。dev RG の 1 件はロック対象外なので即削除。新 member-a OID の RBAC 4 件は無傷を再確認。教訓: ロック付き RG への role assignment 直接 DELETE は、ARM 側で「lock scope と一致する scope への DELETE」と判定されてブロックされる（role assignment 自体は単なる metadata だが、lock の semantic は scope subtree 全体に効く）。再適用時に notes の em-dash が PowerShell-az の encoding でハイフンに化けたが cosmetic で、次回 Bicep deploy で自動修復される。
