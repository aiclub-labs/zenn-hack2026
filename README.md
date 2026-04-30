# Microsoft Agent Hackathon 2026 — Scaffold

ハッカソンプロジェクト用のテーマ非依存スキャフォールド。第 1 候補は PPT Polish Agent（`../idea-shortlist.md` および `../ideation-workbook.md` 参照）ですが、このスキャフォールド自体は特定テーマを前提としていません — バックアップ案（Meeting → Action Agent）への pivot は agents と tools の差し替えのみで済み、インフラやフレームワークの変更は不要です。

> **AI レビュー**: PR 上で `@claude` メンションすると Anthropic Claude GitHub App がレビューコメントを返します。advisory レビューであり、merge ゲートは CODEOWNERS / 人間 SME approval のままです。

## 技術スタック

- **言語**: Python 3.11
- **エージェントフレームワーク**: Semantic Kernel（`AgentGroupChat` でマルチエージェント）
- **LLM**: Azure OpenAI（デフォルト `gpt-4o-mini`、必要に応じて `gpt-4o` にエスカレート）
- **統合プロトコル**: MCP (Model Context Protocol) — `mcp` Python SDK
- **API 層**: FastAPI
- **UI**: Streamlit（v1）。React は stretch goal
- **コンピュート**: Azure Container Apps（scale-to-zero）
- **シークレット**: Azure Key Vault + ローカルの `.env`
- **オブザーバビリティ**: Application Insights via OpenTelemetry
- **IaC**: Bicep
- **CI**: GitHub Actions

## ディレクトリ構成

```
scaffold/
├── README.md                    # このファイル
├── pyproject.toml               # Python 依存 + ツール設定（ruff, mypy, pytest）
├── .env.example                 # 環境変数の契約
├── .gitignore
├── .devcontainer/
│   └── devcontainer.json        # 再現可能な開発環境（Python + Azure CLI + Bicep）
├── app/
│   ├── main.py                  # FastAPI エントリーポイント + /health + /chat
│   ├── agents/
│   │   └── hello_agent.py       # 最小限の SK エージェント（テーマごとに差し替え）
│   ├── mcp/
│   │   └── echo_server.py       # MCP サーバーのテンプレート（テーマごとに差し替え）
│   └── config.py                # pydantic-settings 経由の設定
├── ui/
│   └── streamlit_app.py         # アップロード + 承認ループのスケルトン
├── infra/
│   ├── main.bicep               # サブスクリプションスコープの IaC エントリ（RG + modules を統括）
│   ├── main.parameters.json
│   ├── bicepconfig.json
│   └── modules/                 # resource-groups / shared / rbac / budget / policy
├── scripts/
│   └── dev.sh                   # ローカル開発便利スクリプト
├── .github/workflows/
│   └── ci.yml                   # push 時の lint + test
└── tests/
    └── test_smoke.py            # ハロー・ワールドテスト
```

## クイックスタート（ローカル、Azure 不要）

```bash
# 1. 仮想環境を作成
python -m venv .venv && source .venv/bin/activate  # Windows なら .venv\Scripts\activate
pip install -e ".[dev]"

# 2. .env テンプレートをコピー
cp .env.example .env
# Azure アカウント準備後に AZURE_OPENAI_* を埋める

# 3. API をローカル起動
uvicorn app.main:app --reload

# 4. UI を別ターミナルで起動
streamlit run ui/streamlit_app.py
```

## Azure へのデプロイ（Azure アカウント開設後）

`main.bicep` はサブスクリプションスコープで、3 つの RG（`rg-hack2026-{dev,shared,prod}`）も自身で作成します。完全な TL;DR ランブック・フェーズ別スクリプト（プロバイダ登録、メンバー OID 解決、what-if プレビュー、GitOps 配線）は `../azure-setup.md` および `scripts/` を、ブラウザ側のポータル作業は `scripts/automation/` を参照してください。

```bash
# オプション A — azd
azd env new hack2026
azd provision

# オプション B — az CLI のみ
az deployment sub create \
  --location swedencentral \
  --template-file infra/main.bicep \
  --parameters @infra/main.parameters.json
```

## このスキャフォールドに**含まれない**もの（テーマ確定後に追加）

- `python-pptx` および PPT 操作ツール（PPT Polish Agent が確定した場合のみ）
- Azure AI Speech のバインディング（バックアップの Meeting → Action Agent に pivot する場合のみ）
- 個別エージェントの persona（Scanner / Style Arbiter / Cross-Page Coherence など） — 第 1 週の Problem Statement 確定後に追加
