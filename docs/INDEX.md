# ハッカソン — インデックス

> **Microsoft Agent Hackathon Japan 2026 (Zenn)** · KPMG AI部 · 法人部門 · 2026-06-01 提出 · 3 名

このフォルダはオペレータの企画用ワークスペース。チームメンバーは GitHub リポジトリ (`aiclub-labs/zenn-hack2026`) を参照する想定です。企画ドキュメントは Phase B（GitHub Projects bootstrap）でリポジトリ側にオンボード予定。

## 知りたいことから飛ぶ

| 質問 | ファイル |
|---|---|
| **今週何が起きてる？何がブロック？** | [STATUS.md](./STATUS.md) — ライブ、毎セッション更新 |
| **タイムラインは？マイルストーンの担当は？** | [ROADMAP.md](./ROADMAP.md) — 日付・RACI のシングルソース |
| **Azure はどうセットアップする？** | [azure-setup.md](./azure-setup.md) — TL;DR runbook + 決定事項 D1–D9 |
| **採択テーマと問題設定は？** | [problem-statement.md](./problem-statement.md) — As-Is/To-Be/Gap のカノニカル |
| **テーマの技術設計は？** | [architecture-cards/idea-f-dialogue-monitoring.md](./architecture-cards/idea-f-dialogue-monitoring.md), [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/) |
| **プロジェクト方針・意思決定は？** | [.kiro/steering/](../.kiro/steering/)（product / tech / structure / decisions / development-model） |
| **技術スタックと選定理由は？** | [.kiro/steering/tech.md](../.kiro/steering/tech.md), [research/azure-agent-platform-decision.md](./research/azure-agent-platform-decision.md), [dev-prep.md §9](./dev-prep.md) |
| **開発の前提条件で未確定のものは？** | [dev-prep.md](./dev-prep.md) §1–§9 |
| **新メンバーのオンボーディングは？** | [TEAM-SETUP.md](./TEAM-SETUP.md) — 自己完結。メンバー 2 & 3 に転送可 |
| **オペレータが手動でやるべきブラウザ/ポータル作業は？** | [HANDOFF.md](./HANDOFF.md) |
| **部門選択（4/23）で何が決まった？** | [action-plan.md](./action-plan.md) Phase 1 |
| **実コードはどこ？** | `github.com/aiclub-labs/zenn-hack2026`（private; ローカルでは `./scaffold/` に clone 済） |

## ドキュメントの状態（編集前に確認）

- **カノニカル参照**（採択後の正本）: `problem-statement.md`, `architecture-cards/idea-f-*.{md,html}`, `.kiro/steering/*.md`, `.kiro/specs/dialogue-delta-formalization/`
- **生きた企画ドキュメント**（このインデックスで一行ずつ管理。状態が変わったら更新）: `STATUS.md`, `ROADMAP.md`, `azure-setup.md`
- **意思決定ログ + 未解決項目**（基本追記のみ）: `action-plan.md`, `dev-prep.md`, `HANDOFF.md`, `.kiro/steering/decisions.md`
- **pre-kickoff ブレスト資料**（off-repo に退避済、参照のみ）: personal-hub `../archive/` 配下

## 規約

タイムライン / 進捗を重複記載していたドキュメントは、すべて以下を参照する形に変更しました:

> **Project status & timeline canonical sources:** `STATUS.md`（現状）· `ROADMAP.md`（タイムライン）· `INDEX.md`（ナビゲーション）

日付や進捗を編集する場合は `ROADMAP.md` または `STATUS.md` のみ更新してください。他のドキュメントで「see ROADMAP」と書いてあれば、ROADMAP の値を信じて、コピーバックしないでください。
