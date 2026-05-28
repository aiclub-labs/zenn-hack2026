# Dev Prep — テーマ非依存で進められる開発準備

> 📌 **進行中タスクは GitHub Issues 管理**: https://github.com/aiclub-labs/zenn-hack2026/issues — このファイルは背景情報・ランブック用。新規タスクは Issue を切ること。

> **Project status & timeline canonical sources:** [STATUS.md](./STATUS.md) (current state) · [ROADMAP.md](./ROADMAP.md) (timeline) · [INDEX.md](./INDEX.md) (navigation)
>
> このドキュメントは **dev prerequisite の決定事項** に絞る。進捗スナップショットは STATUS.md に移管。

**目的**: テーマ確定を待たずに進められる共通基盤を先に固める
**対象タスク**: #3 (Shared dev prerequisites) / #4 (Scaffold Agent baseline) / #5 (Submission workflow)

---

## 1. GitHub リポジトリ

### 決め事
- [ ] **リポジトリ名**: 案 → `msft-agent-hackathon-2026` or `kpmg-ai-club-hackathon`
- [ ] **可視性**: Private で開発 → 提出時に Public 切替（GitHub提出は任意だが推奨）
- [ ] **オーナー**: 個人アカウント（法人部門でも個人Azure利用のため、IP帰属確認(社内確認#4)の結果次第）
- [ ] **ライセンス**: MIT（提出後公開する場合）/ 決定保留（社内確認結果次第）

### ブランチ戦略
- `main`: 常にデプロイ可能
- `develop`: 統合ブランチ
- `feature/*`: 個人作業
- PR必須 / 3名中1名のレビューで merge OK

### 初期ディレクトリ構成（scaffold/ 実態と一致）
```
/
├── README.md           # 提出用
├── pyproject.toml      # Python deps + tool config
├── azure.yaml          # azd entry point
├── app/                # FastAPI + Semantic Kernel agents + MCP servers
│   ├── main.py
│   ├── agents/
│   ├── mcp/
│   └── config.py
├── ui/                 # Streamlit UI
├── infra/              # Bicep（subscription-scoped main + modules/）
├── scripts/            # ローカル開発・デプロイ補助
├── tests/              # smoke + 単体テスト
├── .devcontainer/      # Python + Azure CLI + Bicep の再現環境
└── .github/workflows/  # ci.yml / infra-ci.yml / infra-deploy.yml
```

---

## 2. Azure サブスクリプション

### 決め事
- [ ] **契約形態**: 個人 Pay-As-You-Go（$200 クレジット対象）
- [ ] **アカウント開設タイミング**: 新規開設で $200 自動付与（事務局問合せ不要 — `action-plan.md` §フェーズ3 確定済）
- [ ] **リージョン**: `swedencentral`（AOAI モデル可用性優先 — 詳細は `azure-setup.md` §6）
- [ ] **リソースグループ**: `rg-hack2026-dev` / `rg-hack2026-shared` / `rg-hack2026-prod`（Bicep が subscription scope で 3 RG を作成）

### 初期作成リソース（baseline）
- [ ] Azure OpenAI Service（GPT-4o-mini 優先 / クレジット節約）
- [ ] Azure AI Agent Service（案件次第）
- [ ] Azure Container Apps（scale-to-zero / §9 で確定）
- [ ] Azure Key Vault（秘匿情報）
- [ ] Azure Storage Account（ログ・成果物）
- [ ] Application Insights（トレース）

### コスト管理
- [ ] **予算アラート**: ceiling $180、80%（$144）と 100%（$180）で通知（`infra/modules/budget.bicep` 実装と一致）
- [ ] **Cost Management** で日次モニタリング
- [ ] 不要リソースは毎日停止

---

## 3. 秘匿情報管理

- [ ] **Key Vault** で API キー管理
- [ ] **ローカル**: `.env` ファイル（`.gitignore` 必須）
- [ ] **CI/CD**: GitHub Actions Secrets
- [ ] **共有方法**: 1Password or Bitwarden の共有ボールト（チーム3名）
- [ ] **禁止**: Slack/Teams直貼り、コミット、スクショ共有

---

## 4. チーム共有チャネル

- [ ] **コミュニケーション**: AI部Slack内の専用チャネル or 新規Teamsチーム
- [ ] **ドキュメント**: この personal-hub は個人管理 → チーム共有は別途（Notion or SharePoint）
- [ ] **タスク管理**: GitHub Projects or Jira Lite
- [ ] **定例**: 週1オンライン（30分）+ 非同期進捗

---

## 5. ローカル開発環境

### 共通
- [ ] **言語**: Python 3.11+ (Semantic Kernel / Azure SDK の主流)
- [ ] **代替**: C# .NET 8（Semantic Kernel 本家・.NET チーム向け）
- [ ] **IDE**: VS Code 推奨（Dev Container 利用可）
- [ ] **Azure CLI** + **Bicep CLI**

### devcontainer.json（推奨）
- Python 3.11 + Node.js 20 + Azure CLI プリインストール
- 3名が同一環境で再現可能

---

## 6. エージェント基盤（Baseline Scaffold）

> 案件を問わず動くHello World。テーマ確定後はここに機能を足す。

### 最小構成
- [ ] FastAPI (or Flask) で `/chat` エンドポイント
- [ ] Azure AI Agent Service or Semantic Kernel で 1ツール呼び出し
- [ ] Application Insights でトレース可視化
- [ ] Azure Container Apps に CLI デプロイ成功

### 狙い
- テーマが決まった瞬間に「ツール追加」だけで進められる状態
- デプロイ・認証・ログの地雷を先に踏んでおく

---

## 7. 提出物ワークフロー（タスク #5）

### Zenn ブログ
- [ ] **アカウント**: 個人 or 新規組織
- [ ] **組織化**: 「KPMG AI部」表記可否は社内確認(#2)結果次第
- [ ] **記事テンプレ**（事前に骨子を用意）:
  1. はじめに（課題背景）
  2. アーキテクチャ（図解）
  3. 技術選定の理由
  4. 実装の工夫（プロンプト・ツール設計）
  5. ハマりどころ
  6. デモ動画埋め込み
  7. まとめ・今後

### デモ動画
- [ ] **収録ツール**: OBS Studio（無料・高品質）
- [ ] **解像度**: 1920x1080 / 30fps
- [ ] **尺**: 2〜3分目安（Zenn埋め込み想定）
- [ ] **台本**: デモシナリオをもとに事前作成
- [ ] **字幕**: 日本語（提出対象が日本なので必須ではないが加点要素）

### GitHub README
- [ ] バッジ（ビルド・ライセンス）
- [ ] アーキテクチャ図
- [ ] 動かし方（make run / docker compose up）
- [ ] デモ動画リンク
- [ ] Zenn記事リンク

---

## 8. タイムライン（dev prep 単独）

| 日付 | マイルストーン |
|------|---------|
| 4/23〜4/27 | GitHubリポジトリ作成・ブランチ戦略合意・devcontainer整備 |
| 4/28〜5/03 | **クレジット申請フロー確認後**、Azureアカウント開設・baseline リソース作成 |
| 5/03〜5/10 | Hello World 疎通・デプロイパイプライン構築・Zennテンプレ準備 |

> テーマ確定（フェーズ2 終盤 = 5/10 前後）までにこのレイヤーを**完全に済ませておく** ことが目標。

---

## 9. Resolved decisions (2026-04-23)

| Question | Decision | Rationale |
|---|---|---|
| Language | **Python 3.11** | python-pptx maturity; SK + Azure SDK first-class; Claude Code/Codex strongest here |
| Agent framework | **Semantic Kernel (Python)** primary; Azure AI Agent Service as managed-host fallback | Multi-agent via AgentGroupChat; MCP plays well with SK |
| MCP | **`mcp` Python SDK**, servers hosted on **Azure Container Apps** with built-in authentication (Entra ID) | Spec-native SDK; CAE が agent 側と同一基盤で sidecar 配置しやすい |
| IaC | **Bicep** | Azure-native, single-sub simplicity; Codex-friendly |
| Compute | **Azure Container Apps** (scale-to-zero) | Lowest idle cost; good MCP sidecar fit |
| Frontend | **Streamlit** for v1; React only if stretch | Upload + approval UI in ~200 LOC |
| Repo owner | **Personal GitHub**, private until submission; revisit post-IP confirmation | Social check #4 still pending |
| Model default | **GPT-4o-mini**; escalate to **GPT-4o** for cross-page coherence + disagreement arbitration | Credit discipline |
| Secrets | Key Vault + local `.env` + 1Password shared vault | Zero-trust pattern, fits 3-person team |
| Observability | **Application Insights + OpenTelemetry** (SK integration) | Demo narrative: "watch the 4 agents converse in the trace" |

## 10. Resolutions (2026-04-23)

- [x] **Azure account ownership** → **Set up a new shared Azure account** dedicated to the hackathon; other members added as Contributors to `rg-hack2026-dev` / `rg-hack2026-shared` (RBAC は `infra/modules/rbac.bicep` で宣言)。Keeps $200 credit pooled, avoids personal account contamination.
- [x] **Zenn organization** → Plan to create an **"AI Club" Zenn organization** (does not exist yet). Action: create the org as part of submission-workflow setup (task #5). Fallback: publish under personal account with co-author tags if org creation is blocked on social check #2.
- [x] **Style Guide data for demo** → Use a **synthetic, public-safe mock style guide** (fictional "AI Club Consulting" brand) with realistic structure but invented values. Demonstrates the capability of enforcing *a* style guide without leaking the real one. Owner: Member 3 (detection rules). Deadline: end of Week 1 (2026-04-30).

## 11. New follow-ups generated

- [ ] Create shared Azure account（クレジット判断は確定済み・残るは作業のみ — `HANDOFF.md` §B）
- [ ] Reserve/claim `ai-club` (or alternative) Zenn organization handle — check availability before committing to the name
- [x] Draft `demo-style-guide.yaml` spec template → `../tests/fixtures/demo-style-guide.yaml`（Member 3 が 4/30 までに値確定）

## 12. Hackathon requirement compliance (full audit 2026-04-23)

### Hard mandates

| # | Rule | Satisfied by | Status |
|---|---|---|---|
| M1 | "Microsoft Azure アプリケーション実行基盤またはCopilot Studio" | Azure Container Apps | ✅ |
| M2 | "Microsoft AI技術" (1+) | Azure OpenAI + Semantic Kernel | ✅ (double) |

### Full stack audit

| Component | Rule status | Verdict |
|---|---|---|
| Azure Container Apps | Explicit allowlist (4/16 official) | ✅ |
| Azure OpenAI (GPT-4o-mini / GPT-4o) | Explicit allowlist | ✅ |
| Semantic Kernel (Python) | Explicit allowlist (added 4/16) | ✅ |
| Azure AI Agent Service (fallback) | Explicit allowlist | ✅ |
| MCP (Python SDK) | Not mentioned; MSFT-endorsed via Copilot Studio MCP support | ✅ Not prohibited, strategically aligned |
| Key Vault / Blob / App Insights / Entra ID / Bicep | Azure services, unrestricted | ✅ |
| Python 3.11 / Streamlit / python-pptx / FastAPI / OpenTelemetry | OSS, no restrictions found | ✅ |
| GitHub | MSFT-owned; officially accepted as submission repo | ✅ |
| Non-Microsoft AI in shipped product | **Not used** (avoids the only gray zone) | ✅ by exclusion |

### Risk-bite cases and how we avoid them

| Potential issue | Our posture |
|---|---|
| OpenAI direct (non-Azure) → arguably not "Microsoft AI" | Use Azure OpenAI only |
| AWS/GCP compute → breaks M1 | Azure Container Apps only |
| Claude Code / Codex shipping in product | They are dev-time collaborators only, not shipped |
| Non-MSFT AI as router/judge in the agent crew | Azure OpenAI exclusively for shipped agents |

### Questions to confirm at 5/14 entry session (or earlier inquiry)

- [ ] Region-specific model availability (GPT-4o-mini in `swedencentral`（現選定）vs. fallback region)
- [ ] Credit grant mechanics for new Pay-As-You-Go sub with Container Apps
- [ ] Soft preference between Semantic Kernel and Azure AI Agent Service at judging
- [ ] MCP architecture welcome as an explicit Agent pattern demonstration
- [ ] Gray zone: non-Microsoft AI as supplementary service inside the shipped pipeline (we're not doing it, but confirming prevents scope creep)
