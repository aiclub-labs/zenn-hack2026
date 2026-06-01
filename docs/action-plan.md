# AI部 アクションプラン — Microsoft Agent Hackathon 2026

> 📌 **進行中タスクは GitHub Issues 管理**: https://github.com/aiclub-labs/zenn-hack2026/issues — このファイルは背景情報・ランブック用。新規タスクは Issue を切ること。

> **Project status & timeline canonical sources:** [STATUS.md](./STATUS.md) (current state) · [ROADMAP.md](./ROADMAP.md) (timeline) · [INDEX.md](./INDEX.md) (navigation)
>
> このドキュメントは **意思決定ログ** として保持。週次のアクション項目・最新の進捗は STATUS.md / ROADMAP.md を見ること。

**作成日**: 2026-04-14
**最終更新**: 2026-05-13（M6 確定後の post-kickoff refresh）
**提出締切**: **2026-06-01 23:59**（詳細は [ROADMAP.md](./ROADMAP.md)）

> ⚠️ **Post-M6 状態**: 2026-05-11 に idea-f（暗黙知形式化 dialogue-monitoring 方式）採択済。フェーズ1–2 の旧記載（部門選択・shortlist A–E ベースのアイデア出し）は履歴として保持。採択テーマの正本は [problem-statement.md](./problem-statement.md) と [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/)。

---

## 0. 4/16 反映の重要ポイント

要件が大きく変わったため、**最初のアクションは「部門選択の再検討」** になる。

- **個人部門** が新設された（賞金 ¥10〜50万・現金）
- **法人部門の賞金は現金 → トロフィー＋登壇枠** に変更
- 同一企業から複数チーム提出可・法人部門でも個人Azureアカウント可
- 詳細差分は overview.md §11 _(pre-kickoff, archived off-repo)_ を参照

---

## フェーズ1: 部門選択 & 意思決定（〜4月23日）

### 部門選択（決定事項: 2026-04-23）

**法人部門で参加**（法人コンサルティング AI部として、新規Azureアカウント + 個人PCで実施）

| 軸 | 法人部門 | 個人部門 |
|----|---------|---------|
| 目的 | 法人社名でのブランディング・登壇 | 賞金獲得・個人スキル証明 |
| 社内承認 | 必要（組織承諾必須） | 副業/兼業規定の確認のみ |
| 賞金 | なし（ノベルティ・登壇枠20分/10分） | 現金 ¥10〜50万 |
| 提出物 | 法人名で公開 | 個人名で公開（社名は任意） |

### 社内確認チェックリスト（マーケティング部門）

> 担当: チームメンバーが広報/マーケティング部門経由で確認中
> 前提: 個人PC・個人Azureアカウント・業務時間外での活動

- [x] ✅ **(1) 法人部門エントリーの組織承諾**（確認メール送付済み 2026-04-23）
- [ ] 🔄 **(2) 提出ブログ記事での 法人 所属表記の可否**（「法人 AI部として参加」と書くか）
- [ ] 🔄 **(3) 受賞時の社名露出・登壇・プレス発表の許諾**（最優秀20分/優秀10分の登壇枠、Zenn/クラスメソッド/東京エレクトロンデバイス/Microsoft の各社発信）
- [ ] 🔄 **(4) 成果物のIP帰属・GitHub公開可否・終了後の扱い**（個人PC/時間外で作成したもののIP判断）
- [ ] 🔄 **(5) 利益相反チェック**（Microsoft / クラスメソッド / 東京エレクトロンデバイスとの既存取引関係）

### その他フェーズ1タスク
- [x] AI部リーダーへ参加意思を共有 & 部門選択を相談
- [x] チームメンバー確定（**3名**）
- [ ] **Zenn エントリーフォーム登録**（チーム代表1名・法人名義・法人部門）
  - エントリー完了後に**成果物提出フォームURL**がメールで届く想定
  - **5/14 エントリーセッション**の案内もこの登録経由で確実に届く
  - 組織承諾メール (1) の結果を待たずに早期登録推奨（撤回は可能）

### チーム編成
- [x] 参加希望者を募集（AI部内Slack/Teams等で告知）
- [x] メンバー確定: **3名体制**
- [ ] 役割分担の仮決め（開発、ブログ執筆、デモ動画制作）

---

## フェーズ2: アイデア出し & 設計（4月23日〜5月11日） ✅

2026-05-11 ミーティングで **idea-f（暗黙知形式化 dialogue-monitoring 方式）** を採択。詳細・履歴は以下を参照:

- [problem-statement.md](./problem-statement.md) — 採択スコープ / As-Is / To-Be / Gap
- [architecture-cards/idea-f-dialogue-monitoring.md](./architecture-cards/idea-f-dialogue-monitoring.md) — 12 セクションのアーキテクチャカード
- [.kiro/specs/dialogue-delta-formalization/](../.kiro/specs/dialogue-delta-formalization/) — Kiro spec（initialized）
- [research/azure-agent-platform-decision.md](./research/azure-agent-platform-decision.md) — Microsoft Agent Framework 1.0 + Foundry Agent Service ハイブリッド構成
- [.kiro/steering/decisions.md](../.kiro/steering/decisions.md) — D1–D5 未解決決定の進捗

pre-kickoff の shortlist A–E ベースのブレストは off-repo `archive/` に退避済。

---

## フェーズ3: 開発（5月10日〜5月25日）

### Azure 環境構築（開発前の0日目）

- [ ] **新規Azureアカウント開設**（チーム代表の個人アカウント・法人業務アカウントとは分離）
- [ ] $200 フリークレジットの付与確認（ポータルのコスト管理で確認）
- [ ] `azure-setup.md` の TL;DR runbook に沿って実行（§2〜§5）
  - §2 Phase 0: テナント命名、サブ rename + tag、メンバー招待、sub-RBAC（`bootstrap-phase0.{sh,ps1}`）
  - §3 Phase 1: プロバイダ登録、objectId 解決、`main.parameters.json` 記入、`what-if`（`bootstrap-phase1.{sh,ps1}`）
  - §4 Phase 2: `azd provision` or `az deployment sub create` で Bicep 適用
- [ ] §5 検証（RG 3件 / deployment Succeeded / App Insights キー取得）— `bootstrap-verify.{sh,ps1}`

### 開発作業
- [ ] MVP実装（Azure上にデプロイ可能な状態）
- [ ] エージェント機能の実装 & テスト
- [ ] デモシナリオの確定

### Azureクレジット（2026-04-24 確定）

- **$200**: Microsoft 標準の Azure 新規サインアップ特典 → **新規開設で自動付与**。ハッカソン固有の申請フロー無し
- **¥50,000**: クラスメソッド経由・ハッカソン法人部門枠。条件「日本MS/東京エレクトロンデバイス/クラスメソッドのいずれとも Azure 取引がない企業」→ **法人 は MS アライアンス保有で対象外確定**
- **事務局問合せ不要**（`zenn-support@classmethod.jp` への確認は不要と判断）
- 開発は $200 のみを前提に設計（足りる見込み — `dev-prep.md` / budget ¥180 設定で管理）

### 中間チェックポイント（任意）
- [ ] **5/14 12:30-14:30** エントリーセッション参加（法人部門の場合）

---

## フェーズ4: 提出準備（5月25日〜6月1日）

### 提出物の作成
- [ ] **成果物URL** — デプロイ済みWebアプリ or Copilot Studio共有URL
- [ ] **Zennブログ記事**
  - 実装上の工夫
  - アーキテクチャ解説
  - プロンプトエンジニアリングの工夫
  - **デモ動画の埋め込み**（必須）
- [ ] **GitHubリポジトリ**（任意・無くても減点なし、ただし提出推奨）

### 提出フロー（Zenn 2段構成）

- [ ] ①フェーズ1で登録した **エントリー完了メール** に記載の**成果物提出フォーム**から入力
  - 提出項目: 成果物URL / Zennブログ記事URL / GitHubリポジトリURL（任意）
- [ ] ②**Zennブログ記事**を公開状態にしてURLを確定
- [ ] ③デプロイ先 URL の可用性確認（審査期間中も生きていること）

### 最終チェック
- [ ] 審査基準に照らした自己評価
- [ ] デモ動画の品質確認
- [ ] ブログ記事のレビュー
- [ ] **6/1 23:59 までに提出完了**

---

## フェーズ5: 審査対応（6月）

- [ ] 審査期間 6/2〜6/9 → 結果通知 **6/10**
- [ ] 最終ラウンド進出時: 6/11〜17 でピッチ準備
- [ ] **6/18 最終審査・表彰式**

---

## 重要イベント（更新版）

| 日付 | イベント | アクション |
|------|----------|------------|
| **5月14日 12:30-14:30** | エントリーセッション（法人向け・任意） | 参加して詳細確認 |
| **6月1日 23:59** | 提出締切 | 全提出物の提出完了 |
| **6月10日** | 最終ラウンド通知 | 結果確認 |
| **6月18日** | 最終審査・表彰式 | プレゼン（通過した場合） |

---

## 直近の最優先アクション

→ **[STATUS.md](./STATUS.md)** の "What's next this week" セクションを参照。
週次で更新されるため、このファイルでは管理しない。
