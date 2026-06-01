# 審査員向けアクセスガイド — Dialogue Delta

## 1. 成果物 URL

<https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/>

## 2. サインイン

上記 URL を開くと **Microsoft サインイン画面** に自動リダイレクトされます。

### 使えるアカウント

multi-tenant + 個人 MSA で設定しているため、以下いずれも利用可能:

- 組織アカウント (例: `*@*.onmicrosoft.com`, `*@<your-tenant>.com`)
- 個人 Microsoft アカウント (`*@outlook.com`, `*@hotmail.com`, `*@live.com` 等)

### 同意画面 (初回のみ)

サインイン直後に「このアプリ Dialogue Delta Demo が以下にアクセス」という画面が出ます。求めている権限:

| Scope | 内容 |
|---|---|
| `openid` | 「あなたが誰か」を確認 |
| `profile` | 表示名 / 基本プロフィール |
| `email` | メールアドレス |

→ **データアクセス系 (Outlook 本文 / Teams / OneDrive 等) は一切要求しません**。最小権限の認証情報のみ。承認して進めてください。

2 回目以降のサインインでは同意画面は出ません。

## 3. サインアウト

`https://ca-hack2026-dev-web-chat.victoriousbeach-c5de1386.swedencentral.azurecontainerapps.io/.auth/logout` にアクセスでクリアできます。

## 4. アプリ内の動線

サインイン後の画面構成:

| Route | 用途 |
|---|---|
| `/chat` | 業務ユーザー向け対話 (gpt-5、citation 自動表示、低自信時 hearout) |
| `/admin/schemas` | スキーマ定義 (Excel 数式 / Power Query レシピ / 等) の追加 / 編集 |
| `/review` | レビュアーキュー (gap → hearout → 承認 → corpus 反映) |
| `/popular` | Ranking (Good/Bad 投票で人気ノウハウを可視化) |

ヘッダーの Combobox で sector / unit / user を切替可能 (例: `general / general / haruka@example.com`)。デモ動画と同じテナントで触ると挙動が一致します。

## 5. トラブルシュート

| 症状 | 原因 / 対処 |
|---|---|
| 「**管理者承認が必要です**」(AADSTS501) | 一部組織で個人レベル consent を禁止しているケース。**個人 MS アカウント (outlook.com 等)** で再度お試しください |
| サインイン後ループ | ブラウザの cookie / cache をクリアして再アクセス |
| AI 応答が返らない (timeout) | Container Apps の scale-to-zero による cold start。30 秒待って再送信 |
| 「Microsoft アカウントが見つかりません」 | Entra と無関係の Google アカウント等は使えません。MS アカで再試行 |
| 503 / 502 | revision 切替中など一時的な問題。1 分待って再アクセス |

## 6. 認証アーキテクチャ (補足)

| 層 | 仕組み |
|---|---|
| **UI (Web Chat) Container App** | Microsoft Easy Auth (Microsoft Identity Provider) で全 path 保護、未認証 → MS login へリダイレクト |
| **Entra アプリ登録** | sign-in audience = `AzureADandPersonalMicrosoftAccount` (multi-tenant + 個人 MSA) |
| **API Container App** | ingress = **internal-only**。外部 FQDN は存在せず、UI の nginx 経由でのみ呼べる |
| **データ層 (Cosmos / AI Search)** | `pk eq '{sector}#{unit}'` を全 query に強制、partition key で構造的にテナント隔離 |

詳細経緯は [Zenn 記事 §「工夫したところ g」 + §「ハマったところ H5」](../articles/dialogue-delta-hack2026.md) を参照。

## 7. 何かあれば

- リポジトリ Issue: <https://github.com/aiclub-labs/zenn-hack2026/issues>
- 提出フォーム経由のコンタクト
