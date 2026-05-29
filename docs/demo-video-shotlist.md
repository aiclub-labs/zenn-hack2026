# Demo Video Shotlist — 5/31 night collection target

提出物 = 動画 (1-3 分想定)。撮影は 5/31 夜、編集 6/1 朝、提出 6/1 昼。

**前提**: `chore/demo-threshold-relax-temp` を merge + deploy 済 (= critic 7.5 まで gap 起動)。撮影後 **必ず revert** (judging 期間突入前)。

## Storyboard (90-120 秒)

### Shot 1: Tagline (5s)
- 黒画面 → タイトル `Dialogue Delta — 暗黙知を citation 必須で形式知化する`
- サブ: `Microsoft Agent Hackathon 2026 / Team aiclub-labs`

### Shot 2: Chat 1 turn — citation 表示 (15s)
- URL: `web-chat /chat`
- 質問入力: 「Power Automate で月次レポートを Teams に自動投下する手順は?」
- LLM 応答 + self-critic + citation 3 件 (w=70-85%) 表示
- **強調**: citation カードの sector#unit + weight + 詳細 button

### Shot 3: Hearout 5W1H (20s)
- 上記応答に対し「Bad」 押下 (実 demo 用には threshold 緩和済なので gap_detected=true で自動 modal)
- HearoutModal 5W1H フィールド埋め (Who/What/When/Where/Why/How)
- 「完了」 → formalization → **Discord #hack-pending-review に着弾画 (split screen)**

### Shot 4: Admin schema 編集 (15s)
- URL: `web-admin /schemas`
- 既存 field を編集 → 保存
- **Discord #hack-schema-updates に着弾画 (split screen)**
- 履歴タブで revision diff 表示

### Shot 5: Review queue + 自己承認 (15s)
- URL: `web-review`
- Shot 3 で生まれた pending ticket → Lock → Approve
- weight breakdown (a/b/c) を hover で表示
- 自己承認 KPI ダッシュボード ちらり

### Shot 6: Expired 着弾 (10s) — optional
- 別ticket を Lock → 5min 待ち (タイムラプス) → sla-cron 起動
- **Discord #hack-expired に着弾画**

### Shot 7: Cost ダッシュボード + Discord cost alert (10s)
- Azure Portal Cost analysis pane (PoC 累計 ¥1,491 → 投影 ¥14,000)
- (cost.alert は smoke 経由の表示でも可: docs/cost-model.md と並置)

### Shot 8: クロージング (5s)
- 「自社 corpus grounding + 暗黙知形式化 + citation 必須化 = ¥1,750/user/月」
- GitHub URL: aiclub-labs/zenn-hack2026
- BGM フェードアウト

## 撮影前チェックリスト

- [ ] `chore/demo-threshold-relax-temp` を main に merge + `azd deploy api`
- [ ] Cosmos に sample tacit knowledge 数件 seed 済 (seed_consultant_tacit.py 再実行)
- [ ] Review queue にダミー pending 1 件 (shot 6 用)
- [ ] OBS / Loom 録画準備、解像度 1920x1080、ブラウザ zoom 100%
- [ ] Discord は別ウィンドウ + 各チャンネル開いた状態でスタンバイ
- [ ] BGM 著作権 OK のもの (Pixabay / DOVA-SYNDROME 推奨)

## 撮影後チェックリスト

- [ ] `chore/demo-threshold-relax-temp` を **revert** + `azd deploy api`
- [ ] revert 動作確認 (新規 chat → critic 9 → gap false)
- [ ] 録画素材を `output/demo-video/` 配下に保存
