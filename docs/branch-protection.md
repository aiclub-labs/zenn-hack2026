# Branch protection (GitHub repo setup)

Apply these once the GitHub repo is created. Browser path:
`Settings → Branches → Add rule`.

## `main`

- [x] Require pull request before merging
  - Required approvals: **1** (3-person team — solo block on each other is overkill)
  - Dismiss stale approvals on new commits
- [x] Require status checks to pass before merging
  - `ci / lint-test`
  - `infra-ci / validate` (only required when infra files changed; GitHub auto-skips when path filter excludes)
- [x] Require branches to be up to date before merging
- [x] Require linear history
- [ ] Require signed commits (optional; skip if it slows the team down)
- [x] Do not allow bypassing the above settings (apply to admins too)
- [x] Restrict deletions

## `develop`

Same as `main` minus "linear history" — rebases on `develop` are fine.

## OIDC for `infra-deploy.yml`

The deploy workflow uses `id-token: write` with `azure/login@v2`. To enable:

1. Browser: Azure Portal → Microsoft Entra ID → App registrations → New registration
   - Name: `gh-actions-hack2026-deploy`
   - Supported account types: single tenant
2. App → Certificates & secrets → Federated credentials → Add credential
   - Issuer: `https://token.actions.githubusercontent.com`
   - Subject: `repo:<org>/<repo>:ref:refs/heads/main`
   - Audience: `api://AzureADTokenExchange`
3. Subscription → IAM → grant the App `Contributor`
4. GitHub repo → Settings → Secrets and variables → Actions
   - Variables: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `AZURE_LOCATION=swedencentral`
   - Secrets: `MEMBER_OBJECT_IDS` (JSON array string), `OWNER_OBJECT_ID`, `BUDGET_CONTACT_EMAILS` (JSON array string)

## Secret hygiene checklist

- [ ] `.env` is in `.gitignore` (verified)
- [ ] No `AZURE_OPENAI_API_KEY` ever committed — use Key Vault refs
- [ ] PR template reminds reviewers to scan for accidental secrets
