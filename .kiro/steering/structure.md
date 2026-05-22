# Project Structure

## Organization Philosophy

**Hackathon-scoped monorepo**。上層 `microsoft-agent-hackathon-2026/` は **kickoff 前後の運営／配布アーカイブ**（オンボーディング・連絡・アクセス手順・kickoff スナップショット）を平置きし、**実装と team-facing な進行ドキュメントは `scaffold/` 配下に閉じる**。Kiro SDD 成果物 (`.kiro/steering/`, `.kiro/specs/`) も実装側 = `scaffold/.kiro/` に置く。

Feature spec は **`.kiro/specs/{feature}/` を並列に切る**。umbrella spec は作らず、project-wide 制約は steering で束ねる（`../../docs/research/sdd-approach-evaluation.md` §4 結論）。

## Directory Patterns

### 上層（運営／配布アーカイブ）
**Location**: `microsoft-agent-hackathon-2026/`
**Purpose**: kickoff 前後の運営・告知・アクセス手順・スナップショット。team が日常的に参照する team-facing ドキュメントはここに置かない
**Example**:
- `HANDOFF.md`, `INDEX.md`, `STATUS.md`, `TEAM-SETUP.md` — 運営／オンボーディング
- `access-guide.md`, `azure-setup.md`, `kickoff-meeting-agenda.md`, `meeting-brief.html` — kickoff 前後の準備物
- `overview.md`, `idea-shortlist.md`, `ideation-workbook.md`, `tech-stack-matrix.md` — kickoff 時点のスナップショット
- `discord-hackchat-post.md` — 外部告知文案
- `archive/` — pre-kickoff 版の凍結資料（`problem-statement-pre-kickoff.md` 等）
- `scripts/` — 上層運営スクリプト

### 実装層 + team-facing 文書（scaffold）
**Location**: `scaffold/`
**Purpose**: 実装コード、IaC、CI/CD、Kiro spec / steering、および team が日常参照する進行ドキュメント
**Example**:
- `app/` — アプリ実装
- `ui/` — Chat / Admin / Review SPA
- `infra/` — Bicep IaC (`main.parameters.json` 等)
- `scripts/` — provision / bootstrap shell (`aoai-provision.sh`, `bootstrap-phase0.ps1`)
- `tests/` — テスト
- `decisions/` — ADR
- `azure.yaml` — Azure Developer CLI 定義
- `docs/` — team-facing 進行ドキュメント（下記参照）

### team-facing ドキュメント（scaffold/docs）
**Location**: `scaffold/docs/`
**Purpose**: チームが日常的に参照する進行管理・アーキ判断・リサーチ・議事録
**Example**:
- `problem-statement.md` — 正本 problem statement（5/11 決定反映）
- `ROADMAP.md` / `action-plan.md` / `dev-prep.md` — 進行管理・意思決定ログ・準備物
- `architecture-cards/idea-f-dialogue-monitoring.{md,html}` — 採択アーキ判断カード
- `architecture-cards/archive/idea-{a,c,cd,d,e}-*.{md,html}` — historical reference（凍結）
- `research/{tacit-knowledge-ai-prior-art, azure-agent-platform-decision, sector-unit-candidates, sdd-approach-evaluation}.md` — 一次リサーチ
- `meetings/2026-05-11.md` 等 — 議事録
- `branch-protection.md`, `discord-notify-setup.md` — 運用補助

### Kiro SDD 層
**Location**: `scaffold/.kiro/`
**Purpose**: Spec-Driven Development の永続成果物
**Example**:
- `steering/{product, tech, structure}.md` — 全 spec 共通の前提（本ファイル含む）
- `steering/decisions.md` — オープン論点 + 早期判断ゲート（custom steering）
- `specs/{feature}/{spec.json, requirements.md, design.md, tasks.md, research.md}` — feature spec
- 現状の spec: `specs/dialogue-delta-formalization/`

## Naming Conventions

- **Files (markdown / config)**: kebab-case（例: `dialogue-delta-formalization`, `sdd-approach-evaluation.md`）
- **Architecture cards**: `idea-{letter}-{slug}.md`（A-F のうち F が採用）
- **Research notes**: `{topic-slug}.md`、出典 URL を本文に明示
- **Decisions log entries (decisions.md)**: `D{n}` 連番、判断期限 / 主体 / 暫定結論を必ず付与
- **Components (TS/React)**: PascalCase、1 component = 1 ファイル
- **Functions / variables**: camelCase
- **Cosmos collections**: snake_case (`dialogue_turns`, `delta_events`, `hearout_records`, `formalization_queue`, `truth_judgment_logs`, `corpus_meta`, `error_logs`)
- **Partition key**: `{sector}#{unit}` 統一（多マス対応）

## Import Organization

```typescript
// 1. External
import { z } from 'zod';
// 2. Internal absolute
import { TurnService } from '@/services/turn';
// 3. Relative
import { computeDelta } from './delta';
```

**Path Aliases**:
- `@/`: `scaffold/app/src/` (TS 側)、`scaffold/app/` (Python は src layout)

## Code Organization Principles

- **Stateless / Stateful の境界**: API / UI は stateless、agent orchestration / checkpoint は Foundry に集約。アプリ側で workflow 状態を抱え込まない
- **Multi-cell-ready**: すべての persistent resource は `{sector}#{unit}` partition key を持つ。agent も `target_sectors` / `target_units` を環境変数で受ける
- **Research traceability**: design / spec の決定は `scaffold/docs/research/*.md` にリンクが辿れること。出典なしの数値・方式は禁止（steering/product.md §Non-Negotiable Principles #2）
- **Spec 横断参照**: feature spec 間の依存は各 `design.md` の `Related Specs` セクションでクロスリンク（umbrella spec を作らない）
- **3-phase 承認**: Requirements → Design → Tasks → Implementation の Kiro 流ワークフロー準拠

## Spec Lifecycle Status

`spec.json.phase` で進捗管理:
- `initialized` → `requirements-generated` → `design-generated` → `tasks-generated` → `implementing` → `validated`
- 各フェーズ `approvals.{phase}.approved = true` で次フェーズ移行可
- `-y` 高速化フラグはリスクの低いフェーズ限定（design は人間レビュー必須）

## What NOT to do

- Umbrella / メタ spec を `.kiro/specs/` 配下に作らない（Kiro 仕様外）
- Spec ファイルに `.kiro/settings/` 配下のメタデータを記述しない
- 上層 `microsoft-agent-hackathon-2026/` に実装コードを置かない（scaffold に閉じる）
- **team-facing 文書を上層に書かない**（`scaffold/docs/` 以下に置く。上層は kickoff 前後の運営・配布アーカイブ専用）
- 出典なし数値で要件を作らない（重み付け閾値 / 正誤判定スコア 等）

---
_Document patterns, not file trees. New files following patterns shouldn't require updates_
