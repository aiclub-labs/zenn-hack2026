#!/usr/bin/env bash
# One-shot: seed hackathon backlog issues into aiclub-labs/zenn-hack2026.
# Idempotent: skips issues whose title already exists.
set -e
REPO=aiclub-labs/zenn-hack2026
TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

create_issue() {
  local title="$1"
  local labels="$2"
  local milestone="$3"
  local body_file="$4"

  if gh issue list -R "$REPO" --state all --search "\"$title\" in:title" --json title --jq '.[].title' | grep -Fxq "$title"; then
    echo "SKIP (exists): $title"
    return 0
  fi

  local args=(-R "$REPO" --title "$title" --body-file "$body_file" --assignee "@me")
  IFS=',' read -ra LBL <<< "$labels"
  for l in "${LBL[@]}"; do args+=(--label "$l"); done
  if [[ -n "$milestone" ]]; then args+=(--milestone "$milestone"); fi

  gh issue create "${args[@]}"
}

# ============ #1 ============
cat > "$TMPDIR/b1.md" <<'EOF'
## 背景
Zennハッカソンへのエントリー提出と、KPMG社内承認・利益相反チェックを完了させる。提出が遅れるとエントリーセッション(5/14)案内が来ない。

## チェックリスト
- [ ] **A1** Zennエントリーフォーム提出（KPMG法人区分・チーム代表）
- [ ] **A2** Zenn org `ai-club` ハンドル予約（fallback: `kpmg-ai-club` / `aiclub-jp`）
- [ ] **A3-2** KPMG帰属表記の許可確認（マーケ）
- [ ] **A3-3** 表彰式・登壇権・プレスリリース許可確認
- [ ] **A3-4** 成果物IP帰属確認（個人PC・業務外時間）
- [ ] **A3-5** 利益相反チェック（Microsoft / Classmethod / 東京エレクトロン）

## 完了基準
エントリー確認メール受領 + 社内承認4件すべて文面で取得

## 参考
- `action-plan.md` §フェーズ1
- `STATUS.md` ブロック中項目
EOF
create_issue "[setup] Hackathon entry & 社内承認 (epic)" "area:setup,priority:p0,epic" "" "$TMPDIR/b1.md"

# ============ #2 ============
cat > "$TMPDIR/b2.md" <<'EOF'
## 背景
Discordサーバの最終仕上げ。デザインは完了済み (`discord-bot/docs/server-setup-execution-guide.md`)。残作業は実行・配線のみ。

## チェックリスト
- [ ] **D1** メンバー3名のDiscord User ID（18桁・Developer Mode）収集
- [ ] **D2** `#welcome` ピン留めメッセージ作成（日本語・rules + Server Guide）
- [ ] **D3** 2nd Admin（2FA有効）確認 — Community mode 必須
- [ ] **D4** ハッカソン後の alumni / 公開招待ポリシー決定
- [ ] **D5** `#github-feed` Webhook を `aiclub-labs/zenn-hack2026` に配線

## 完了基準
3名がそれぞれ役割割当済みでサーバ参加、`#github-feed` で push が流れることを確認

## 参考
- `HANDOFF.md` §D
- `discord-bot/docs/server-setup-execution-guide.md`
EOF
create_issue "[setup] Discord 仕上げ (epic)" "area:setup,priority:p1,epic" "" "$TMPDIR/b2.md"

# ============ #3 ============
cat > "$TMPDIR/b3.md" <<'EOF'
## 背景
M2/M3 の Azure / GitHub / Discord アクセス開通。Azure ゲスト招待は `PendingAcceptance` のまま。これが完了するまで M5 以降の検証に二人を巻き込めない。

## チェックリスト
- [ ] M2/M3 が UPN / GitHub username / Discord ID を提出
- [ ] M2/M3: Azure ゲスト招待受諾（メール: invites@microsoft.com）
- [ ] M2/M3: GitHub Collaborator 受諾（メール: noreply@github.com）
- [ ] (任意) ローカルツールチェーン（Azure CLI / azd / gh / bicep / Python 3.11 / Git）

## 完了基準
M2/M3 が `az login` 成功 + `gh repo clone aiclub-labs/zenn-hack2026` 成功

## 参考
- `TEAM-SETUP.md` Steps 1.1–1.3
EOF
create_issue "[setup] チームメンバー オンボーディング (epic)" "area:setup,priority:p0,epic" "" "$TMPDIR/b3.md"

# ============ #4 ============
cat > "$TMPDIR/b4.md" <<'EOF'
## 背景
Azure OpenAI のモデルデプロイメントを作成し、キーを Key Vault に格納する。これがないと agent コードのテストができない。

## チェックリスト
- [ ] gpt-4o-mini デプロイ作成
- [ ] gpt-4o デプロイ作成
- [ ] text-embedding-3-small デプロイ作成
- [ ] Key Vault にキー格納（`AOAI_API_KEY` / `AOAI_ENDPOINT`）
- [ ] `tests/test_smoke.py` から AOAI 呼び出し成功

## 完了基準
スモークテストが Container Apps 環境から AOAI を呼び出せる

## 参考
- `azure-setup.md` §6
- `ROADMAP.md` M5
EOF
create_issue "[infra] M5: Azure OpenAI プロビジョニング" "area:infra,priority:p0" "M5: AOAI provisioning" "$TMPDIR/b4.md"

# ============ #5 ============
cat > "$TMPDIR/b5.md" <<'EOF'
## 背景
コードレビュー指摘 S2: API キー認証だけでなく Managed Identity 認証フォールバックを追加すべき。本番デプロイ後にキーを Key Vault から外せる。

## チェックリスト
- [ ] `app/agents/hello_agent.py` で `DefaultAzureCredential` フォールバック実装
- [ ] Container Apps の System-Assigned Managed Identity に AOAI 権限付与
- [ ] 環境変数 `USE_MANAGED_IDENTITY=true` で切替可能に

## 完了基準
キー無しで AOAI 呼び出し成功

## 参考
- コードレビュー指摘 S2
EOF
create_issue "[infra] Managed Identity 認証フォールバック追加" "area:infra,priority:p1" "M5: AOAI provisioning" "$TMPDIR/b5.md"

# ============ #6 ============
cat > "$TMPDIR/b6.md" <<'EOF'
## 背景
M6 (5/10) のテーマ確定後、`hello_agent.py` を本実装エージェントへ拡張する。Semantic Kernel + MCP 統合。

## チェックリスト
- [ ] 確定テーマに沿ったエージェント実装
- [ ] MCP サーバ（`mcp/echo_server.py`）テンプレート + 本実装
- [ ] Semantic Kernel プラグイン化
- [ ] ユニットテスト追加

## 完了基準
M9 デモシナリオ通りに動作（ローカル + Container Apps）

## 参考
- `dev-prep.md` §6
- `ROADMAP.md` M6 / M9
EOF
create_issue "[agent] テーマ確定後の本実装エージェント開発" "area:agent,priority:p0" "M9: MVP integration" "$TMPDIR/b6.md"

# ============ #7 ============
cat > "$TMPDIR/b7.md" <<'EOF'
## 背景
PPT Polish Agent (Primary テーマ) のデモで使うモックスタイルガイド。実クライアント情報を漏らさないため架空ブランド「AI Club Consulting」を使う。

担当: Member 3
締切: 2026-04-30（既に過ぎている — 至急要確認）

## チェックリスト
- [ ] `scaffold/tests/fixtures/demo-style-guide.yaml` 完成
- [ ] フォントルール（見出し / 本文 / コード）
- [ ] カラーパレット（プライマリ / セカンダリ / アクセント）
- [ ] 余白・タイポグラフィ規約
- [ ] 架空ブランド「AI Club Consulting」設定の整合性

## 完了基準
PPT Polish Agent がこの YAML を読んで PPT を診断できる

## 参考
- `dev-prep.md` §10
- `ROADMAP.md` M3
EOF
create_issue "[agent] M3: モックスタイルガイド demo-style-guide.yaml 完成" "area:agent,priority:p1" "M6: Theme freeze + kickoff" "$TMPDIR/b7.md"

# ============ #8 ============
cat > "$TMPDIR/b8.md" <<'EOF'
## 背景
**M6 ハードゲート (2026-05-10)**。テーマが確定しないと本実装に入れない。Primary 候補: PPT Polish Agent / Backup: Meeting→Action Agent。

## チェックリスト
- [ ] Step6 problem statement ドラフトを M2/M3 にレビュー依頼
- [ ] キックオフでテーマ確定（Primary 採用 or Backup 切替）
- [ ] v1 スコープ定義 → 開発タスクIssue化（このメタタスク）
- [ ] Pivot判断基準合意（Week-2 5/10 までに blocker が出たら backup）

## 完了基準
README.md 冒頭に確定テーマ + 1段落 problem statement 反映

## 参考
- `ideation-workbook.md`
- `idea-shortlist.md`
- `ROADMAP.md` M6
EOF
create_issue "[ideation] M6: テーマ確定 (epic)" "area:ideation,priority:p0,epic" "M6: Theme freeze + kickoff" "$TMPDIR/b8.md"

# ============ #9 ============
cat > "$TMPDIR/b9.md" <<'EOF'
## 背景
M6 までにキックオフ完了。テーマ確定 + RACI 確定 + アーキテクチャレビュー + リスク確認をワンセットで実施。

## チェックリスト
- [ ] 5/10 までに開催日程確定
- [ ] アジェンダ準備（`kickoff-meeting-agenda.md` を活用）
- [ ] テーマ確定（#8 と連動）
- [ ] アーキテクチャレビュー
- [ ] RACI 確定（Operator / M2 / M3 の責任分担）→ README に追記
- [ ] リスク・backup theme 切替条件合意

## 完了基準
議事録を repo `docs/kickoff-notes.md` にコミット

## 参考
- `kickoff-meeting-agenda.md`
- `ROADMAP.md` RACI 表
EOF
create_issue "[team] M6: キックオフミーティング" "area:team,priority:p0" "M6: Theme freeze + kickoff" "$TMPDIR/b9.md"

# ============ #10 ============
cat > "$TMPDIR/b10.md" <<'EOF'
## 背景
M9 (5/25) までに全エージェント統合し Container Apps へデプロイ。E2E デモシナリオが本番URLで通ること。

## チェックリスト
- [ ] エージェント統合（agent + MCP + UI）
- [ ] Container Apps デプロイ
- [ ] 本番URL でデモシナリオ実行成功
- [ ] エラーログ・コスト確認
- [ ] CI 緑

## 完了基準
本番URL を共有してチーム3名がブラウザでデモシナリオを完走できる

## 参考
- `ROADMAP.md` M9
EOF
create_issue "[demo] M9: 全エージェント統合 + Container Apps E2E デプロイ" "area:demo,priority:p0" "M9: MVP integration" "$TMPDIR/b10.md"

# ============ #11 ============
cat > "$TMPDIR/b11.md" <<'EOF'
## 背景
M11 (5/31) までに提出資料3点セット完成: デモ動画 / Zenn記事 / GitHub README。

## チェックリスト
- [ ] デモ動画録画（OBS Studio, 1080p30fps, 日本語字幕, 2–3分）
- [ ] Zenn 記事ドラフト（アーキ / プロンプト / 実装知見 / 動画埋込）
- [ ] GitHub README（badges, アーキ図, デプロイ手順）
- [ ] 動画限定公開URL確保

## 完了基準
Zenn プレビューで読める状態 + 動画限定公開URLが Zenn 記事に埋め込み済み

## 参考
- `dev-prep.md` §7
- `ROADMAP.md` M11
EOF
create_issue "[demo] M11: デモ動画 + Zenn記事 + README 仕上げ" "area:demo,priority:p0" "M11: Demo + Zenn draft" "$TMPDIR/b11.md"

# ============ #12 ============
cat > "$TMPDIR/b12.md" <<'EOF'
## 背景
**ハード締切 2026-06-01 23:59 JST**。Zenn 提出フォームから3点送信。提出後すぐ teardown でコスト止血。

## チェックリスト
- [ ] デプロイURL を提出
- [ ] Zenn記事URL（公開状態）を提出
- [ ] GitHub repo URL（任意・推奨）を提出
- [ ] 提出確認メール受領
- [ ] **teardown 即実行**: `azd down --purge`
- [ ] Key Vault purge
- [ ] AOAI deployments purge
- [ ] Azure コスト残高確認（残債ゼロ）

## 完了基準
提出確認メール受領 + Azure リソースグループ全削除完了

## 参考
- `ROADMAP.md` M12 / M13
EOF
create_issue "[demo] M12: Zenn 提出フォーム送信 + teardown" "area:demo,priority:p0" "M12: Submission" "$TMPDIR/b12.md"

# ============ #13 ============
cat > "$TMPDIR/b13.md" <<'EOF'
## 背景
$200 Free Trial 内に収めるため継続的なバーンレート監視が必要。$180 を ceiling とする。

## チェックリスト
- [ ] Cost Management 予算アラート設定（$180 / 80% / 100%）
- [ ] 5/22 チェックポイント: $120 超なら gpt-4o-mini 限定運用へ切替
- [ ] M10 5/26: Free Trial 期限 vs PAYG 切替判断（カード課金回避 ~$10）
- [ ] 不要リソースの pre-stop 運用

## 完了基準
ハッカソン期間中、月次コスト $180 以下を維持

## 参考
- `dev-prep.md` §2
- `ROADMAP.md` M8 / M10
EOF
create_issue "[cost] バーンレート管理 (epic)" "area:cost,priority:p1,epic" "" "$TMPDIR/b13.md"

# ============ #14 ============
cat > "$TMPDIR/b14.md" <<'EOF'
## 背景
ブランチ保護と OIDC は M5 以降の任意改善項目。free-tier private repo は ruleset API 不可のため公開化後に対応。M12 まではマニュアル `az` デプロイで十分。

## チェックリスト
- [ ] **C3** ブランチ保護ルール設定（公開化後 / advisory CI で代替）
- [ ] **C4** GitHub Actions OIDC App Registration 作成
- [ ] **C4** GitHub Secrets/Vars 設定（CI デプロイ用）
- [ ] `bootstrap-verify.ps1` 実装（任意の正式サインオフ）

## 完了基準
PR が Action 経由で自動デプロイされる

## 参考
- `HANDOFF.md` §C3 / §C4
- `STATUS.md` 今週の次アクション
EOF
create_issue "[setup] CI/CD 強化（任意・後回し）" "area:setup,priority:p2,blocked" "" "$TMPDIR/b14.md"

echo ""
echo "=== Done ==="
