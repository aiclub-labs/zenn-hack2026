# ハッカソン — ロードマップ

> **唯一のカノニカルタイムライン。** 他のドキュメントが日付に言及する場合はここを指す。
> ライブ実行状態は [STATUS.md](./STATUS.md)、ナビゲーションは [INDEX.md](./INDEX.md)。

## マイルストーン

| # | 日付 | マイルストーン | 成果物 | オーナー | 状態 | 詳細 |
|---|---|---|---|---|---|---|
| M0 | 2026-04-23 | 部門選択 frozen | 法人部門 (法人 AI部) で参加 | オペレータ | ✅ done | [action-plan.md §フェーズ1](./action-plan.md) |
| M1 | 2026-04-28 | Azure アカウント開設 | Free Trial sub + $200 クレジット + テナント + AI-club MS account | オペレータ | ✅ done | [azure-setup.md §2.1](./azure-setup.md)（D9） |
| M2 | 2026-04-28 | GitHub repo + scaffold push | `aiclub-labs/zenn-hack2026`（private）、58 ファイルの初回コミット | オペレータ | ✅ done | [HANDOFF.md §C](./HANDOFF.md), [INDEX.md](./INDEX.md) |
| M3 | 2026-04-30 | モックスタイルガイド確定 | `../tests/fixtures/demo-style-guide.yaml` に値が入った状態 | メンバー 3 | ⏳ in progress | [dev-prep.md §10](./dev-prep.md) |
| M4 | by 2026-05-04 | Phase 0–2 完了 | hack2026 sub の rename/tag、メンバー招待、RBAC 適用、インフラ provision（RGs/KV/Storage/CAE/LAW/AppI） | オペレータ | ✅ done 2026-04-29 | [azure-setup.md TL;DR](./azure-setup.md) steps 2–6 |
| M5a | 2026-05-05 | AOAI 最小プロビジョン | **gpt-4o-mini のみ** を Key Vault に格納（テーマ非依存で必ず使う） | オペレータ | ✅ done 2026-05-11（6日遅延、GlobalStandard SKU 修正含む） | [azure-setup.md §6](./azure-setup.md)（D7） |
| M5b | 2026-05-11 | AOAI 追加プロビジョン | M6 確定テーマに応じて **gpt-4o**（仲裁/横断推論用）+ **text-embedding-3-small**（RAG 路線採択時のみ）を追加 | オペレータ | ⏳ scheduled | [azure-setup.md §6](./azure-setup.md)（D7） |
| M6 | 2026-05-11 | **テーマ確定** | 暗黙知形式化（dialogue-monitoring 方式 / idea-f）採択、v1 スコープ確定 | 3 名全員 | ✅ done 2026-05-11（1 日遅延） | [problem-statement.md](./problem-statement.md), [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/) |
| M7 | 2026-05-14 | エントリーセッション参加 | Microsoft イベント 12:30–14:30 — グレーゾーン質問の確認 | オペレータ（代表） | ⏳ scheduled | [problem-statement.md](./problem-statement.md), [dev-prep.md §12](./dev-prep.md) |
| M8 | 2026-05-22 | バーンレートチェック | $120 超え消費なら gpt-4o → gpt-4o-mini に Arbiter を縮小 | オペレータ | ⏳ scheduled | [azure-setup.md §8.1](./azure-setup.md) |
| M9 | 2026-05-25 | MVP 統合完了 | 全エージェント結線、Streamlit デモがデプロイ済 CAE 上で E2E 動作 | 3 名全員 | ⏳ scheduled | [action-plan.md フェーズ3](./action-plan.md) |
| M10 | 2026-05-28 | Free Trial → PAYG | Card-on-file が有効化、デモまで sub 継続。M9 から 3 日間バッファ（PAYG 切替で課金エンジンが切替わるため CAE 動作確認時間が必要） | オペレータ | ⏳ scheduled | [azure-setup.md §2.6](./azure-setup.md)（D9） |
| M11 | 2026-05-30 | デモ + Zenn 完成 | 録画デモ（2–3 分）、Zenn ドラフト、GitHub README 仕上げ。提出 24h 前ではなく 48h 前完成で事故バッファ確保 | メンバー 2（ブログ/動画リード） | ⏳ scheduled | [dev-prep.md §7](./dev-prep.md) |
| M11.5 | 2026-05-31 | 予備日 + 最終チェック | エンコード再実行 / Zenn 公開リジェクト対応 / URL 再発行などの fault buffer。新規作業は禁止 | 全員 | ⏳ scheduled | — |
| M12 | **2026-06-01 23:59** | **提出** | 成果物URL + Zenn URL + GitHub URL を提出フォームから提出 | オペレータ（代表） | 🚨 ハードデッドライン | [action-plan.md フェーズ4](./action-plan.md) |
| M13 | 2026-06-10〜 | Teardown（条件付き） | 最終ラウンド通知後に判断。**通過した場合は M15（6/18）後まで sub 継続**。落選なら 6/10 以降に `azd down --purge` + KV purge + AOAI purge。**審査期間 6/2〜6/9 中はリソースを残す（成果物URL の生存が必須）** | オペレータ | ⏳ contingent | [azure-setup.md §9](./azure-setup.md) |
| M14 | 2026-06-10 | 最終ラウンド通知 | 通過していればピッチ準備 | 3 名全員 | ⏳ contingent | [action-plan.md フェーズ5](./action-plan.md) |
| M15 | 2026-06-18 | 最終審査・表彰式 | ピッチ（通過した場合） | 3 名全員 | ⏳ contingent | [action-plan.md フェーズ5](./action-plan.md) |

## RACI — 誰が何を担当する

暫定振り分け。役割は [idea-f アーキテクチャカード](./architecture-cards/idea-f-dialogue-monitoring.md) のコンポーネント分割にマッピング。

| 機能 | R（実行） | A（説明責任） | C（相談） | I（共有） |
|---|---|---|---|---|
| **Infra / Azure / OIDC / 予算** | オペレータ | オペレータ | M2, M3 | — |
| **エージェントコード（SK + MCP）** | メンバー 2 | オペレータ | オペレータ（レビュー） | メンバー 3 |
| **UI / Streamlit / デモフロー** | メンバー 3 | メンバー 3 | オペレータ | メンバー 2 |
| **スタイルガイドルール + デモデータ** | メンバー 3 | メンバー 3 | オペレータ, M2 | — |
| **Zenn ブログのドラフト + 最終版** | メンバー 2 | メンバー 2 | オペレータ, M3 | — |
| **デモ動画の録画 + 編集** | メンバー 2 | メンバー 2 | 全員 | — |
| **提出パッケージ + 提出フォーム入力** | オペレータ | オペレータ | M2, M3 | — |
| **テーマ決定の調停** | 全員 | オペレータ | — | — |

## 依存関係（クリティカルなもの）

- **M5a は M4 に依存** — `rg-hack2026-shared` 内の AOAI は RG が存在することを前提（Phase 2 Bicep）
- **M5b は M6 に依存** — 追加モデル（gpt-4o / text-embedding-3-small）の必要性はテーマ確定後に決まる
- **M9 は M5a + M5b + M6 に依存** — エージェント統合には AOAI フル稼働 AND テーマ確定の両方が必要
- **M10 は M9 に依存（バッファ込み）** — PAYG 切替は MVP 動作確認後に。最低 3 日のバッファで切替事故を吸収
- **M11 は M9 + M10 に依存** — デモ録画は MVP + 安定した課金状態の両方が前提
- **M12 は M11 に依存** — 提出にはデモ URL + Zenn 記事の公開が必要
- **M13 は M14 に依存（条件付き）** — Teardown は最終ラウンド通知（M14, 6/10）の結果で実施可否が決まる。**審査期間 6/2〜6/9 中はリソース存続が必須**

## 切替トリガー

M6（2026-05-11）で idea-f（dialogue-monitoring 方式 暗黙知形式化）採択済。代替案候補へのフォールバックは **設けない**（M12 を延長しないため）。MVP スコープ縮退で対応する場合は [problem-statement.md §Non-Goals](./problem-statement.md) と [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/) を参照。
