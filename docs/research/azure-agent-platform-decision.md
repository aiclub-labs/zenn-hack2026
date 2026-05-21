# Azure Agent Orchestration プラットフォーム選定

> 作成日: 2026-05-12 / 用途: dialogue-delta-formalization spec の design フェーズ前確定
> 関連: ../../.kiro/specs/dialogue-delta-formalization/requirements.md, ../architecture-cards/idea-f-dialogue-monitoring.md
> 調査タイムボックス: 約 20 分。一次情報は Microsoft Learn / Azure 公式 pricing / Microsoft devblogs を優先採用。二次情報（メディア記事）は補強用途のみ。

---

## TL;DR (推奨案 + 3 行根拠)

**推奨: Microsoft Foundry Agent Service の "Hosted agents (preview)" 上に Microsoft Agent Framework 1.0 (旧 Semantic Kernel) で 4 エージェント workflow を実装し、state は "Bring your own Cosmos DB" で持つハイブリッド構成。**

1. **Agent Framework 1.0 が 2026-04-03 GA**、Semantic Kernel と AutoGen を統合した後継として multi-agent / HITL / durable workflow / checkpoint を 1.0 安定 API で提供（[devblogs](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)）。SK と AutoGen の単独採用は事実上不要になった。
2. **Foundry Agent Service 本体は追加料金ゼロ**（モデル token + 使用ツール課金のみ。[Pricing](https://azure.microsoft.com/en-us/pricing/details/foundry-agent-service/)）、既存の gpt-4o-mini swedencentral リソースをそのまま使えるため $200 予算に収まる。
3. **Cosmos DB を "Bring Your Own" として接続して conversation state を保持できる**ことが公式 docs で明示済み（[Foundry overview](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)、"Use your own Azure resources (for example, storage, Azure AI Search, and Azure Cosmos DB for conversation state)"）。要件の Cosmos persistence / AI Search RAG と矛盾しない。

---

## 1. Microsoft Foundry Agent Service の現状 (2026-05 時点)

### GA 状態 (公式 doc 最終更新 2026-05-09)

出典: [What is Microsoft Foundry Agent Service?](https://learn.microsoft.com/en-us/azure/foundry/agents/overview)

| コンポーネント | 状態 |
|---|---|
| Foundry Agent Service Runtime | **GA** |
| Prompt agents | **GA** |
| Workflow agents | **Preview** |
| Hosted agents (container-based) | **Public preview** |
| Multi-Agent Workflows | **Preview** ([InfoQ GA 報告](https://www.infoq.com/news/2025/05/azure-ai-foundry-agents-ga/)) |
| Connected Agents (point-to-point) | **Preview** |
| A2A protocol (agent-to-agent) | **Preview** |
| Memory tool / Web search tool | **Preview** |

注: 2025-05 (Build 2025) で GA、2025-10 以降 Microsoft Foundry にブランド統合。2026-04 に Microsoft Agent Framework 1.0 GA で SDK 側が安定化。

### 対話状態 (thread / session)

- 公式 Q&A ([Microsoft Learn answers 5542041](https://learn.microsoft.com/en-us/answers/questions/5542041/azure-ai-foundry-how-to-persist-memory-across-thre)) によれば **thread をまたいだメモリ共有は自動では行われない**（thread はステートレス境界）。Microsoft 管理のストレージに thread/message/run は保持される。
- 長期 state は (a) Memory tool (preview) (b) **Bring-your-own Cosmos DB** (c) Hosted agents 内のセッション永続化、のいずれかで実現する想定。
- Hosted agents は **session ID で論理セッションが識別され、$HOME や /files にアップロードしたファイルが永続化される**（[Hosted agents docs](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents)）。Scale-to-zero 料金体系。

### Multi-agent orchestration

- **Connected Agents (preview)**: agent を tool として呼び出す point-to-point パターン。
- **Multi-Agent Workflows (preview)**: stateful な orchestration 層。長期実行、context management、error recovery、durability を扱う。YAML / Visual Studio Code / Foundry portal で定義可能。
- **Workflow agents** はビジュアルビルダー + YAML で **branching logic / HITL ステップ / sequential or group-chat パターン**を直接サポート。
- 内部的には Semantic Kernel + AutoGen を統合した **converged runtime = Microsoft Agent Framework** が裏で動く（[VS Magazine 2025-10](https://visualstudiomagazine.com/articles/2025/10/01/semantic-kernel-autogen--open-source-microsoft-agent-framework.aspx)）。

### HITL サポート

公式 doc: [Workflows - Human-in-the-loop](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) / [Multi-agent Workflow with Human Approval blog](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/multi-agent-workflow-with-human-approval-using-agent-framework/4465927)

- **すべての orchestration パターンが HITL に対応**。`RequestInfoEvent` で workflow を一時停止し、人間からの応答待ち。
- **承認必須ツール**: agent が approval-required tool を呼ぶと workflow が pause、`ToolApprovalRequestContent` (.NET) / `function_approval_request` (Python) を emit。
- **チェックポイント機構**: pending request も checkpoint state に保存され、restore 時に `RequestInfoEvent` として再 emit。

→ 我々の 5W1H ヒアリング/形式化承認フローに必要な「人間レビュー → 続行」が**フレームワーク標準機能でカバー可能**。

### Container Apps / Functions 統合

- Hosted agents は container として Foundry 上で稼働。**bring-your-own VNet** 対応。
- Agent Framework agents は **Azure Durable Functions として実行可能**（[Durable Workflows blog](https://devblogs.microsoft.com/dotnet/durable-workflows-in-microsoft-agent-framework/)）。
- 既存の Container Apps Environment は **agent から呼ばれる側 (custom tool 実装)** として位置付けるのが整合的。MCP サーバとして Container Apps を露出する選択肢もあり ([Foundry overview](https://learn.microsoft.com/en-us/azure/foundry/agents/overview))。

### 価格モデルと $200 予算

公式: [Foundry Agent Service Pricing](https://azure.microsoft.com/en-us/pricing/details/foundry-agent-service/)

- **Foundry Agent Service 本体は no additional charge**。
- 課金されるもの:
  - Foundry Models (token 課金) — 既存の gpt-4o-mini GlobalStandard をそのまま流用 (約 $0.15/1M in, $0.60/1M out)
  - Foundry Tools (Grounding with Bing 等) — 我々の要件では Bing 不要、AI Search は既存リソース利用
  - Hosted agents の compute (scale-to-zero) — 開発期間中はアイドル時 $0
- **ハッカソン 3 週間 + デモ 1 回 + 短期テストで $200 内に収まる試算**。

---

## 2. Microsoft Agent Framework (旧 Semantic Kernel) + Container Apps 自前実装

### 最新版の正体

- **2026-04-03 に Microsoft Agent Framework 1.0 GA** ([devblogs](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/))。
- **Semantic Kernel + AutoGen の統合後継**。SK のエンタープライズ機能 (session-based state、type safety、middleware、telemetry) + AutoGen のシンプルな agent 抽象 + **graph-based workflow** による explicit multi-agent orchestration。
- C# / Python 両対応。プロダクションレディ、stable API。
- A2A / MCP プロトコル準拠。

### Multi-agent パターン

- `ChatCompletionAgent` / `AgentGroupChat` / 階層的合成 (triage agent → 専門 agent)。
- **Graph workflow** で 4 エージェント (Schema Manager / Delta Detector / Hearout / Formalization) のフローを宣言的に記述可能。
- **DevUI (preview)**: ブラウザベースのローカルデバッガで agent 実行、message flow、tool call、orchestration を可視化。

### Long-running state を Container Apps + Cosmos DB で持つパターン

公式: [Workflows - HITL](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) / [Durable Workflows](https://devblogs.microsoft.com/dotnet/durable-workflows-in-microsoft-agent-framework/)

- workflow が pause 時、**`AgentThread` 全体を JSON にシリアライズして persistence provider に保存**。
- persistence provider は plug-in 式。プロダクションでは **Azure Cosmos DB** を推奨と公式に明記。
- Resume 時、checkpoint から state + pending request を復元。

### Foundry Agent Service 不採用時に SK/MAF 単独でカバーできる範囲

| 機能 | MAF 単独 (Container Apps + Cosmos) | Foundry Hosted Agent 経由 |
|---|---|---|
| Multi-agent orchestration | OK | OK |
| HITL (approval gate / resume) | OK | OK |
| Cosmos 永続化 | 自前実装 (provider 設定) | BYO Cosmos 設定で同等 |
| Identity (Entra per-agent) | 自前 (managed identity) | 標準機能 |
| Observability (App Insights) | OpenTelemetry 手配線 | 標準 dashboard |
| Tool ecosystem (Bing/AI Search/MCP) | 自前接続 | catalog 利用可 |
| ホスティング | Container Apps を運用 | フルマネージド scale-to-zero |

### 採用判断

- **MAF 単独構成 (Foundry Agent Service なし)** も技術的には完全可能。3 週間ハッカソンでは「Foundry が止まったら詰む」リスクを避けるため**バックアップ案として保持**する価値あり。
- ただし観測性・identity・scale 周りを自前構築するコストは無視できない → **Hosted agent 上に MAF を載せる方が ROI 高い**。

---

## 3. AWS Bedrock Agents との機能比較

出典: [Q2 2026 比較記事 AgentMarketCap](https://agentmarketcap.ai/blog/2026/04/09/aws-bedrock-agentcore-vs-azure-ai-agent-service-vs-google-vertex-ai-agents-q2-2026) / [aiagentstore 比較](https://aiagentstore.ai/compare-ai-agents/amazon-bedrock-agents-vs-azure-ai-foundry) / Microsoft 公式 docs

| 機能 | AWS Bedrock AgentCore (GA 2025-10-13) | Azure Foundry Agent Service (GA 2025-05) | MAF + 自前 Container Apps |
|---|---|---|---|
| Multi-agent orchestration | Supervisor + collaborator agents | Connected Agents / Workflow / A2A | Graph workflow (MAF) |
| 長期 state / session | Session memory + S3 + DynamoDB | Thread (managed) + BYO Cosmos DB | Cosmos DB (自前 provider) |
| HITL | Lambda callback で実装 | Workflow 標準機能 (RequestInfoEvent) | MAF 標準機能 |
| 承認 / approval gate | カスタム実装 | `ToolApprovalRequestContent` 標準 | 同左 (MAF) |
| RAG 連携 | Knowledge Bases (Bedrock 内) | Azure AI Search (file_search / 直接接続) | AI Search SDK |
| Agent Identity | IAM / OAuth + Token Vault | **Microsoft Entra per-agent identity** | Managed Identity |
| 価格 (本体) | AgentCore 利用料 + 基盤モデル | **本体無料 + モデル token + tool** | Container Apps consumption |
| 強み | Lambda 統合、AWS native | M365 統合、Entra、無料 orchestration 層 | 完全制御、ロックイン回避 |

**「Bedrock Agents が対話状態管理含めカバー」と言われる具体機能 → Azure 側マッピング**

| Bedrock の機能 | Azure 等価 |
|---|---|
| Session-scoped memory | Foundry thread + Memory tool (preview) / BYO Cosmos |
| Knowledge Bases (managed RAG) | Foundry の file_search tool + Azure AI Search (既存リソース流用可) |
| Action groups (OpenAPI → Lambda) | Foundry custom function tool / MCP server (Container Apps) |
| Orchestration prompt | Workflow agent (YAML) / MAF graph workflow |
| Trace | Agent tracing + App Insights |
| Guardrails | Foundry guardrails (XPIA mitigation 込み) |

**Azure に「ない」もの**: 現時点で Azure の Memory tool は preview、長期 cross-thread memory は BYO Cosmos で埋める必要あり。Bedrock の Memory は GA で標準で長期化される。→ **本要件では BYO Cosmos が要件にマッチしているため不利にならない**。

---

## 4. 推奨アーキテクチャ + 採用根拠

```
┌────────────────────────────────────────────────────┐
│ Foundry Agent Service (Workflow agent, preview)    │
│  ├─ Schema Manager  (Prompt agent)                  │
│  ├─ Delta Detector  (Prompt agent)                  │
│  ├─ Hearout         (Workflow agent + HITL)         │
│  └─ Formalization   (Hosted agent / MAF code)       │
│                                                      │
│  HITL: RequestInfoEvent / function_approval_request │
└────────┬──────────────────┬─────────────────────────┘
         │                  │
         ▼                  ▼
┌────────────────┐  ┌─────────────────────┐
│ Azure Cosmos DB│  │ Azure AI Search     │
│ (BYO):         │  │  (既存 RAG)         │
│  - thread 永続 │  │                     │
│  - corpus      │  └─────────────────────┘
│  - checkpoint  │
└────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Azure Container Apps (既存 env)         │
│  - custom tools (MCP webhook)           │
│  - 業務対話の ingest worker             │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ Application Insights (既存)             │
│  - agent tracing                        │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ AOAI gpt-4o-mini (swedencentral, 既存)  │
└─────────────────────────────────────────┘
```

### 採用根拠

1. **既存リソースをすべて活かせる**: AOAI gpt-4o-mini、Container Apps Env、Key Vault、App Insights、AI Search は全て Foundry Agent Service / MAF と接続可能で再プロビジョン不要。
2. **コスト最小**: Foundry 本体無料 + token 課金のみ → $200 内安全。Cosmos DB は serverless で開発期は数ドル。
3. **ロックイン回避**: 万一 Foundry の preview 機能 (Workflow / Hosted agent) が動かない場合、**MAF 単独 + Container Apps** で同一コード資産を載せ替え可能（MAF が converged runtime のため）。
4. **HITL が標準機能**: 5W1H ヒアリング → 重み付き形式化承認のフローを自前で組まずに済む。
5. **multi-agent コミュニケーションが宣言的**: YAML / graph workflow で 4 agent の役割分担を spec design に直接落とし込める。

---

## 5. ハッカソンスコープでの判断 (3 週間制約)

| Phase | 期間目安 | やること | バックアップ |
|---|---|---|---|
| Week 1 (5/12-5/18) | Spec design + skeleton | MAF 1.0 で 4 agent の **ローカル動作** (Container Apps ではなく開発機) を最優先で確認。Workflow YAML で HITL の pause/resume を smoke test | preview 機能不安定なら Prompt agents 多用に切り替え |
| Week 2 (5/19-5/25) | Foundry へデプロイ + Cosmos 接続 | Hosted agent としてデプロイ、BYO Cosmos で thread state 永続化、AI Search 接続 | Hosted agent preview が詰まったら **MAF を Container Apps に直接デプロイ**して Foundry は Prompt agents だけ利用 |
| Week 3 (5/26-6/1) | Polish + demo | observability、demo シナリオ、提出 | — |

**重要判断**:
- **Hosted agent (preview)** が今もって preview なのは事実 → Week 1 終了時点で「Foundry Hosted agent で動かす」or「Container Apps に MAF を直接乗せる」を最終決定する **flag day** を設ける。
- **Workflow agent (preview)** の HITL 機能は新しい → 既存ハッカソンチームでは Prompt agent + MAF コードで HITL を組む方が確実なケースもある。Week 1 中に実機検証必須。

---

## 開いている疑問 / 要確認

1. **Foundry Hosted agent の swedencentral リージョン提供状況**: 公式 [limits-quotas-regions](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/limits-quotas-regions) の最新確認必須。要確認。既存 AOAI が swedencentral なので、Hosted agent が同リージョンになければクロスリージョン課金 / レイテンシ問題が出る。
2. **Workflow agent の YAML での 4-agent fan-out / join パターン**: 公式サンプルが multi-agent fan-out をどこまで宣言的にできるか要確認。HITL with parallel branches の例を探す必要あり。
3. **Memory tool (preview)** を使うか BYO Cosmos のみにするか: 機能重複の整理が必要。corpus はどちらに置くか spec design で決める。
4. **Free Trial → PAYG 移行タイミングと Foundry Agent Service の利用可否**: Free Trial 下で Hosted agent (preview) が enable できるか要確認。既知ノートに 5/26 PAYG 移行とあるため、それ以前に動作確認が必要なら制約になる。
5. **AutoGen の現状 (観点 4)**: AutoGen は Microsoft Agent Framework に統合済み、独立した製品ラインとしては事実上 MAF が後継。AutoGen 単独採用は非推奨（[devblogs](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/) 参照）。

---

## 参考一次資料

- [What is Microsoft Foundry Agent Service? - Microsoft Learn](https://learn.microsoft.com/en-us/azure/foundry/agents/overview) (最終更新 2026-05-09)
- [Foundry Agent Service Pricing](https://azure.microsoft.com/en-us/pricing/details/foundry-agent-service/)
- [Hosted agents in Foundry Agent Service (preview)](https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents)
- [Microsoft Agent Framework 1.0 GA blog](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/) (2026-04-03)
- [Agent Framework Workflows - Human-in-the-loop](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop)
- [Multi-agent Workflow with Human Approval using Agent Framework](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/multi-agent-workflow-with-human-approval-using-agent-framework/4465927)
- [Durable Workflows in the Microsoft Agent Framework - .NET Blog](https://devblogs.microsoft.com/dotnet/durable-workflows-in-microsoft-agent-framework/)
- [Azure AI Foundry Agent Service GA - InfoQ](https://www.infoq.com/news/2025/05/azure-ai-foundry-agents-ga/) (二次情報、GA タイムライン補強)
- [Semantic Kernel + AutoGen = Microsoft Agent Framework - VS Magazine](https://visualstudiomagazine.com/articles/2025/10/01/semantic-kernel-autogen--open-source-microsoft-agent-framework.aspx) (二次情報、統合経緯)
- [AWS Bedrock AgentCore vs Azure vs Google Vertex Q2 2026 - AgentMarketCap](https://agentmarketcap.ai/blog/2026/04/09/aws-bedrock-agentcore-vs-azure-ai-agent-service-vs-google-vertex-ai-agents-q2-2026) (二次情報、比較補強)
- [microsoft/agent-framework GitHub](https://github.com/microsoft/agent-framework)
