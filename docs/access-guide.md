# アクセスガイド — GitHub & Azure

ハッカソンで使用する共有リソースに、GUI（ブラウザ／ポータル）と CLI の両方からアクセスする方法をまとめます。

## リソース一覧

| システム | リソース | 必要な権限 |
|---|---|---|
| GitHub | `aiclub-labs/zenn-hack2026`（プライベートリポジトリ） | コラボレーターとして招待された GitHub アカウント |
| Azure | サブスクリプション `2c29a97c-08b6-4bc3-88ea-266eb1cfd730` | テナント `tenant-redacted.onmicrosoft.com` のゲストユーザー |
| Azure | リソースグループ `rg-hack2026-dev` | Contributor |
| Azure | リソースグループ `rg-hack2026-shared` | Storage Blob Data Contributor |
| Azure | リソースグループ `rg-hack2026-prod` | （チームアクセスなし。オーナー専用） |

## 現在のメンバー

UPN サフィックスはすべて `@tenant-redacted.onmicrosoft.com` です。

| 名前 | GitHub | Azure UPN（プレフィックス部分） |
|---|---|---|
| Mao（オーナー） | `operator` | `tenant-redacted_gmail.com#EXT#` |
| Mao（テスト用） | — | `operator_gmail.com#EXT#` |
| member-b | `member-b` | `member-b_gmail.com#EXT#` |
| member-a | `member-a` | `member-a_outlook.com#EXT#` |

---

## GitHub

### GUI からのアクセス
1. メールに届いたコラボレーター招待を承諾するか、`https://github.com/aiclub-labs/zenn-hack2026/invitations` を開いて承諾します。
2. リポジトリ URL: `https://github.com/aiclub-labs/zenn-hack2026`
3. クローン: 緑色の **Code** ボタン → HTTPS の URL をコピーして `git clone` してください。

### CLI からのアクセス
```bash
# GitHub CLI のインストール: https://cli.github.com/
gh auth login           # ブラウザでログイン
gh auth status          # ログイン中アカウントの確認
gh repo clone aiclub-labs/zenn-hack2026
gh api repos/aiclub-labs/zenn-hack2026/collaborators -q '.[].login'   # アクセス権を持つユーザー一覧
```

複数アカウント運用の場合: 個人 GitHub アカウントも併用しているなら `gh auth switch` で切り替え可能です。

---

## Azure

### 初回のみ: テナント招待を承諾
1. `invites@microsoft.com` から届く招待メール（件名にテナント名 `tenant-redacted` が含まれます）を開きます。
2. 個人の Google／メールアカウントでサインインすると、テナントにゲストユーザーとして登録されます。
3. 同意プロンプトが出たら承認します。

### GUI（Azure Portal）
1. `https://portal.azure.com` を開きます。
2. 右上のアカウントメニュー → **ディレクトリの切り替え** → `tenant-redacted (Default Directory)` を選択。
3. **サブスクリプション** → `Azure subscription 1` → **リソースグループ** → `rg-hack2026-dev` を開きます。
4. ここから Contributor 権限の範囲内でデプロイ・ログ確認・リソース編集が可能です。

ストレージ（データプレーン）の場合:
- `rg-hack2026-shared` → ストレージアカウント → **コンテナー** から Blob のアップロード／ダウンロードができます。

### CLI（azure-cli）
```bash
# インストール: https://learn.microsoft.com/cli/azure/install-azure-cli
az login                                                          # ブラウザでログイン
az account set --subscription 2c29a97c-08b6-4bc3-88ea-266eb1cfd730
az account show                                                   # 現在のコンテキスト確認

# リソース確認
az group list -o table
az resource list -g rg-hack2026-dev -o table

# 自分に付与されているロールを確認
az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --all -o table
```

`az login` が別テナントに入ってしまう場合:
```bash
az login --tenant tenant-redacted.onmicrosoft.com
```

### CLI（azd — Azure Developer CLI）
スキャフォールドからの一括プロビジョニング／デプロイで使用します。
```bash
azd auth login
azd env new hack2026-dev
azd env set AZURE_SUBSCRIPTION_ID 2c29a97c-08b6-4bc3-88ea-266eb1cfd730
azd env set AZURE_LOCATION japaneast
azd up                  # プロビジョン + デプロイ
azd down                # 削除（ティアダウン）
```

### ストレージのデータプレーン（azcopy / az storage）
Azure AD ベースの RBAC で認証するため、アカウントキーは不要です。
```bash
az storage blob list --account-name <storage-name> --container-name <container> --auth-mode login -o table
azcopy login
azcopy copy ./local-file "https://<storage-name>.blob.core.windows.net/<container>/"
```

---

## 自分のアクセス権を確認する

```bash
# GitHub
gh auth status
gh repo view aiclub-labs/zenn-hack2026

# Azure
az account show
az group show -n rg-hack2026-dev -o table
```

いずれかが失敗する場合は、エラーメッセージを添えて Discord で Mao に連絡してください。

---

## 新規メンバーの追加（オーナー専用）

GitHub:
```bash
gh api -X PUT repos/aiclub-labs/zenn-hack2026/collaborators/<github-username> -f permission=push
```

Azure（テナント招待 + ロール付与）:
```bash
# 1. テナントへの招待
az rest --method post \
  --uri "https://graph.microsoft.com/v1.0/invitations" \
  --body '{"invitedUserEmailAddress":"<email>","inviteRedirectUrl":"https://portal.azure.com"}'

# 2. 招待承諾後、オブジェクト ID を取得
OBJ_ID=$(az ad user show --id "<#EXT# 付きの UPN>" --query id -o tsv)
SUB=2c29a97c-08b6-4bc3-88ea-266eb1cfd730

# 3. REST API でロールを付与
#    （`az role assignment create` は MissingSubscription エラーで失敗するため REST を使用）
GUID=$(python -c "import uuid; print(uuid.uuid4())")
CONTRIB=b24988ac-6180-42a0-ab88-20f7382dd24c
az rest --method put \
  --uri "https://management.azure.com/subscriptions/$SUB/resourceGroups/rg-hack2026-dev/providers/Microsoft.Authorization/roleAssignments/$GUID?api-version=2022-04-01" \
  --body "{\"properties\":{\"roleDefinitionId\":\"/subscriptions/$SUB/providers/Microsoft.Authorization/roleDefinitions/$CONTRIB\",\"principalId\":\"$OBJ_ID\",\"principalType\":\"User\"}}"
```

`rg-hack2026-shared` も同じ流れで、ロール定義 ID を `ba92f5b4-2d11-453d-a403-e96b0029c9fe`（Storage Blob Data Contributor）に置き換えて実行します。

## 監査（誰がどこにアクセスできるかの確認）

```bash
# ハッカソン用 RG にスコープされた Azure ロール一覧
az role assignment list --all \
  --query "[?contains(scope, 'rg-hack2026')].{principal:principalName, role:roleDefinitionName, scope:scope}" \
  -o table

# テナント内の全ユーザー
az ad user list --query "[].{name:displayName, upn:userPrincipalName}" -o table

# GitHub リポジトリのコラボレーター一覧
gh api repos/aiclub-labs/zenn-hack2026/collaborators -q '.[].login'
```
