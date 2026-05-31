# チームメンバー オンボーディング — Microsoft Agent Hackathon 2026

> AI Club ハッカソンチームへようこそ。このドキュメントは Azure / GitHub / Discord 上で開発を始められる状態にするためのチェックリストです。今日 5 分（情報収集）+ 後日 30 分（ツール導入と初回サインイン）が必要です。
>
> オペレータ（= 連絡先・セットアップ窓口）: [STATUS.md](./STATUS.md) を参照。
>
> 提出締切: **2026-06-01 23:59**。テーマ確定: **2026-05-11 ✅**（暗黙知形式化 dialogue-monitoring 方式 / idea-f）。タイムライン全体は [ROADMAP.md](./ROADMAP.md) を参照。

---

## ステップ 1 — オペレータに 3 つの情報を送る (5 分)

以下 3 つを返信してください。これがあれば、あなたのアカウントの紐付けはすべて行えます。

### 1.1 Microsoft アカウントメール（UPN）

Microsoft の各種サービスにサインインするときに使うメールアドレスです。

✅ OK:
- 既存の **outlook.com / hotmail.com** アドレス
- すでに MSA 化されている **個人 Gmail**（Microsoft 365 / Xbox / OneDrive personal にサインインしたことがあるもの）
- その他、Microsoft アカウントを持っている任意のメール

❌ NG:
- **法人 コーポレートメール**（`*@jp.__法人COM__` など） — 法人 テナントとハッカソン作業が混ざるため、法人部門エントリでは明示的に避けています。個人アイデンティティを使ってください。

持っていない・分からない場合 → `https://signup.live.com` で無料の outlook.com を新規作成（3 分）。クレジットカード不要。

**自分で Azure アカウントを作る必要はありません。** $200 クレジットの付いた Azure サブスクリプションはオペレータが所有します。あなたの Microsoft アカウントはオペレータの Entra テナントに **ゲスト** として招待されるだけで、課金関係を持たずにハッカソンリソースの Contributor 権限を得られます。

### 1.2 GitHub ユーザー名

`github.com` のハンドル名。既存の個人アカウントで構いません。

持っていない場合 → `https://github.com/signup` でサインアップ（3 分）。Settings → Password and authentication からすぐに 2FA を有効化してください。

**注意:** push したコミットはこのハンドル名で公開されます。個人 GitHub と切り離したい場合は、専用ハンドル（例 `<yourname>-aiclub`）を作成しても OK（任意）。

### 1.3 Discord ユーザー ID

Discord 上で個人を一意に識別する 18 桁の数字です。ユーザー名とは別物。

取得方法:
1. Discord を開く（デスクトップアプリ推奨。モバイルでも可）
2. **設定 → 詳細設定 → 「開発者モード」を ON**
3. 自分のユーザー名（サーバーリスト・自分のメッセージ等）を右クリック → **「ユーザー ID をコピー」**
4. 貼り付け — `123456789012345678` のような 18 桁の数字

これにより、AI Club Discord サーバーで **Hackathon Team** ロールが付与され、`🏆 Hackathon: MS Agent 2026` カテゴリとチャンネルが見えるようになります。

### 任意（あれば便利）

- SMS-based MFA バックアップ用の電話番号（Authenticator アプリ単体に頼りたくない場合）
- 役割の希望: `agent code`（Python + SK + MCP） / `UI + demo`（Streamlit + 動画） / `blog + submission`（Zenn 記事 + GitHub README）

---

## ステップ 2 — 招待を受け取る（オペレータ作業; ~30 分）

オペレータが 3 つの情報を受け取った後、以下を実行します:

1. あなたの Microsoft アカウントを Azure Entra テナントにゲストとして招待（"You're invited!" というメールが Microsoft Invitations から届く）
2. あなたの GitHub ユーザー名を `github.com/aiclub-labs/zenn-hack2026` に `push` collaborator として追加（GitHub からメールが届く）
3. あなたの Discord ユーザーに `Hackathon Team` ロールを付与（無音; 開いた瞬間に新チャンネルが見えるようになる）

**3 つの招待を受諾してください:**
- Azure: メールリンク → サインイン → 「Accept」でゲスト招待を承認。「新しい組織にアカウントを接続します」のプロンプトが出ますが想定通りです。
- GitHub: メールリンク → "Accept invitation"
- Discord: 受諾操作は不要 — AI Club サーバーを開いて `#hack-chat`、`#hack-dev-log`、`#hack-submission` が見えれば OK

---

## ステップ 3 — ローカルツール導入 (~20 分; コード作業を始めるとき)

実際にエージェントコード作業を始める（5/10 のテーマ確定後）まで、これは必須ではありません。早めに準備しても OK。

### Windows (PowerShell 7+ 推奨; `az`/`azd` には Git Bash を避ける)

```powershell
winget install -e --id Microsoft.AzureCLI
winget install -e --id Microsoft.Azd
winget install -e --id GitHub.cli
winget install -e --id jqlang.jq
winget install -e --id Python.Python.3.11
winget install -e --id Git.Git
az bicep install
```

ターミナルを再起動して確認:
```powershell
az version; azd version; gh --version; jq --version; python --version; git --version
```

### macOS

```bash
brew install azure-cli azd gh jq python@3.11 git bicep
```

### WSL Ubuntu / Linux

```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
curl -fsSL https://aka.ms/install-azd.sh | bash
sudo apt install -y jq gh python3.11 git
az bicep install
```

### 任意: VS Code 拡張

- Python (`ms-python.python`)
- Pylance (`ms-python.vscode-pylance`)
- Bicep (`ms-azuretools.vscode-bicep`)
- Azure Container Apps (`ms-azuretools.vscode-azurecontainerapps`)
- GitHub Pull Requests (`github.vscode-pull-request-github`)

リポジトリには `.devcontainer/` も含まれているため、VS Code + Dev Containers 拡張で「Reopen in Container」を選ぶと Python 3.11 + 全 CLI 環境が事前構成済みで立ち上がります。

---

## ステップ 4 — 初回サインイン + clone (~5 分)

招待を受諾しツールを導入し終えたら:

```powershell
# <TENANT_ID> はオペレータから受け取る値（a4597d14-... のような形）に置き換える
az login --tenant <TENANT_ID>

# ハッカソンサブスクリプションが見えることを確認
az account list --query "[?tenantId=='<TENANT_ID>'].{name:name,id:id,state:state}" -o table
# 期待: hack2026, Enabled

az account set --subscription hack2026
az account show --query "{name:name,user:user.name}" -o table
# 期待: name=hack2026, user=<your-MSA-email>
```

```powershell
# リポジトリを clone（あなた自身の GitHub 認証を使用）
gh auth login           # 一度きりの設定; GitHub.com → HTTPS → web browser を選択
git clone https://github.com/aiclub-labs/zenn-hack2026.git
cd zenn-hack2026

# Python 依存をインストール
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # macOS/Linux なら `source .venv/bin/activate`
pip install -e ".[dev]"

# Python アプリがローカルで起動することを確認（Azure 不要）
uvicorn app.main:app --reload
# http://localhost:8000/health → {"status":"ok"} が返ればOK
```

いずれかで失敗したら、Discord の `#hack-dev-log` に `infra` タグでエラーを貼ってください。

---

## ステップ 5 — 3 つのドキュメントを読む (15 分)

コードに貢献する前に、以下を読んでプロジェクトの把握をしてください:

| ドキュメント | 学べること | 読むタイミング |
|---|---|---|
| [STATUS.md](./STATUS.md) | 完了したこと・ブロック中のこと・今週のアサイン | 今 (5 分) |
| [ROADMAP.md](./ROADMAP.md) | 全マイルストーンと日付、自分の RACI | 今 (3 分) |
| [problem-statement.md](./problem-statement.md) | 採択テーマの As-Is / To-Be / Gap | 今 (5 分) |
| [architecture-cards/idea-f-dialogue-monitoring.md](./architecture-cards/idea-f-dialogue-monitoring.md) | 採択アーキテクチャの構成と工数（wall-clock + human review） | 今週中 (10 分) |

より深い文脈が知りたい場合: [INDEX.md](./INDEX.md) がナビゲーションのエントリーポイントです。

---

## ステップ 6 — デイリーワークフロー

### コード変更は PR を経由する

ブランチ保護は GitHub 側では強制されていません（free-tier private repo の制約）が、チームの方針として:

```bash
git checkout -b feat/<short-name>      # または fix/, infra/, ui/, docs/
# ... ファイルを編集 ...
git add .
git commit -m "<scope>: <change in present tense>"
git push -u origin feat/<short-name>
gh pr create --fill                    # PR を開く; CI がバックグラウンドで走る
# CI が緑になったら、レビューは任意・推奨
gh pr merge --squash --delete-branch
```

**`main` への直接 push は禁止です。** 技術的にはできてしまいますが、チームの相互可視性を壊すのでやめてください。

### CI 失敗はマージブロックではないが直すべき

`ci.yml` は PR ごとに `ruff`（lint）+ `pytest`（tests）を実行します。赤の CI でもマージはできますが、チーム方針は「マージ前に CI を直す」です。詰まったら `#hack-dev-log` に `infra` タグで質問してください。

### 質問はどこに書くか

| 質問の種類 | チャンネル |
|---|---|
| 「X で詰まった」 / 「Y はどう動く?」 | `#hack-dev-log`（Discord forum, タグ `wip`） |
| リアルタイムのペアリング・デバッグ | `#hack-voice` (voice) |
| テーマ・スコープの判断 | `#hack-chat` テキスト — 合意が必要 |
| 提出物・ブログ・動画 | `#hack-submission` テキスト |
| 議事録ダイジェスト (Bot 自動投稿) | `#hack-meetings` |
| 緊急 | オペレータに DM |

### Bot 経由で Azure / GitHub を操作 (`/connect`)

Discord から `/az status` `/gh status` `/gh pr-merge` `/az lock-*` `/deploy` を使うには、**各メンバーが自分の Azure / GitHub アカウントを Bot に紐付け**する必要があります。Bot は per-user で device code フローのトークンを保持するので、誰が何をしたかは Azure Activity Log と GitHub Audit Log で個別に追跡されます（オペレータの権限は流用されません）。

初回のみ、各自 1 回だけ実行してください:

1. **`/connect azure`** を任意のチャンネルで実行
   - Bot が DM に device code (例 `ABCD-1234`) と URL を返す
   - ブラウザで `https://microsoft.com/devicelogin` を開き、コードを入力 → Microsoft アカウントでサインイン（ステップ 1 で送った UPN）
   - Bot DM に「✅ connected as `<your-MSA>`」が出れば完了
2. **`/connect github`** を実行
   - 同じく DM に device code + `https://github.com/login/device` の URL
   - ブラウザで承認 → 「✅ connected as `<your-gh-username>`」

確認:
- `/az status` → AOAI deployments / RG / Lock 一覧が embed で返る
- `/gh status` → あなたの open PR + Actions の直近実行が embed で返る

**トークンの寿命:**
- Azure: 90 日（24h 以内に何か実行すれば自動延長）
- GitHub: 30 日

期限切れすると `/az` `/gh` `/deploy` が「未接続」エラーを返すので、その時に `/connect` を再実行してください。

### ミーティング録音 (`/recap`) — Bot で自動議事録

`#hack-voice` で会議をするとき、AI Club Bot が録音 → 文字起こし → 議事録を自動生成してくれます。

1. 全員 `#hack-voice` に入室
2. 誰か一人がテキストチャンネル (例 `#hack-chat`) で **`/recap start`** を実行
   - Bot がボイスチャンネルに参加し、各自の音声を per-user で録音開始
3. ミーティング終了時に **`/recap stop`** を実行
4. 約 20–40 秒後に:
   - インタラクション返信に **commit URL** (議事録の Markdown ファイル)
   - **`#hack-meetings`** にダイジェスト投稿（決定事項 + アクション項目のみ）
   - `aiclub-labs/zenn-hack2026:docs/meetings/YYYY-MM-DD.md` に構造化議事録（概要 / 決定事項 / アクション項目 / 議論された論点 / オープン論点 / 参加者）

**注意点:**
- 1ギルドにつき同時 1 セッションまで（誰かが先に start していると弾かれる）
- 同じ日に複数回 stop すると `YYYY-MM-DD.md` は **上書きコミット** になる
- `/recap status` で現在のセッション状況を確認できる
- 録音は OpenAI Whisper に送られます。機密情報は喋らないでください
- 詳細仕様: [discord-bot/docs/meeting-recap.md](../../../../discord-bot/docs/meeting-recap.md)

### 非同期スタンドアップ

各メンバーは作業を始めたタイミング（または毎日）で、`#hack-chat` に短い投稿をしてください:
- 前回以降にやったこと
- 次に着手すること
- ブロックされていること（あれば）

定例ミーティングは無し — 可視性は非同期で保ちます。

---

## ステップ 7 — 境界線 (やってはいけないこと)

- ❌ オペレータの `aiclub-labs` GitHub 認証情報を流用しない（あなたには別途 collaborator アクセスがあります）
- ❌ 法人 コーポレートアイデンティティで `az login` しない。常にオペレータが招待した個人 MSA を使用
- ❌ `az group delete` / `azd down` を実行しない — teardown はオペレータ（Subscription Owner）のみ。あなたは dev RG の Contributor 権限を持っているため `rg-hack2026-dev` 内のリソースの作成・変更・削除は可能ですが、RG 自体や shared リソースは触れません
- ❌ `.env` ファイル、AOAI キー、その他シークレットを commit しない。`.gitignore` で除外済みですが、commit 前に必ず確認
- ❌ デモ前（2026-06-01）まで GitHub リポジトリ URL をチーム外に共有しない。デモ後にショーケース用に公開予定
- ❌ **¥180 予算を流出させない**。オペレータが監視していますが、重い AOAI 呼び出しを走らせる人は `#hack-chat` で告知してください（例: 「今日 1000 token 重めのテストコール、~$5 想定」）。誤って暴走させた場合は即座に止めてオペレータに通知

---

## ステップ 8 — カレンダーリマインダー設定

| 日付 | イベント |
|---|---|
| ~~2026-04-30~~ | ~~モックスタイルガイド確定~~ — idea-f 採択により対象外 |
| ~~2026-05-10~~ | ~~テーマ確定締切~~ → ✅ 2026-05-11 idea-f 採択 |
| **2026-05-14** | 任意: Microsoft エントリーセッション 12:30–14:30 — オペレータ（代表）参加 |
| **2026-05-22** | バーンレートチェック（オペレータ実施。プロンプト圧縮を依頼される可能性あり） |
| **2026-05-31** | デモ録画 + Zenn 記事 + GitHub README 完成（メンバー 2 担当） |
| **2026-06-01 23:59** | **提出締切**（オペレータが提出フォームから提出） |
| **2026-06-10** | 結果通知 |
| **2026-06-18** | 最終審査・表彰式（通過した場合） |

---

## クイック FAQ

**Q: 自分の $200 で自分の Azure アカウントを作るのではダメなの？**
A: チーム全体で 1 つの $200 クレジットプールを共有します。3 アカウント × $200 のほうが大きく見えますが、課金分離・RBAC の複雑さ・AOAI デプロイの共有ができないことを考えるとネガティブです。Free Trial サブはあとから統合できません。1 サブ・3 ゲストが標準パターンです。

**Q: 招待メールが届かない場合は？**
A: 迷惑メールを確認してください。Microsoft の招待メールは `invites@microsoft.com` から、GitHub のメールは `noreply@github.com` から来ます。30 分経っても届かない場合は `#hack-chat` でオペレータに連絡（再送可能）。

**Q: Claude Code / Codex / Cursor を開発に使っていい？**
A: はい — むしろそういう設計です。AI 開発ツールは開発時の協働ツールとしてのみ使用。ハッカソン提出物（提出ルール上 Microsoft AI のみで構成）には乗せません。

**Q: 法人 との利益相反が心配です**
A: オペレータが 法人 マーケ部門と確認済（社内確認 4 項目中 1 つ確定、3 つ進行中）。**法人部門 (法人 AI部)** として組織承諾あり。個人 MS アカウント・個人 PC・業務時間外 — この 3 条件を守ること。法人 コーポレートアイデンティティ・法人 リポジトリ・法人 クライアントデータを混ぜなければ、線の中にいます。

**Q: 想定される週あたり工数は？**
A: 2026-05-22 までは ~5–8 時間/週、その後 2026-05-23 → 2026-06-01 は 8–12 時間/週（最終統合・デモ準備・提出）。非同期前提。固定ミーティングは任意の 30 分週次同期くらい。

**Q: 抜けたい場合は？**
A: 早めのほうが良いです。テーマ確定（2026-05-11 ✅）後は 3 人スケールでスコープを切っているので、抜ける場合は即座にオペレータへ連絡してください — 再スコープが必要になります。

---

## 返信テンプレート

以下を埋めて Discord DM でオペレータに送ってください:

```
1. MS account UPN: __________
2. GitHub username: __________
3. Discord user ID: __________
（任意）MFA 用電話番号: __________
（任意）役割の希望: agent code / UI+demo / blog+submission
```

これだけです。受信後、オペレータが ~30 分でアクセスを構成し、すぐに開発を始められる状態になります。
