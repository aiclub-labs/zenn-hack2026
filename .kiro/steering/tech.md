# Technology Stack

## Architecture

**Foundry Agent Service Workflow (preview) + MAF 1.0 + BYO Cosmos DB のハイブリッド構成**。Stateless な API / UI 層 (Container Apps) と Stateful な agent 層 (Foundry Workflow) を分離し、conversation state は BYO Cosmos に永続化、corpus は AI Search に格納。

採用根拠と Week 1 (2026-05-18) flag day 検証計画は `../../docs/research/azure-agent-platform-decision.md` 参照。バックアップは MAF を Container Apps に直接デプロイ（converged runtime のためコード移植可能）。

## Core Technologies

- **Agent SDK**: Microsoft Agent Framework 1.0（2026-04-03 GA、Semantic Kernel + AutoGen 統合後継）
- **Agent Runtime**: Microsoft Foundry Agent Service (Workflow agent preview)
- **LLM**: AOAI gpt-4o (Hearout / Formalization), gpt-4o-mini (Delta scoring / Truth assist)、既存 swedencentral リソース流用
- **Backend**: Node.js 20 + Fastify (API), MAF SDK (Python or .NET、flag day 後に確定)
- **Frontend**: React 18 + Vite（Chat / Admin / Review の 3 SPA shell、1 Container App で host）
- **Data**: Cosmos DB Serverless (BYO conversation state) / AI Search Basic (corpus index)
- **Infra**: Azure Container Apps (既存 environment), Key Vault `kv-hack2026-tyu3o4`, App Insights, Entra ID + Managed Identity

## Key Libraries / Patterns

- **MAF `RequestInfoEvent` / `ToolApprovalRequestContent`** — HITL pause-resume の標準実装。自前で workflow 停止/再開を組まない
- **Foundry Workflow YAML / graph** — 4 agent orchestration + HITL を宣言的に記述
- **per-agent Microsoft Entra identity** — agent ごとに最小権限スコープを発行
- **AgentThread checkpoint to Cosmos JSON** — 長期対話セッション中断・再開の標準機構

## Development Standards

### Type Safety
- TypeScript strict mode (frontend / API)
- Python type hints + `mypy --strict` または .NET nullable annotations（agent 側、SDK 選定後に確定）
- `any` / dynamic 禁止、`unknown` で受けて narrowing

### Code Quality
- ESLint + Prettier (TS), ruff (Python), `dotnet format` (.NET)
- File 300 行 / function 50 行を上限目安（CLAUDE.md グローバルルール準拠）

### Testing
- Unit: Delta scoring 境界 / weight 計算 / schema cooldown / AI Search filter / ChatExtract 確認応答
- Integration: turn → gap → Hearout → Formalization → Reviewer → Search upsert → 次 turn 引用の E2E
- HITL: `RequestInfoEvent` pause-resume / 24h expired / Discord 通知

## Development Environment

### Required Tools
- Node.js 20+, npm
- Python 3.11+ or .NET 8+（agent SDK 言語次第）
- Azure CLI (`az`), Azure Developer CLI (`azd`)
- Docker / Container Apps CLI (ローカル開発時)

### Common Commands
```bash
# Provision: ./scaffold/scripts/bootstrap-phase0.ps1（既存 AOAI / Container Apps 環境を流用）
# AOAI 確認: ./scaffold/scripts/aoai-provision.sh
# Build: azd up（scaffold/azure.yaml で定義）
# Test: pyproject.toml / package.json の test target
```

## Key Technical Decisions

| 決定 | 採用 | 出典 |
|------|------|------|
| Agent platform | Foundry Workflow + MAF + BYO Cosmos | `../../docs/research/azure-agent-platform-decision.md` |
| 正誤判定 MVP | GraphCheck 型 (atomic claim 分解 + corpus 照合) | `../../docs/research/tacit-knowledge-ai-prior-art.md` |
| 正誤判定 冷起動 | FactCheck 型 (3 LLM ensemble vote、corpus < 30 件時のみ) | 同上 |
| 重み付け MVP | LLM 自己批評スコア A のみ（B/C は Phase 2/3） | Kunumi arXiv 2507.03811 |
| ヒアリング | Kunumi 5-step に 5W1H 埋込 + ChatExtract follow-up confirmation | Kunumi + Nature 2024 |
| Region | AOAI: swedencentral 既存 / Foundry Hosted agent: 提供状況 Week 1 確認 | flag day 議題 |

## Budget Constraints

- **総枠**: $200 / 6 週
- **想定**: $128 (MVP) + $15 (検索 SPA nice-to-have) + バッファ $57
- **アラート**: 累積 $120 (M8 burn-rate gate) / $150 (warning) → Tier A/C 削減推奨
- **scale-to-zero**: Container Apps idle 5 分で停止

詳細スコープ縮退ラダー: `../../docs/architecture-cards/idea-f-dialogue-monitoring.md` §5b

## Security Baseline

- API キー直接利用禁止、すべて Entra ID + Managed Identity 経由
- secret は Key Vault `kv-hack2026-tyu3o4` に集約
- per-agent Entra identity で最小権限スコープ
- `redact = true` フラグ立てた turn の content は Cosmos に保存せずメタデータのみ
- 認証エラー時のユーザー返答は汎用 5xx、詳細は内部ログのみ

---
_Document standards and patterns, not every dependency_
