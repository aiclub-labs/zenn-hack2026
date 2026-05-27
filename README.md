# Microsoft Agent Hackathon 2026 — Scaffold

ハッカソンプロジェクト用のテーマ非依存スキャフォールド。テーマは 2026-05-11 に確定予定で、現時点の候補（新案A 人材マッチング / 新案C 知見アーカイブ / 新案D ドメイン学習）の比較は `../problem-statement.md` 参照。スキャフォールド自体は特定テーマを前提としておらず、候補間の pivot は agents と tools の差し替えのみで済み、インフラやフレームワークの変更は不要です。

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

## Sustainability / Responsible AI

- **Scale-to-zero**: Azure Container Apps を min-replicas=0 で運用。アイドル時の compute フットプリントゼロ。
- **Serverless data plane**: Cosmos DB serverless + AI Search free tier。常時稼働 capacity を持たず、リクエスト単位で課金 = 環境負荷も従量。
- **トークン効率**: デフォルトは `gpt-5.4-mini` に routing、必要時のみ `gpt-5.4` にエスカレート。`max_completion_tokens` は Hearout=400 / 自己批評=120 と厳格に制限（`app/api/turn.py`）。
- **観測可能性**: `aoai.token.total` を customMetric として日次集計（`app/util/cost.py:19` `aggregate_aoai_tokens_daily`）。Tier A/C 縮退条件 ($200 上限) は `infra/modules/budget.bicep:17-42` で alert 連動。Fairness proxy (reviewer × sector × decision) + Continuous iteration workbook 用 KQL 一式は `docs/observability-kql.md` 参照。
- **Responsible AI 自己評価**: MS RAI Standard v2 / KPMG Trusted AI / NIST AI RMF を統合した Impact Assessment は `docs/impact-assessment.md` 参照。12 harm × mitigation × file:line 出典、5 残存リスクを開示。
- **フレームワーク準拠レビュー**: Azure WAF AI / AWS GenAI Lens / KPMG / MS RAI / NIST AI RMF の 5 framework 横断 gap 分析を `.kiro/specs/dialogue-delta-formalization/framework-review.md` に記録。

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

- テーマ別データソース・ツール（候補確定後に追加）:
  - 新案A 人材マッチング: Microsoft Graph (HR) / KC Bridge / GPDR 連携 / マッチング reasoner
  - 新案C 知見アーカイブ: SharePoint API / NDA・機密分類 (Azure AI Document Intelligence) / retrieval ranker
  - 新案D ドメイン学習: scheduled jobs (Functions) / Teams 通知 / transcript ingest
- 個別エージェントの persona（テーマ確定後、`app/agents/` 配下に追加）

<!-- B3 /gh pr-merge smoke test 2026-05-12T08:16:07Z -->
