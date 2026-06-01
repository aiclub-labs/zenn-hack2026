# 統合セットアップ・ガイド — Discord ↔ GitHub ↔ Azure

**対象**: AI部 ハッカソン (Microsoft Agent Hackathon Japan 2026) の3名チーム
**目的**: Discord / GitHub / Azure / Claude Code を「Spec-driven 開発の幹」として接続するための、再現可能な実行手順
**前提リソース**:
- Discord guild: `1478407098521092198` (AI Club)
- GitHub repo: `aiclub-labs/zenn-hack2026` (private)
- Azure subscription: `hack2026` (`2c29a97c-08b6-4bc3-88ea-266eb1cfd730`, region `swedencentral`)
- ローカル: `discord-bot/` (TypeScript, Bun) / `events/microsoft-agent-hackathon-2026/scaffold/` (Bicep + Python)

**関連ドキュメント**:
- 全体計画: [./action-plan.md](./action-plan.md)
- 進捗: [./STATUS.md](./STATUS.md)
- ブラウザ作業: [./HANDOFF.md](./HANDOFF.md)
- Discord 設計根拠: [discord-bot/docs/dev-workflow-research.md](../../../../../discord-bot/docs/dev-workflow-research.md)
- Discord サーバー構築: [discord-bot/docs/server-setup-execution-guide.md](../../../../../discord-bot/docs/server-setup-execution-guide.md)

---

## 0. 設計原則（採用済み・shortcut しない）

研究 (`dev-workflow-research.md`) から確定した方針:

1. **GitHub = system of record / Discord = pre-flight room.** 重要な意思決定は GitHub PR / `.kiro/specs/` / `decisions/YYYY-Www.md` に書く。Discord 絵文字は批准の根拠にしない。
2. **GitHub→Discord webhook は3種類に絞る** (PR opened / review-requested / merged) — 「全イベント」は必ずノイズになる。本ガイドでは入門としてもう少し広めの 5 種類で開始 → 1週間ごとに dial down。
3. **AI レビューは GitHub PR 上で完結させ、Discord は通知だけ.** Anthropic 公式 GitHub App の `@claude` を主軸とする。Claude-Code-in-Discord (1スレッド = 1 Claude セッション) はハッカソン差別化候補として後続検討。

---

## 1. Discord ↔ GitHub Webhook

`#github-feed` チャンネルに GitHub のリポジトリイベントを流し込む。スクリプトは既に `discord-bot/scripts/create-github-webhook.ts` に landing 済み。

### 1.1 前提

- `discord-bot/.env` に `DISCORD_TOKEN` が入っていること
- Discord 側で `#github-feed` チャンネルが存在すること（[`server-setup-execution-guide.md`](../../../../discord-bot/docs/server-setup-execution-guide.md) Phase 2 で作成済み）
- 操作者が GitHub `aiclub-labs/zenn-hack2026` の Settings → Webhooks へアクセスできる admin 権限を持つこと

### 1.2 手順

```bash
cd discord-bot
npm run create-github-webhook
```

スクリプトの動作:

- guild の `#github-feed` を探す → 既存の `GitHub` という名前の webhook があれば再利用、無ければ作成
- URL の末尾に `/github` を自動付加（Discord が GitHub payload を解釈する形式）
- `discord-bot/.webhook-url` (chmod 600, gitignore 済み) に書き出し
- 標準出力にはマスキング済みの URL のみ。ログにフル URL を残さない

### 1.3 GitHub 側の設定

URL の取扱い:

```bash
# URL は .webhook-url の中身。チャットや Issue にコピペしない
cat discord-bot/.webhook-url
```

GitHub UI: `https://github.com/aiclub-labs/zenn-hack2026/settings/hooks/new`

| 項目 | 値 |
|------|------|
| Payload URL | `.webhook-url` の内容（`/github` 付きであることを目視確認） |
| Content type | `application/json` |
| Secret | **空欄**（決定: 2026-05-01 — 下記 §1.3.1 参照） |
| SSL verification | Enable |
| Which events? | **Let me select individual events** → Pushes / Pull requests / Issues / Issue comments / Releases |
| Active | ✅ |

#### 1.3.1 Secret を空欄にする理由

Discord の `/github` 受信エンドポイントは GitHub の HMAC 署名を **検証しない**。「URL を知っている = 投稿可能」という設計のため、GitHub 側の Secret は no-op。実際の機密境界は webhook URL そのもの (`.webhook-url`、chmod 600、gitignore 済み)。

漏洩した場合は `npm run rotate-github-webhook` で URL を再発行 → GitHub 側の Webhook URL を貼り直す。

将来カスタム receiver (HMAC 検証する独自 endpoint) を挟む構成に変える場合のみ Secret を設定する。

### 1.4 検証

GitHub 側で webhook を作成すると自動で `ping` が送信される。

- GitHub: `Recent Deliveries` タブ → 直近の delivery が **204 No Content** を返していること
- Discord: `#github-feed` に ping のテストペイロードが embed で表示されること

失敗時のチェック:

| エラー | 原因 | 対処 |
|--------|------|------|
| 401 | URL 末尾の `/github` 抜け | URL を再コピー |
| 404 | URL 自体が壊れている | webhook を Discord 側で削除 → スクリプト再実行 |
| 403 | bot が `Manage Webhooks` 権限を持っていない | `admin-tools-setup.md` 参照 |
| Discord 側に出ない / GitHub 側 200 | 別の webhook がペイロードを食ってる可能性 | Channel → Integrations → Webhooks で重複チェック |

### 1.5 ローテーション（漏洩時）

スクリプト `discord-bot/scripts/rotate-github-webhook.ts` が同梱。実行すると:

1. 既存の `GitHub` webhook を削除
2. 新しいものを作成、`/github` 付加、`.webhook-url` に上書き
3. GitHub 側 webhook の URL を貼り直すのは手作業

---

## 2. Anthropic Claude GitHub App

PR 上で `@claude` を呼び出して in-context レビュー / 質問応答を回すための公式 App。**Discord-Claude-bridge より優先度高**（成熟度 🟢、商用バックアップあり）。

### 2.1 インストール

**重要 (2026-05-01 検証時の発見)**: 現行版の Claude GitHub App は **2 段構え**:

1. App をリポジトリにインストール（OAuth）
2. `.github/workflows/claude.yml` をコミット（`anthropics/claude-code-action@beta` を呼び出すワークフロー）

ブラウザだけで進めると **Step 1 のみ完了** し、`@claude` メンションは受信されるが応答が出ない。両方を一気にやる方法は **Claude Code セッション内で `/install-github-app` を実行** すること — このコマンドは App インストールとワークフロー追加 PR を併せて実施する。

```
/install-github-app
```

ブラウザに飛ぶ → org `aiclub-labs` を選択 → リポジトリは `Only select repositories` → `zenn-hack2026` のみ選ぶ → Install。完了後、Claude Code が `Add Claude workflow` PR を自動で作成 → review → merge。

App だけ既にインストール済みなら、ワークフロー部分のみ後付けする方法は §2.1.1 を参照。

### 2.1.1 ワークフロー後付け（既に App インストール済の場合）

`.github/workflows/claude.yml` を作成:

```yaml
name: Claude Code Review
on:
  issue_comment:
    types: [created]
  pull_request_review_comment:
    types: [created]
  issues:
    types: [opened]
  pull_request:
    types: [opened]
jobs:
  claude:
    if: contains(github.event.comment.body, '@claude') || contains(github.event.issue.body, '@claude') || contains(github.event.pull_request.body, '@claude')
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
      issues: write
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: anthropics/claude-code-action@beta
        with:
          use_oauth: true   # App OAuth を使う場合 (Claude Code Pro/Max bind)
          # または anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

**認証モードの選択**:
- `use_oauth: true` — Claude Code Pro/Max 加入者向け。App インストール時に紐付けた Anthropic アカウントの quota を消費。secret 不要
- `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` — Anthropic API key 直接指定。Pro/Max 不要だが API 課金発生。`gh secret set ANTHROPIC_API_KEY` で投入

ハッカソン用途では `use_oauth: true` 推奨（オペレータの Claude Code Pro 加入を流用、追加課金なし）。

### 2.2 検証

リポジトリで dummy PR を 1 件立てる:

```bash
git switch -c test/claude-app-smoke
echo "smoke" >> README.md
git commit -am "chore: smoke test for Claude GitHub App"
git push -u origin test/claude-app-smoke
gh pr create --title "smoke: Claude App" --body "@claude please summarize this diff"
```

数十秒以内に Claude bot が PR にコメント返答すれば成功。

### 2.3 利用パターン (チームで合意)

- `@claude review` — 差分レビュー (人間 reviewer の前段)
- `@claude explain <function>` — 既存コードの解説
- `@claude` 単体メンション — 自由質問 (`how would you refactor this?` 等)

**やってはいけない:**

- `#general` 等の雑談チャンネルに Claude レビュー出力を流す（`dev-workflow-research.md` §5）
- `@claude` の出力を意思決定の根拠として PR description に貼り付けて merge — レビューはあくまで **advisory**、CODEOWNERS / 人間 SME approval が硬いゲート

---

## 3. GitHub → Azure (OIDC, 任意 / M5 以降)

**優先度低**: 現在の Bicep デプロイはオペレータの local `az` セッション経由。CI からの自動デプロイが必要になるまで実装を遅延可（`HANDOFF.md` C4）。実装は demo 後に push 化検討する場合に必要。

### 3.1 アーキテクチャ

```
GitHub Actions (workflow_run)
  └── azure/login@v2 (federated credential 経由)
        └── App Registration: github-actions-hack2026
              └── Federated Credential
                    repo:aiclub-labs/zenn-hack2026:ref:refs/heads/main
                    repo:aiclub-labs/zenn-hack2026:pull_request
              └── RBAC: Contributor on rg-hack2026-dev / rg-hack2026-prod
```

- アクセスキー / client secret は使わない（OIDC で短命トークン）
- Azure 側 entitlement は **RG scope のみ** (sub scope を渡さない — オペレータ自身の Owner と分離)

### 3.2 実装スクリプト（未着手）

`scaffold/scripts/setup-gitops.ps1` に landing 予定。手順:

```powershell
# 1. App Registration
$app = az ad app create --display-name "github-actions-hack2026" --query appId -o tsv
$sp  = az ad sp create --id $app --query id -o tsv

# 2. Federated credential (main + PR)
az ad app federated-credential create --id $app --parameters '@scaffold/infra/oidc/main.json'
az ad app federated-credential create --id $app --parameters '@scaffold/infra/oidc/pr.json'

# 3. RBAC: Contributor on dev RG only (prod は手動 promote)
az role assignment create --assignee $sp `
  --role Contributor `
  --scope "/subscriptions/2c29a97c-08b6-4bc3-88ea-266eb1cfd730/resourceGroups/rg-hack2026-dev"

# 4. GitHub variables/secrets
gh secret  set AZURE_CLIENT_ID       --body $app
gh variable set AZURE_TENANT_ID       --body (az account show --query tenantId -o tsv)
gh variable set AZURE_SUBSCRIPTION_ID --body "2c29a97c-08b6-4bc3-88ea-266eb1cfd730"
```

### 3.3 federated-credential JSON 例

`scaffold/infra/oidc/main.json`:

```json
{
  "name": "main-branch",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:aiclub-labs/zenn-hack2026:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}
```

`scaffold/infra/oidc/pr.json`:

```json
{
  "name": "pull-request",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:aiclub-labs/zenn-hack2026:pull_request",
  "audiences": ["api://AzureADTokenExchange"]
}
```

### 3.4 GitHub Actions ワークフロー雛形

`.github/workflows/azure-deploy.yml`:

```yaml
name: Azure Deploy
on:
  push:
    branches: [main]
    paths: [infra/**, app/**]
  pull_request:
    paths: [infra/**]
permissions:
  id-token: write
  contents: read
jobs:
  what-if:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id:       ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id:       ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: |
          az deployment sub what-if \
            --location swedencentral \
            --template-file infra/main.bicep \
            --parameters @infra/main.parameters.json
  deploy:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: azure/login@v2
        with:
          client-id:       ${{ secrets.AZURE_CLIENT_ID }}
          tenant-id:       ${{ vars.AZURE_TENANT_ID }}
          subscription-id: ${{ vars.AZURE_SUBSCRIPTION_ID }}
      - run: |
          az deployment sub create \
            --location swedencentral \
            --template-file infra/main.bicep \
            --parameters @infra/main.parameters.json
```

### 3.5 検証

- PR を立てる → `what-if` job が green、コメントに 0 Modify が出る
- PR を main に merge → `deploy` job が green、`az deployment sub list` で最新 deployment が `Succeeded`

---

## 4. ローカル開発環境 (3名チームの最小共通項)

### 4.1 必須

| ツール | 最低バージョン | 用途 |
|--------|---------------|------|
| Node.js | 20.x | discord-bot |
| Bun | 1.x | discord-bot 開発体験向上 (任意) |
| Python | 3.12 | scaffold/app (Azure agent) |
| `uv` | latest | Python パッケージ |
| Azure CLI | 2.60+ | Bicep デプロイ・認証 |
| Bicep | 0.27+ | `az bicep install` で OK |
| `gh` | 2.50+ | PR / secret / webhook 操作 |
| `jq` | latest | JSON 整形 |
| Claude Code | latest | `/install-github-app`, `@claude` |

Windows + WezTerm (operator) と macOS (チームメンバー) で動く前提。

### 4.2 環境変数 (`discord-bot/.env`)

```bash
DISCORD_TOKEN=...           # bot token (Developer Portal)
DISCORD_CLIENT_ID=...       # application id
DISCORD_GUILD_ID=1478407098521092198
ANTHROPIC_API_KEY=...       # /ask command 用
```

`.env.example` をリポジトリに含める（実値ではなくキー名のみ）。

### 4.3 Azure 認証

```bash
az login              # 個人 MSA — ハッカソン用
az account set --subscription 2c29a97c-08b6-4bc3-88ea-266eb1cfd730
az account show -o table
```

teammate（M2/M3）はゲスト招待を accept してから上記。RG-scope Contributor のため、`rg-hack2026-dev` 配下は触れる、`rg-hack2026-shared` は read + secret 操作のみ。

### 4.4 Spec-driven 開発の入口

```
.kiro/specs/{feature}/
  ├── requirements.md   ← 1. 要件定義
  ├── design.md         ← 2. 技術設計
  ├── tasks.md          ← 3. タスク分解
  └── spec.json         ← language: ja, status
```

スラッシュコマンド (`/kiro:spec-init`, `/kiro:spec-requirements`, etc.) でフェーズ間遷移。3-phase approval workflow（Requirements → Design → Tasks → Implementation）を守る。

---

## 5. ワークフロー定型 (3 名運用)

### 5.1 PR ライフサイクル

1. `git switch -c {feature}/{slug}` (例: `agent/ppt-polish-llm-call`)
2. `.kiro/specs/{feature}/` に requirements → design → tasks
3. 実装 → push → PR open
4. **GitHub-side**:
   - `@claude review` で AI 1 次レビュー
   - 人間 SME 1名 approval (`member-a` or `member 3`)
5. **Discord-side** (`#hack-dev-log` forum):
   - PR opened webhook が `#github-feed` に流れる
   - 議論が必要なら forum thread を立てる（`infra` / `agent` / `prompt` のタグ付き）
6. Merge — squash 推奨（履歴を spec 単位で整理）

### 5.2 週次 digest commit

毎週金曜（手動 or Claude Code 駆動の cron）:

- `#hack-dev-log` の forum thread を要約
- `decisions/2026-W{NN}.md` に PR を立てる
- merge — Discord エフェメラル性への対抗策

### 5.3 デモ前チェックリスト (M5+)

- [ ] `az deployment sub list` で最新 deployment が `Succeeded`
- [ ] `gh run list --limit 5` で CI が green
- [ ] `#github-feed` に直近 24h のイベントが流れている
- [ ] `@claude review` がレスポンスを返す（App が生きている確認）
- [ ] `discord-bot` が稼働 (`/ask` を 1 回叩く)

---

## 6. ロードバンプ集 (実装時に踏みやすい点)

| 症状 | 原因 | 対処 |
|------|------|------|
| `npm run create-github-webhook` で 401 | bot token 失効 | Developer Portal で再発行、`.env` 更新 |
| Webhook 作成成功だが Discord に何も出ない | bot ロールが Hackathon Team 配下 → channel 権限なし | bot ロールを階層上位へ ([Phase 1.5](../../../../discord-bot/docs/server-setup-execution-guide.md)) |
| `@claude` が無反応 | App アンインストール / repo selection から外れた | <https://github.com/apps/claude> で再 Configure |
| `az deployment sub create` で `RoleAssignmentExists` | 重複の Owner assignment（platform fix #2 の状況） | `rbac.bicep` の ownerAssignment ブロックを削除 (2026-04-29 に landing 済み) |
| OIDC token exchange 失敗 (`AADSTS70021`) | federated credential の `subject` ミスマッチ | `repo:owner/repo:ref:refs/heads/main` のフォーマット厳守 |
| Forum thread の Required Tag が無効化される | Discord client cache | `set-forum-require-tag.ts` を再実行 |

---

## 7. 引数別タスクリスト

### 7.1 INT 系 (初期統合配線、~M4 完了想定)

| ID | タスク | 担当 | 状態 | 参照 |
|----|--------|------|------|------|
| INT-1 | Webhook script 実行 + GitHub 側登録 | operator | ✅ 完了 (2026-04-29) | §1 |
| INT-2 | Claude GitHub App インストール + claude.yml | operator | ✅ 完了 | §2 |
| INT-3 | OIDC `setup-gitops.ps1` 作成 | operator | ⏳ deferred (M5+) | §3 |
| INT-4 | `.env.example` をリポジトリに追加 | operator | ⏳ pending | §4.2 |
| INT-5 | 週次 digest commit を skills 化 | operator | ⏳ pending | §5.2 |
| INT-6 | `azure-deploy.yml` を `.github/workflows/` に追加 | operator | 🟡 workflow ファイル merged、creds 配線未検証 | §3.4 |

### 7.2 E 系 (4 サーフェス土台、プロダクト非依存)

「Discord chat = 開発インタフェース」を成立させるため、機能 (consolidate / spec / review / plan / digest 等) を実装する**前**に揃える環境。テーマ確定や Kiro spec 着手とは独立に進められる。

| ID | タスク | 担当 | 状態 | 補足 |
|----|--------|------|------|------|
| E1 | GitHub→Discord webhook (5 events) | operator | ✅ 完了 | INT-1 と同等 |
| E2 | `@claude` GitHub App + claude.yml | operator | ✅ 完了 | INT-2 と同等 |
| E3 | Meeting recap pipeline (Discord voice → /recap → repo) | operator | ✅ 完了 | `discord-bot/docs/meeting-recap.md` |
| E4 | Discord Bot → GitHub PAT 配線 | operator | ⏳ pending | `.env` に `GITHUB_PAT` (Issues / PRs / Contents:write)。recap で既存の token を拡張 |
| E5 | `.env.example` をリポジトリに追加 | operator | ⏳ pending | INT-4 と同等 |
| E6 | Discord Bot 実行ホストで `az` CLI アクセス | operator | ❌ 未確認 | ローカルでは可、bot プロセス文脈で `az account show` 通るか検証 |
| E7 | `#hack-pm` チャンネル作成 + bot ロール付与 | operator | ❌ 未着手 | PM 系統エージェントの承認サーフェス |
| E8 | OIDC App Reg + federated creds 実存確認 | operator | 🟡 workflow ファイルのみ | `gh secret list` + `az ad app list --display-name github-actions-hack2026` |
| E9 | `decisions/` ディレクトリ + ADR テンプレ | operator | ❌ 未着手 | 週次 digest / 拒絶ハーネス landing 先 |
| E10 | Discord forum tag セット (problem / theme / infra / dev / pm / deliverable) | operator | ❌ 未着手 | アグリゲーターのスライス軸と整合 |

---

## 8. 参考

- [`dev-workflow-research.md`](../../../../discord-bot/docs/dev-workflow-research.md) — Discord + GitHub + Claude Code 設計の根拠
- [`server-setup-execution-guide.md`](../../../../discord-bot/docs/server-setup-execution-guide.md) — Discord サーバー手順
- [Anthropic Claude GitHub App](https://github.com/apps/claude)
- [Azure Login OIDC](https://github.com/Azure/login#login-with-openid-connect-oidc-recommended)
- [GitHub webhook events reference](https://docs.github.com/en/webhooks/webhook-events-and-payloads)
