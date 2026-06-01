# 0001 — Easy Auth (multi-tenant + MSA) + Internal API Ingress

- **日付**: 2026-06-01 (提出 ~24h 前)
- **状態**: 採択 (デプロイ反映済)
- **意思決定者**: 提出担当 (operator)
- **関連**: README §「審査員の方へ」, [docs/access-for-judges.md](../docs/access-for-judges.md), Zenn 記事 §「工夫したところ g」§「ハマったところ H5」

## 背景

提出 24h 前にハッカソンルールを再確認。

- 必須: 成果物 URL (審査員アクセス可能) + Zenn 記事 + デモ動画埋込
- 既存状態: `DEV_SKIP_AUTH=true`、UI / API とも external ingress、URL を知っていれば誰でも素通り

リスク再評価:

1. **AOAI コスト爆発** — URL 露出時 1 request ~$0.01-0.1。1000 req で $100 規模、Mao の Azure 残高に直撃
2. **seed データ閲覧** — consultant tacit のサンプルのみだが、第三者が触れる
3. **bot 攻撃** — 連続 request で AOAI rate limit を即枯渇 → 審査員アクセスが不可になる

「公開 URL のままで放置」は提出締切後の精算でも問題化しうる。一方、本格 RBAC を 24h で組むのは過剰。

## 候補

| | 案 | 工数 | 強度 |
|---|---|---|---|
| A | Container Apps Easy Auth (Microsoft IdP, multi-tenant + MSA) | 30 分 | ★★★ |
| B | nginx Basic Auth (judge 用 ID/PW を Zenn に記載) | 30 分 | ★★ |
| C | Container Apps Entra Easy Auth + 招待 (single-tenant) | 1h+ | ★★★★ (過剰) |
| D | 何もしない (公開のまま) | 0 | ★ |

## 決定

**A** を採用 + **API ingress を internal-only** に変更し、Easy Auth + 物理的ネットワーク境界の二段構え。

### 理由

1. **A の judge 体験が最良**: 招待・ゲスト登録不要、任意の MS アカで sign in
2. **multi-tenant + MSA** にすれば、組織アカ・個人アカ双方をカバー
3. **internal API ingress** で外部攻撃面を物理消滅、UI 内部の nginx proxy 経由のみ
4. Microsoft Hackathon という文脈に Microsoft sign-in は文脈的にも整合
5. 認証コードを書かないので保守負担ゼロ。Phase 2 で Entra `app_role` claim を持ち込む際の足場にもなる

## トレードオフ / 既知の制約

- Easy Auth は「ログインしてれば通す」だけで、Persona A/B/C のロール分離は未実装 (sector/unit/user 切替は誰でもできる)
- internal API への nginx proxy が http (TLS 終端は ingress 側)、Container Apps Environment 内通信なので許容
- 一部組織テナントで個人レベル consent が禁止されている場合、組織アカでは弾かれる → judge ガイドで「個人 MS アカ fallback」を明記
- DEV_SKIP_AUTH=true は API 側にまだ残っており、UI 経由なら任意 user_id で操作可能 (post-提出 TODO: app_role claim から user_id を導出)

## 実装メモ

```bash
# Entra app 登録 (multi-tenant + MSA)
APP_ID=$(az ad app create \
  --display-name "Dialogue Delta Demo (hack2026)" \
  --sign-in-audience AzureADandPersonalMicrosoftAccount \
  --web-redirect-uris "https://ca-hack2026-dev-web-chat.<env>.azurecontainerapps.io/.auth/login/aad/callback" \
  --query appId -o tsv)
az ad app update --id $APP_ID --enable-id-token-issuance true
CLIENT_SECRET=$(az ad app credential reset --id $APP_ID --years 2 --query password -o tsv)

# Easy Auth bind
az containerapp auth microsoft update \
  --name ca-hack2026-dev-web-chat \
  --resource-group rg-hack2026-dev \
  --client-id $APP_ID \
  --client-secret $CLIENT_SECRET \
  --tenant-id common \
  --yes
az containerapp auth update \
  --name ca-hack2026-dev-web-chat \
  --resource-group rg-hack2026-dev \
  --unauthenticated-client-action RedirectToLoginPage \
  --redirect-provider azureactivedirectory

# API を internal に切替 + UI の nginx を internal FQDN に向ける + 再ビルド + デプロイ
az containerapp ingress update -n ca-hack2026-dev-api -g rg-hack2026-dev --type internal
# (ui/chat/nginx.conf 編集 + ACR build + containerapp update)
```

## 検証

| | 期待 | 結果 |
|---|---|---|
| 未認証で UI URL アクセス | login.microsoftonline.com にリダイレクト | ✅ HTTP 302 → 200 確認 |
| 外部から API URL 直叩き | DNS / ingress で到達不可 | ✅ 404 (Front Door 側で reject) |
| UI 内部から `/turn` 呼出 | nginx proxy で internal API へ届く | ✅ ログインユーザで chat 応答返却 |

## 後の TODO

- Bicep / azd config に Easy Auth を IaC 化 (現状 portal/CLI 手動)
- AOAI quota cap / 日次 cost alert を `az consumption` 経由か portal で設定
- Persona A/B/C を Entra `app_role` に対応させ、`/admin/*` `/review/*` のアクセスを claim-based gating
