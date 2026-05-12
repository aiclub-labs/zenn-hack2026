# GitHub Actions → Discord 通知セットアップ

Reusable workflow `_notify-discord.yml` を 4 つの workflow から呼び、Discord に成功/失敗を post する。

## 一度きりの operator 設定

### 1. Discord で webhook 作成

1. Discord で `#hack-dev-log` を右クリック → Edit Channel → Integrations → Webhooks → New Webhook
2. 名前: `GitHub Actions`、アバター: 任意
3. **Copy Webhook URL** で URL を取得（形式: `https://discord.com/api/webhooks/<id>/<token>`）

> 既存 `#github-feed` の webhook（GitHub repo events 用）とは別に作る。チャンネル別 = 用途別で混線を避ける。

### 2. GitHub Secrets に登録

```bash
gh secret set DISCORD_NOTIFY_WEBHOOK_URL \
  --repo aiclub-labs/zenn-hack2026 \
  --body 'https://discord.com/api/webhooks/.../...'
```

### 3. （任意）失敗時メンション用の variable

`infra-deploy` 失敗時に operator にメンションしたい場合:

```bash
# Discord で開発者モード ON → 自分のユーザーアイコン右クリック → ユーザーID をコピー
gh variable set DISCORD_OPERATOR_MENTION \
  --repo aiclub-labs/zenn-hack2026 \
  --body '<@123456789012345678>'
```

ロール宛なら `<@&ROLE_ID>` の形（`Hackathon Team` ロール ID は `npm run inspect` 出力から取得可能）。

## 動作確認

- 任意の PR を作成 → `ci` / `infra-ci` が走る → `#hack-dev-log` に embed で結果通知
- `main` への push で `infra/` を変更 → `infra-deploy` 完了後 `#hack-dev-log` に通知（失敗時 `DISCORD_OPERATOR_MENTION` がメンション）
- 任意の Issue/PR コメントに `@claude` → `claude-code` workflow 完了後 `#hack-dev-log` に通知

`DISCORD_NOTIFY_WEBHOOK_URL` が未設定の場合は notify ジョブが skip メッセージを出すだけで failure 化しない。

## 廃止/復旧

通知をオフにしたい時は GitHub Secret を空文字に更新するか削除。各 caller workflow の `notify` ジョブが no-op 化する。
