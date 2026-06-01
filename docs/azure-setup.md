# Azure Setup — Single Source of Truth

> **Project status & timeline canonical sources:** [STATUS.md](./STATUS.md) (current state) · [ROADMAP.md](./ROADMAP.md) (timeline) · [INDEX.md](./INDEX.md) (navigation)
>
> This doc is the canonical **Azure infra runbook**. For whole-project state (theme decision, team blockers, weekly focus), see STATUS.md.

End-to-end guide for standing up the hackathon Azure environment. **One doc, one flow.** Every step is tagged with its automation status; every automatable step has a ready-to-run script.

Scope: tenant + subscription strategy, identity, infra-as-code provisioning, AOAI, GitOps, day-2 ops, teardown, troubleshooting.

---

## Automation legend

| Tag | Meaning | What it implies |
|---|---|---|
| 🤖 **Auto-CLI** | Pure shell, runs unattended | Wrapped in a phase script under `scaffold/scripts/` |
| 🌐 **Auto-Browser** | Playwright MCP drives the browser, with explicit human break-points for SMS / card / biometric / CAPTCHA | Wrapped in a TypeScript script under `scaffold/scripts/automation/` |
| 👤 **Manual** | Must be a human (passkey biometric, calendar reminder, judgment call) | Doc gives the instructions; no script |

---

## TL;DR Runbook (one-page)

Follow top-to-bottom. Every row maps to **one** invocation. Click into the deeper §-link only if you hit something unexpected.

| # | Status | When | Step | Tag | Invocation |
|---|---|---|---|---|---|
| 0 | ✅ done 2026-04-28 | Day 0 | Sign up at `azure.microsoft.com/free` ($200 credit + tenant + sub in one flow) — see §2.1 | 🌐 | `bun scripts/automation/playwright-signup.ts` |
| 1 | ✅ done 2026-04-28 (visual confirm via portal Cost Management → Credits) | Day 0 | Verify $200 credit landed — see §2.1 | 🤖 | `bash scripts/bootstrap-verify.sh --credit` |
| 2 | ⏳ **NEXT** | Day 0 | Rename + tag sub, invite members, sub-RBAC, tenant rename — see §2.2–2.5 | 🤖 | `pwsh scripts/bootstrap-phase0.ps1 -SubscriptionId <SUB_ID> -MemberUpns @('m1','m2','m3') -BudgetEmail <email>` |
| 3 | ⏸ skipped (passkey covers MFA) | Day 0 | (If not using passkey) Enroll Authenticator + phone backup — see §2.1.5 | 🌐 | `bun scripts/automation/playwright-mfa-enroll.ts` |
| 4 | ⏳ pending | Day 0 | Register RPs + patch parameters.json + what-if — see §3 | 🤖 | `pwsh scripts/bootstrap-phase1.ps1 -SubscriptionId <SUB_ID> -MemberUpns @('m1','m2','m3') -BudgetEmail <email>` |
| 5 | ⏳ pending | Day 0 | Provision infra (RGs, KV, Storage, CAE, LAW, AppI, RBAC, Budget, Policy) — see §4 | 🤖 | `azd env new hack2026 && azd provision` |
| 6 | ⏳ pending | Day 0 | Verify deployment — see §5 | 🤖 | `pwsh scripts/bootstrap-verify.ps1` |
| 7 | ⏳ pending | Day 0–2 | Set up GitOps (OIDC App Registration + federated credentials + `gh` config) — see §7 | 🤖 | `pwsh scripts/setup-gitops.ps1 -RepoOwner aiclub-labs -RepoName zenn-hack2026` |
| 8 | ⏳ scheduled | Day 7 (May 5) | Provision AOAI + stash keys in KV — see §6 | 🤖 | `pwsh scripts/aoai-provision.ps1 -Region <REGION>` |
| 9 | ⏳ scheduled | Day 24 (May 22) | Burn-rate check; downsize models if >$120 spent — see §8.1 | 👤 | `az consumption usage list ...` (manual review) |
| 10 | ⏳ scheduled | Day 28 (May 26) | Convert Free Trial → PAYG — see §2.6 | 🌐 | `bun scripts/automation/playwright-payg-upgrade.ts` |
| 11 | ⏳ scheduled | Day 34+ (Jun 2) | Teardown (lock removal + `azd down --purge` + KV/AOAI purge) — see §9 | 🤖 | `pwsh scripts/teardown.ps1` |

PowerShell variants: every `bash scripts/*.sh` has a `pwsh scripts/*.ps1` sibling for Windows-native WezTerm users (this team is on Windows + WezTerm + PowerShell, so the runbook above defaults to `.ps1`).

**Key dates locked (D9):** signup 2026-04-28 → AOAI 2026-05-05 → burn-check 2026-05-22 → PAYG 2026-05-26 → demo 2026-06-01 → teardown 2026-06-02.

### Session checkpoint — 2026-04-28

Stopped before step 2 (`bootstrap-phase0`). Awaiting from operator:
- `SUB_ID` of the freshly-signed-up `hack2026` Free Trial sub (`az account show --query id -o tsv`)
- 3 member UPNs (or 1 + placeholders, since phase0 is idempotent — re-run after teammates onboard)
- Budget contact email (default = AI-club Gmail used at signup)

Already done in this session:
- Toolchain installed (`az`, `azd`, `gh`, `jq`, `bicep`, `bun` — all on Windows PowerShell 7+)
- New AI-club Microsoft account → Azure Free Trial signed up → $200 credit active, Free Trial sub created (still named "Azure subscription 1" or similar, not yet renamed to `hack2026`)
- New AI-club Google account created (Gmail-based, free tier, 2FA enabled)
- New `aiclub-labs` GitHub account created (SSO via Google, 2FA verified, recovery codes saved)
- Private repo `aiclub-labs/zenn-hack2026` created, full scaffold pushed (initial commit on `main`, 77 objects / ~59 KiB)
- Personal GitHub handle `operator` added as `push` collaborator on the repo
- Branch protection: skipped (free-tier private repo blocks both classic protection and rulesets; team relies on social norms + CI for now — flip to ruleset post-demo if repo goes public, or buy GitHub Pro)
- Pre-push critical review identified 7 issues, all fixed in scaffold (Dockerfile added, bun-types→@types/bun, policy enforcementMode=DoNotEnforce, ownerObjectId conditional, .gitignore expanded, gpt-4o added to AOAI deployments, devcontainer fixed); Bicep compiles clean (zero warnings, zero errors)

Open items / not-yet-locked:
- Teammate UPNs + GitHub usernames not yet collected → step 2 can run with placeholders or be deferred
- D7 (AOAI region) still pending task #6 closure
- `hello_agent.py` needs Managed Identity auth fallback before May 5 demo wiring (S2 from review — not push-blocking, captured as TODO)
- **Business-problem selection still open** — infra is generic; the actual hackathon project (which business pain agent technology will address) has not been frozen. Existing artifacts: `idea-shortlist.md` (candidates) + `ideation-workbook.md` (法人-context constraints + scoring rubric). This is the long-pole for the next 1–2 weeks; infra build-out continues in parallel under the assumption that whatever theme wins fits the SK + MCP + AOAI + CAE stack already declared in `tech-stack-matrix.md`.

---

## 0. Decisions to lock before any `az` command

These are upstream of all infra. Locking them late causes rework.

| # | Decision | Default | Rationale |
|---|---|---|---|
| D1 | **Tenant scope** | New AI-club Entra tenant | Survives past hackathon → reusable for workshops, copilot-agent, discord-bot. Centralizes member identities. |
| D2 | **Subscription scope** | Hackathon-dedicated sub inside AI-club tenant | Hackathon credit binds to the subscription; isolates spend; clean teardown without losing tenant. |
| D3 | **Primary region** | `swedencentral` | Best AOAI model availability (gpt-4o-mini, gpt-4o, o3-mini) as of Q1 2026. Re-evaluate with task #6. |
| D4 | **Project prefix** | `hack2026` | Drives RG names (`rg-hack2026-{dev,shared,prod}`) and resource naming. Lock early — renaming is destructive. |
| D5 | **Budget ceiling** | $180/mo | Aligns with $200 hackathon credit; alerts at 80 % / 100 %. |
| D6 | **Designated Owner** | Member 1 | Single accountable Owner; others get Contributor. Subscription-Owner sprawl is the #1 cost-leak risk. |
| D7 | **AOAI provisioning timing** | ~May 4–5 (target burn-window start) | Aligns peak AOAI spend with the freshest part of the $200 / 30-day window. Region/SKU also depends on task #6 closing. |
| D8 | **GitOps cutover** | After first manual `azd up` succeeds | Don't debug OIDC and Bicep at the same time. |
| D9 | **Azure account signup timing** | **2026-04-28 (today) — hybrid plan** | The 30-day $200 timer is wall-clock from signup, can't be paused. Signing up now buys debug runway (member invites, RP registration delays, AOAI quota requests, OIDC federation) at near-zero cost — infra at idle is ~$0/day. AOAI (the actual spend) is deferred to D7 timing. Trade-off: final 4 days (May 28 – June 1) run on PAYG; expected exposure <$10 per `ideation-workbook.md:144` burn estimate. |

Capture answers in the team's kickoff notes before proceeding.

---

## 1. Prerequisites

### 1.1 Shell environment (CLI-first by policy)

This guide is **CLI-first**. Portal is used only where the underlying API is not exposed: the one-time new-Azure-account signup form (which is also where the $200 free credit is granted — see §2.1). Every other step is `az` / `azd` / `gh` / `bicep`.

Primary terminal: **WezTerm**. Inner shell options (pick one and stay):

| Shell | When to pick | Notes |
|---|---|---|
| **PowerShell 7+ (`pwsh`)** on Windows | You're on Windows-native and don't want a WSL hop | Use `;` not `&&` for chaining (or PS7 supports `&&`). All `az`/`azd` commands work identically. Every `*.sh` script in this repo has a `*.ps1` sibling for this case. |
| **WSL Ubuntu** (bash/zsh) on Windows | You want POSIX scripts unchanged | `*.sh` scripts run as-is. Recommended if you also do Linux-style dev. |
| **bash/zsh** on macOS / Linux | Native | `*.sh` scripts run as-is. |

Avoid **Git Bash** for this stack — `azd` and `az` have known PTY/path quirks under MSYS2 that don't appear in PowerShell or WSL. The previous workshop hooks already use `HOME=/c/Users/maoan` overrides because of similar Git-Bash-on-Windows env weirdness.

### 1.2 Accounts & credits 👤

**Where the $200 comes from:** it is **not** a hackathon-issued code. It is Microsoft's standard new-Azure-account credit ($200 USD, valid 30 days) that **auto-applies** when you create a brand-new Azure account at `https://azure.microsoft.com/free`. Confirmed in `overview.md` §7 (個人部門 = "$200 自動付与（Azure新規開設時）") and `action-plan.md` line 101 ("Microsoft 標準の Azure 新規サインアップ特典 → 新規開設で自動付与。ハッカソン固有の申請フロー無し"). No separate redemption flow exists.

Implications:
- The Microsoft account that signs up for Azure must be **fresh-to-Azure-paid-services** (any Microsoft account that has never had a paid Azure sub on it). If the AI-club account previously held a Pay-As-You-Go sub, the $200 will not be granted.
- ¥50,000 法人クレジット does **not** apply to 法人 (existing Microsoft alliance — `overview.md` §7 disqualifies it). Plan only on $200.
- $200 → 30-day window. Day 31 the trial sub becomes read-only unless converted to PAYG. Plan demos before day 30.

Prereq checklist:
- [ ] A Microsoft account dedicated to AI-club, with **no prior paid Azure activity** (verify by signing into `https://portal.azure.com` with it — if no subscriptions are listed, you're clean).
- [ ] A valid credit card (required by Microsoft for fraud-prevention even on the free trial; not charged until you explicitly convert to PAYG).
- [ ] A phone number that can receive SMS for the signup verification step.
- [ ] All 3 member UPNs collected. UPN ≠ display name; must be the actual `user@tenant.onmicrosoft.com` or verified domain.

### 1.3 Local toolchain (every member) 🤖

**Windows / PowerShell (recommended for this team):**
```powershell
winget install -e --id Microsoft.AzureCLI
winget install -e --id Microsoft.Azd
winget install -e --id GitHub.cli
winget install -e --id jqlang.jq
az bicep install
```

**WSL Ubuntu / Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
curl -fsSL https://aka.ms/install-azd.sh | bash
sudo apt install -y jq gh
az bicep install
```

**macOS:**
```bash
brew install azure-cli azd gh jq bicep
```

For Playwright automation scripts (§2.1, §2.1.5, §2.6), additionally install Bun:
- Windows: `winget install -e --id Oven-sh.Bun`
- WSL/Linux/macOS: `curl -fsSL https://bun.sh/install | bash`

Verify (any shell):
```bash
az version           # >= 2.60
azd version          # >= 1.10
bicep --version      # >= 0.30
gh --version         # >= 2.40 (for OIDC + repo bootstrap)
jq --version         # any
bun --version        # >= 1.1 (only if using Playwright automation)
```

### 1.4 Repo state 👤

- [ ] `scaffold/` cloned and pushed to GitHub (org-owned repo, not personal fork).
- [ ] `scaffold/infra/main.bicep` and modules unmodified from template (custom edits go in `parameters.json`).
- [ ] `.env.example` reviewed; no real secrets committed.

---

## 2. Phase 0 — Tenant + subscription bootstrap (CLI-first)

Bicep operates **inside** a subscription, so the subscription and the tenant must exist first. The CLI covers most of this; the only irreducible portal step is the **new-Azure-account signup form** (which simultaneously creates the tenant, the first subscription, and grants the $200 free credit — all in one flow, no separate steps).

### 2.0 What can vs. cannot be done via CLI

| Task | CLI-able? | Why |
|---|---|---|
| New Azure account signup ($200 credit + tenant + first sub, all bundled) | ❌ Portal-only — wrapped in 🌐 Playwright | `azure.microsoft.com/free` form requires browser: SMS verification, credit card capture, ToS click-through. No Graph/ARM API. ~10 min, one-time. |
| Invite external users to existing tenant | ✅ `az rest` (Graph `invitations`) | Full automation. |
| Create additional subscription (EA / MCA accounts) | ✅ `az account subscription create` | Only after the initial sub exists; needs billing-account permissions. Not relevant for the $200-free-trial path. |
| Convert free-trial sub to PAYG (after $200 burn) | ❌ Portal-only — wrapped in 🌐 Playwright | `https://aka.ms/UpgradeNow` flow; no API. |
| Rename / tag subscription | ✅ `az account update`, `az tag update` | |
| Subscription RBAC (Owner / Contributor) | ✅ `az role assignment create` | |
| Resolve UPN → object ID | ✅ `az ad user show` | |
| Spending limit / budget | ✅ Bicep `budget` module (declarative) | Plus the trial sub's built-in $200 cap. |
| Resource provider registration | ✅ `az provider register` | |

So Phase 0's irreducible portal surface is **one click-through**: the signup form at `https://azure.microsoft.com/free`. Everything else below is `az` / `gh` / `azd`.

### 2.1 Sign up for a new Azure account (the $200 source) 🌐

**Automation:** `bun scripts/automation/playwright-signup.ts` drives the form. Pauses at SMS / card / MFA / passkey for human input, resumes after each, captures `TENANT_ID` + `SUB_ID` to `.env.azure`.

This single signup flow creates **all four** at once: a Microsoft account → an Entra tenant → a first subscription named "Free Trial" → the $200 credit attached to it. There is no separate "redeem credit" step afterward; the credit is the *consequence* of completing this form.

**Pre-flight (do not skip):**
- Open a private/incognito window so you don't accidentally bind to your 法人 or personal Microsoft account.
- Confirm the AI-club Microsoft account has never had a paid Azure sub. Quickest test: sign into `https://portal.azure.com` first; if the "Subscriptions" blade is empty, you're clean. If you see any sub (even an old free trial that already expired), the $200 will be denied.

**Manual fallback walkthrough** (if Playwright script fails):
1. Browse to `https://azure.microsoft.com/free`. Click **Start free**.
2. Sign in with the AI-club Microsoft account (or click "Create one" to make a fresh `aiclub2026@outlook.com` first).
3. **Profile** — pick a country (drives data residency; choose Japan if billing/compliance demands it, else `swedencentral`-aligned region works fine from anywhere). Phone, then SMS code.
4. **Identity verification by card** — credit card. **Not charged**; only authorized for $1 reversal. Required even though the trial is free. The card *only* gets billed if you later explicitly opt into PAYG.
5. **Agreement** — accept the subscription agreement.
6. Form completes → portal redirects → you should immediately see the green banner: **"Your $200 credit is ready"**.

**What you got, in one motion:**
- New tenant, default domain `<somename>.onmicrosoft.com`. Microsoft picks the tenant ID.
- New subscription named **"Free Trial"** (`Microsoft Azure - Free Trial` offer). $200 credit attached.
- A new **work/school identity** in that tenant, mapped from your Microsoft-account sign-in. From this point on, every `az login` / portal sign-in goes through that work/school identity (Entra endpoint), not your personal MSA. Same email, different auth context — relevant when MFA enrollment URLs misroute (see §2.1.5).
- Your account is **Global Administrator** of the tenant + **Subscription Owner** of Free Trial.
- 30-day countdown starts.

**Capture identifiers via CLI immediately:** 🤖
```bash
az login                        # log in with the AI-club account just created
az account show --query "{name:name, id:id, tenant:tenantId, state:state}" -o table
TENANT_ID=$(az account show --query tenantId -o tsv)
SUB_ID=$(az account show --query id -o tsv)
echo "TENANT_ID=$TENANT_ID"
echo "SUB_ID=$SUB_ID"
```
Save both to the team password manager under `ai-club/azure/`.

**Confirm $200 actually landed:** 🤖 `bash scripts/bootstrap-verify.sh --credit` — or manually:
```bash
az rest --method get \
  --url "https://management.azure.com/providers/Microsoft.Billing/billingAccounts?api-version=2020-05-01"

az consumption usage list \
  --start-date $(date -u +%Y-%m-01) \
  --end-date $(date -u +%Y-%m-%d) \
  --query "length(@)" 2>/dev/null  # 0 on day 1 — expected, no spend yet
```
Or visual: `https://portal.azure.com` → Cost Management + Billing → **Credits** should show `$200.00 USD remaining`.

### 2.1.1 Root-account hygiene (treat like AWS root) 👤

The account you just created is the tenant root + billing owner. Treat it the way you treat AWS root:

- **Do not use it for daily `az login` from your laptop.** Provision a regular admin/dev user (§2.3) and switch to that for everyday CLI work.
- **Do not share its credentials.** Other 2 hackathon members come in as guests via §2.3 invitations, never with the root login.
- **Touch it only on these dates:** day-7 AOAI provision (~May 5, if it happens to need root), day-28 PAYG conversion (May 26), day-34+ teardown (June 2+).
- Passkey is sufficient MFA for this account on its own — phishing-resistant, satisfies Security Defaults. Don't burn time adding a second factor unless the passkey device is shared (it isn't, on a hackathon team).

### 2.1.5 MFA enrollment quirks (skip if using passkey) 🌐

**Automation:** `bun scripts/automation/playwright-mfa-enroll.ts` — drives `myaccount.microsoft.com/security-info` enrollment, pauses for QR-scan / biometric, then verifies via Graph CLI.

You can skip this entire section if you logged in with a passkey — passkey already counts as strong MFA at the Entra endpoint and Security Defaults will accept it. Read on only if you need to add or troubleshoot factors.

**Where to enroll MFA factors:** the **self-service** page, not the admin blade.
- ✅ `myaccount.microsoft.com/security-info` (self-service) — the only place that can register Authenticator / phone / FIDO2 / passkey on your Entra identity.
- ❌ portal.azure.com → Entra ID → Users → *user* → Authentication methods (admin blade) — the **+ Add** icon is intentionally disabled here. Microsoft deprecated admin-on-behalf-of enrollment; users must self-enroll.

**Reliable navigation to the self-service page** (avoids the home-realm-discovery loop that bounces personal-MSA emails):
1. From `portal.azure.com` (already authenticated) → click avatar top-right → **View account**.
2. New tab opens at `myaccount.microsoft.com` carrying the right tenant context.
3. Left nav → **Security info** → enroll.

If `View account` is missing, use the tenant-pinned URL:
```bash
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "https://mysignins.microsoft.com/security-info?tenantId=$TENANT_ID"
```
Open the printed URL.

**Definitive "is MFA enrolled?" check (CLI, no browser):** 🤖
```bash
az rest --method get \
  --url "https://graph.microsoft.com/v1.0/me/authentication/methods" \
  --query "value[].'@odata.type'" -o tsv
```
- Output containing only `passwordAuthenticationMethod` → not enrolled, add a method.
- Output containing `microsoftAuthenticator…`, `phone…`, `fido2…`, `softwareOath…`, or `passwordlessMicrosoftAuthenticator…` → enrolled, you're done.

**Why `aka.ms/mysecurityinfo` cold-link fails for personal-MSA emails:** Microsoft's home-realm-discovery resolves your email to the personal-MSA endpoint (login.live.com) by default, then refuses to serve work/school security info there. Tenant-pinned URL or "View account" from inside the portal sidesteps it.

### 2.2 Rename + tag the subscription, rename tenant 🤖

**Automation:** part of `bash scripts/bootstrap-phase0.sh`. Or run inline:

The auto-created sub is called "Free Trial" — rename to `hack2026` so logs and budget alerts make sense.

```bash
az account update --subscription "$SUB_ID" --name hack2026

az tag update --resource-id "/subscriptions/$SUB_ID" --operation Merge \
  --tags project=hack2026 event=microsoft-agent-hackathon-2026 managedBy=bicep

# Verify
az account show --query "{name:name, id:id}"
az tag list --resource-id "/subscriptions/$SUB_ID"
```

Optional but recommended: rename the tenant display name from the auto-generated one to "AI Club":
```bash
az rest --method patch \
  --url "https://graph.microsoft.com/v1.0/organization/$TENANT_ID" \
  --headers "Content-Type=application/json" \
  --body "{\"displayName\":\"AI Club\"}"
```
The `.onmicrosoft.com` primary domain is **not renameable** — you'd have to add a custom verified domain via `az rest` against `/domains` if you want `aiclub2026.onmicrosoft.com`-style branding. Not worth doing for a 6-week hackathon.

### 2.3 Invite the other 2 members via Microsoft Graph 🤖

**Automation:** part of `bash scripts/bootstrap-phase0.sh`. Or run inline:

The signup created a tenant with exactly one user (the AI-club account, who is now Global Admin). Invite the other 2 hackathon members as guests:

```bash
for UPN in member2@... member3@... ; do
  az rest --method post \
    --url https://graph.microsoft.com/v1.0/invitations \
    --headers "Content-Type=application/json" \
    --body "{\"invitedUserEmailAddress\":\"$UPN\",\"inviteRedirectUrl\":\"https://portal.azure.com\",\"sendInvitationMessage\":true}"
done
```

After they accept (email link), confirm:
```bash
az ad user list --query "[?mail!=null].{upn:userPrincipalName, oid:id, mail:mail}" -o table
```
Expected: 3 entries (you + 2 members). If a UPN's `id` is null, the invite hasn't been accepted yet.

### 2.4 Subscription-scoped RBAC for bootstrap 🤖

**Automation:** part of `bash scripts/bootstrap-phase0.sh`.

Bicep RBAC modules will fine-grain to RG scope, but Phase 1 needs the Designated Owner with sub-wide rights to deploy and the others as Contributors:

```bash
OWNER_OID=$(az ad user show --id member1@aiclub2026.onmicrosoft.com --query id -o tsv)
M2_OID=$(az ad user show --id member2@... --query id -o tsv)
M3_OID=$(az ad user show --id member3@... --query id -o tsv)

az role assignment create --assignee-object-id "$OWNER_OID" --assignee-principal-type User \
  --role Owner --scope "/subscriptions/$SUB_ID"

for OID in "$M2_OID" "$M3_OID"; do
  az role assignment create --assignee-object-id "$OID" --assignee-principal-type User \
    --role Contributor --scope "/subscriptions/$SUB_ID"
done

# Verify
az role assignment list --scope "/subscriptions/$SUB_ID" \
  --query "[].{role:roleDefinitionName, principal:principalName}" -o table
```

### 2.5 Verify subscription health + the $200 🤖

**Automation:** `bash scripts/bootstrap-verify.sh`.

```bash
# Sub state — should be Enabled (Free Trial subs auto-disable when credit hits $0 OR at day 30)
az account show --query "{name:name, state:state, tenant:tenantId}"

# Free-trial subs come with a built-in spending limit (sub auto-suspends at $0); confirm it's on
az rest --method get \
  --url "https://management.azure.com/subscriptions/$SUB_ID?api-version=2020-01-01" \
  --query "{name:displayName, offerType:subscriptionPolicies.spendingLimit, state:state}"
# Expected: spendingLimit="On", state="Enabled"

# Quota visibility for the target region (no resources yet, just verifies CLI access works)
az vm list-usage --location swedencentral --query "[?contains(name.value,'cores')].{name:name.localizedValue, current:currentValue, limit:limit}" -o table
```

Phase 0 exit criteria:
- New Azure account created, $200 credit visible in Cost Management → Credits.
- `TENANT_ID` and `SUB_ID` saved to vault.
- `az account show` returns `name=hack2026`, `state=Enabled`.
- Spending limit is `On` (auto-protects against accidental burn past the $200).
- `az role assignment list` shows 1 Owner + 2 Contributors at sub scope.
- `az ad user list` returns all 3 members with non-null OIDs.

### 2.6 Day-30 conversion plan (locked: hybrid for hack2026) 🌐

**Automation:** `bun scripts/automation/playwright-payg-upgrade.ts` for May-26 invocation.

Hackathon deadline: **2026-06-01**. Signup target: **2026-04-28 (today)**. Free Trial window therefore: **2026-04-28 → 2026-05-28**. Demo runs ~4 days past trial expiry on PAYG.

Per D9, the chosen path is **Convert to PAYG on day 28-29** to keep the sub continuous through demo. Card-on-file pays for May 28 – June 1 usage only (~4 days).

| Decision point | Date | Action | Tag |
|---|---|---|---|
| Day 0 (today) | 2026-04-28 | Sign up. Bootstrap infra (KV/Storage/CAE/LAW/AppI). **Do not provision AOAI.** | 🌐+🤖 |
| Day 1–6 | 2026-04-29 → 2026-05-04 | Member invites, OIDC federation, smoke-test agent skeleton against placeholder/mock LLM. | 🤖 |
| Day 7 | 2026-05-05 | Provision AOAI (per D7). File quota request same day if region rejects default. | 🤖 |
| Day 24 | 2026-05-22 | Burn-rate check: `az consumption usage list`. If >$120 spent, downsize gpt-4o → gpt-4o-mini for arbiter. | 👤 |
| Day 28 | 2026-05-26 | **Convert to PAYG** at `https://aka.ms/UpgradeNow`. Confirms card-on-file. Resources persist; spending limit lifts. | 🌐 |
| Day 30 | 2026-05-28 | $200 forfeits if not yet spent. Any remaining usage now bills the card. | (auto, no action) |
| Day 34 | 2026-06-01 | Demo. Submit. | 👤 |
| Day 34+ | 2026-06-02+ | `azd down --purge` (see §9). Kills ongoing card charges. | 🤖 |

Calendar reminders to set today: **May 4** (provision AOAI), **May 22** (burn-rate check), **May 26** (PAYG conversion), **June 2** (teardown).

Alternative paths if the hackathon shifts:

| Option | When to pick | How |
|---|---|---|
| **Stay on Free Trial; let it expire** | Demo ships before May 28 | Do nothing. Sub goes read-only at day 31; resources persist 90 days then delete. Zero card charges. |
| **Burn-and-teardown before day 30** | Demo lands May 25–27 | Teardown via `azd down --purge` (see §9) before trial expires. Cleanest accounting. |

---

## 3. Phase 1 — Imperative bootstrap 🤖

Wrapper scripts in `scaffold/scripts/`:
- `bootstrap-phase1.sh` — bash (WSL, macOS, Linux)
- `bootstrap-phase1.ps1` — PowerShell 7+ (Windows-native)

```bash
# bash (WSL inside WezTerm, or macOS/Linux)
cd scaffold
./scripts/bootstrap-phase1.sh \
  <hack2026-sub-id> \
  member1@aiclub2026.onmicrosoft.com \
  member2@... \
  member3@... \
  budget-alerts@aiclub2026.onmicrosoft.com
```

```powershell
# PowerShell 7+ (Windows-native inside WezTerm)
cd scaffold
./scripts/bootstrap-phase1.ps1 `
  -SubscriptionId <hack2026-sub-id> `
  -MemberUpns @('member1@aiclub2026.onmicrosoft.com','member2@...','member3@...') `
  -BudgetEmail budget-alerts@aiclub2026.onmicrosoft.com
```

What it does (each step idempotent — re-run safe):

1. `az login` if not cached.
2. `az account set --subscription <id>`.
3. Registers RPs: `Microsoft.App`, `Microsoft.ContainerRegistry`, `Microsoft.CognitiveServices`, `Microsoft.KeyVault`, `Microsoft.Storage`, `Microsoft.OperationalInsights`, `Microsoft.Insights`, `Microsoft.ManagedIdentity`, `Microsoft.Consumption`, `Microsoft.Authorization`. RP registration is async; first pass returns `Registering`, status flips to `Registered` within ~2 min.
4. Resolves UPNs → object IDs via `az ad user show`.
5. Patches `infra/main.parameters.json` with member OIDs, owner OID, and budget contact email using `jq`.
6. Runs `az deployment sub what-if` for review.

### 3.1 Override knobs (env vars)

| Var | Purpose | Default |
|---|---|---|
| `OWNER_OID` | Force a specific owner (else = member 1) | member1 OID |
| `AZURE_LOCATION` | Override region | `swedencentral` |

### 3.2 Manual review of `parameters.json` 👤

After the script, inspect:
```bash
jq . infra/main.parameters.json
```
Confirm:
- `memberObjectIds.value` has 3 GUIDs, no empty strings.
- `ownerObjectId.value` is one of the member OIDs.
- `budgetContactEmails.value` is a real, monitored email.
- `budgetAmount.value` matches D5.

### 3.3 What-if interpretation 👤

The what-if printout shows resources by symbol:
- `+ Create` — new resource (expected on first run).
- `~ Modify` — drift; investigate before proceeding.
- `- Delete` — should be empty on first run; non-empty means you ran it against the wrong sub.
- `= No change` — safe re-runs.

**Stop and read** any `Modify` block. Do not proceed if you see deletions you didn't expect.

Phase 1 exit criteria: what-if shows only `+ Create` for ~15 resources; no warnings about missing object IDs or invalid emails.

---

## 4. Phase 2 — Apply infrastructure (declarative) 🤖

### Option A — `azd` (recommended)

```bash
cd scaffold
azd env new hack2026
azd env set AZURE_LOCATION swedencentral
azd env set AZURE_SUBSCRIPTION_ID <hack2026-sub-id>
azd provision
```

`azd` reads `azure.yaml`, calls Bicep, and persists outputs to `.azure/hack2026/.env` for app code to consume.

### Option B — pure `az`

```bash
az deployment sub create \
  --name hack2026-bootstrap-$(date +%Y%m%d-%H%M) \
  --location swedencentral \
  --template-file infra/main.bicep \
  --parameters @infra/main.parameters.json
```

Use named deployments (timestamp suffix) so the deployment history stays readable.

### 4.1 What gets created

From `infra/main.bicep` orchestrating modules:

| Resource | Purpose | Cost note |
|---|---|---|
| `rg-hack2026-dev` | Dev workloads — agents, container apps, experiments | Tagged `env=dev` |
| `rg-hack2026-shared` | Long-lived: KV, Storage, LAW, AppI, CAE | Locked (`CanNotDelete`) |
| `rg-hack2026-prod` | Demo/showcase deploys | Empty until demo prep |
| Key Vault | Secrets (AOAI keys, GitHub tokens, etc.) | RBAC mode — no access policies |
| Storage Account | `artifacts` container; agent state, logs | LRS, HNS off, public access denied |
| Log Analytics Workspace | All app/infra logs | 30-day retention default |
| Application Insights | App-level telemetry, distributed tracing | Workspace-based |
| Container Apps Env | Hosts agent containers | Consumption tier; scales to zero |
| Subscription Budget | $180 cap, alert at 80 % / 100 % | Email to `budgetContactEmails` |
| Policy assignment | `Deny public blob access` on the sub | Blocks accidental anonymous Storage |
| RBAC | Members → Contributor on dev RG; Owner → Owner on shared RG; KV Secrets Officer + Storage Blob Data Contributor on shared resources | Least-privilege |

### 4.2 First-deploy expected duration

~6–9 min. CAE provisioning dominates; KV soft-delete propagation adds 1–2 min.

### 4.3 Post-deploy outputs 🤖

```bash
azd env get-values   # everything Bicep emitted as outputs
# or
az deployment sub show -n hack2026-bootstrap-... --query properties.outputs
```

Consumed by app code via `pyproject.toml` → `pydantic-settings` reading `.azure/hack2026/.env`.

---

## 5. Phase 3 — Verification 🤖

**Automation:** `bash scripts/bootstrap-verify.sh` runs every block below in sequence and exits non-zero on first failure.

Run all of these. Failures mean re-running `azd provision` (idempotent) or filing an issue against the Bicep modules.

```bash
# RGs exist and are tagged
az group list --tag project=hack2026 -o table

# Deployment succeeded
az deployment sub list --query "[?starts_with(name,'hack2026')].{name:name, state:properties.provisioningState}" -o table

# KV reachable + RBAC applied
KV=$(azd env get-value AZURE_KEY_VAULT_NAME)
az keyvault show -n "$KV" --query "{sku:properties.sku.name, rbac:properties.enableRbacAuthorization}"
az role assignment list --scope "$(az keyvault show -n "$KV" --query id -o tsv)" -o table

# AppInsights returning a key
APPI_CS=$(azd env get-value AZURE_APPINSIGHTS_CONNECTION_STRING)
[[ -n "$APPI_CS" ]] && echo "AppI OK"

# Storage with deny-public policy
SA=$(azd env get-value AZURE_STORAGE_ACCOUNT_NAME)
az storage account show -n "$SA" --query "{public:allowBlobPublicAccess, https:enableHttpsTrafficOnly, tls:minimumTlsVersion}"
# expect: public=false, https=true, tls=TLS1_2

# Container Apps Env ready
CAE=$(azd env get-value AZURE_CONTAINER_APPS_ENV_ID)
az containerapp env show --ids "$CAE" --query "{state:properties.provisioningState}"

# Budget visible
az consumption budget list --query "[?name=='hack2026-monthly'].{amount:amount, current:currentSpend.amount}" -o table 2>/dev/null || \
  az rest --method get --url "https://management.azure.com/subscriptions/$(az account show --query id -o tsv)/providers/Microsoft.Consumption/budgets?api-version=2023-05-01"
```

Verification exit criteria: every block returns expected values, no `Failed` provisioning states, RBAC assignments visible for all 3 members.

---

## 6. Phase 4 — Azure OpenAI (deferred-then-declarative) 🤖

**Automation:** `bash scripts/aoai-provision.sh <REGION>` — wraps §6.1–6.2.

AOAI is provisioned **after** task #6 confirms region availability for required models. Don't pre-provision in the wrong region — moving an AOAI deployment requires destroy/recreate.

### 6.1 Interim imperative provisioning

```bash
RG=rg-hack2026-shared
NAME=aoai-hack2026
LOC=<region-from-task-6>

az cognitiveservices account create \
  -g "$RG" -n "$NAME" -l "$LOC" \
  --kind OpenAI --sku S0 \
  --custom-domain "$NAME" \
  --assign-identity \
  --yes

# Model deployments — adjust SKU capacity to your hackathon credit budget
az cognitiveservices account deployment create \
  -g "$RG" -n "$NAME" \
  --deployment-name gpt-4o-mini \
  --model-name gpt-4o-mini --model-version "2024-07-18" \
  --model-format OpenAI \
  --sku-name Standard --sku-capacity 50

# NOTE: text-embedding-3-small in swedencentral does NOT offer plain `Standard` SKU
# (verified 2026-04-28 via `az cognitiveservices model list --location swedencentral`).
# Only `GlobalStandard` and `DataZoneStandard` are available — `GlobalStandard` is the right pick
# for hackathon (cheapest, no zone-pinning needed).
az cognitiveservices account deployment create \
  -g "$RG" -n "$NAME" \
  --deployment-name text-embedding-3-small \
  --model-name text-embedding-3-small --model-version "1" \
  --model-format OpenAI \
  --sku-name GlobalStandard --sku-capacity 50
```

### 6.2 Stash credentials in Key Vault (never in `.env`)

```bash
KV=$(azd env get-value AZURE_KEY_VAULT_NAME)
KEY=$(az cognitiveservices account keys list -g "$RG" -n "$NAME" --query key1 -o tsv)
ENDPOINT=$(az cognitiveservices account show -g "$RG" -n "$NAME" --query properties.endpoint -o tsv)

az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-API-KEY --value "$KEY"
az keyvault secret set --vault-name "$KV" --name AZURE-OPENAI-ENDPOINT --value "$ENDPOINT"
```

### 6.3 Lift to Bicep (TODO after 6.1 stabilizes)

Create `infra/modules/openai.bicep`:
- `Microsoft.CognitiveServices/accounts` (kind: `OpenAI`, sku: `S0`, public network = disabled if VNet-injected)
- `Microsoft.CognitiveServices/accounts/deployments` per model
- KV secret references via `Microsoft.KeyVault/vaults/secrets`
- RBAC: `Cognitive Services OpenAI User` to member OIDs

Wire into `main.bicep` after the `shared` module. Run `azd provision` — it converges to declared state, removing imperative drift.

### 6.4 App code: managed identity > API keys

In Container Apps, prefer:
```python
from azure.identity import DefaultAzureCredential
from openai import AzureOpenAI
client = AzureOpenAI(
    azure_endpoint=settings.azure_openai_endpoint,
    azure_ad_token_provider=...,  # DefaultAzureCredential().get_token("https://cognitiveservices.azure.com/.default")
    api_version="2024-08-01-preview",
)
```
API keys remain available for local dev only.

---

## 7. Phase 5 — GitOps with OIDC federation 🤖

**Automation:** `bash scripts/setup-gitops.sh <REPO_OWNER> <REPO_NAME>` wraps §7.1 + §7.2 in one shot.

Cut over **only after** a manual `azd up` succeeds. Goal: `infra/` changes deploy via PR + merge, no long-lived secrets in GitHub.

### 7.1 One-time federation setup

```bash
APP_NAME=ghactions-hack2026
SUB_ID=$(az account show --query id -o tsv)
TENANT_ID=$(az account show --query tenantId -o tsv)

# 1. App Registration
APP_ID=$(az ad app create --display-name "$APP_NAME" --query appId -o tsv)
az ad sp create --id "$APP_ID"
SP_OID=$(az ad sp show --id "$APP_ID" --query id -o tsv)

# 2. Federate to GitHub repo — pass JSON inline so this works in bash AND pwsh
REPO_OWNER=<org>
REPO_NAME=<repo>

az ad app federated-credential create --id "$APP_ID" \
  --parameters "{\"name\":\"github-main\",\"issuer\":\"https://token.actions.githubusercontent.com\",\"subject\":\"repo:${REPO_OWNER}/${REPO_NAME}:ref:refs/heads/main\",\"audiences\":[\"api://AzureADTokenExchange\"]}"

# Second FIC for PR builds (what-if only, separate workflow, least privilege)
az ad app federated-credential create --id "$APP_ID" \
  --parameters "{\"name\":\"github-pr\",\"issuer\":\"https://token.actions.githubusercontent.com\",\"subject\":\"repo:${REPO_OWNER}/${REPO_NAME}:pull_request\",\"audiences\":[\"api://AzureADTokenExchange\"]}"

# 3. Grant Contributor on the sub
az role assignment create --assignee "$SP_OID" --role Contributor --scope "/subscriptions/$SUB_ID"
# Plus User Access Administrator if RBAC modules are part of the deploy
az role assignment create --assignee "$SP_OID" --role "User Access Administrator" --scope "/subscriptions/$SUB_ID"
```

### 7.2 GitHub configuration (via `gh` CLI — no portal)

```bash
REPO=<org>/<repo>

# Variables (non-sensitive)
gh variable set AZURE_CLIENT_ID         --repo "$REPO" --body "$APP_ID"
gh variable set AZURE_TENANT_ID         --repo "$REPO" --body "$TENANT_ID"
gh variable set AZURE_SUBSCRIPTION_ID   --repo "$REPO" --body "$SUB_ID"
gh variable set AZURE_LOCATION          --repo "$REPO" --body "swedencentral"

# Secrets (sensitive — JSON-typed values)
gh secret set MEMBER_OBJECT_IDS     --repo "$REPO" --body "[\"$M1_OID\",\"$M2_OID\",\"$M3_OID\"]"
gh secret set OWNER_OBJECT_ID       --repo "$REPO" --body "$OWNER_OID"
gh secret set BUDGET_CONTACT_EMAILS --repo "$REPO" --body "[\"budget-alerts@aiclub2026.onmicrosoft.com\"]"

# Verify
gh variable list --repo "$REPO"
gh secret list   --repo "$REPO"
```

### 7.3 Workflows

`.github/workflows/infra-ci.yml` — runs on PRs touching `infra/**`:
- `azure/login@v2` with OIDC
- `bicep build` + `bicep lint`
- `az deployment sub what-if` — output posted as PR comment

`.github/workflows/infra-deploy.yml` — runs on merge to `main`:
- Same OIDC login
- `az deployment sub create` with named deployment

Verify by opening a no-op PR (touch a comment in `main.bicep`); CI should run, post what-if showing 0 changes, then merge → deploy completes in <1 min.

---

## 8. Phase 6 — Day-2 operations

### 8.1 Cost monitoring (do this weekly) 👤

```bash
# Burn rate
az consumption usage list --start-date $(date -d '7 days ago' +%Y-%m-%d) --end-date $(date +%Y-%m-%d) \
  --query "[].{date:usageStart, service:meterDetails.serviceName, cost:pretaxCost}" -o table | \
  sort -k3 -nr | head -20
```
Largest spenders to watch: AOAI tokens, Container Apps active replicas, Log Analytics ingestion.

Cost levers (in order of effort):
1. AOAI: lower `--sku-capacity`, switch demos to gpt-4o-mini.
2. CAE: set `minReplicas: 0` on dev container apps.
3. LAW: drop retention to 7 days for dev (`az monitor log-analytics workspace update --retention-time 7`).
4. Storage: move artifacts to Cool tier after demo.

### 8.2 Secret rotation 🤖

KV soft-delete is enabled (90 days). To rotate:
```bash
az keyvault secret set --vault-name "$KV" --name <name> --value <new-value>
# old version stays as history; reference by version-less URI in app code so rotation is transparent
```
AOAI key rotation:
```bash
az cognitiveservices account keys regenerate -g rg-hack2026-shared -n aoai-hack2026 --key-name Key1
# then update KV secret
```

### 8.3 Scaling agent workloads 🤖

Container Apps revisions:
```bash
az containerapp revision list --name <app> --resource-group rg-hack2026-dev -o table
az containerapp update --name <app> --resource-group rg-hack2026-dev \
  --min-replicas 1 --max-replicas 5 --scale-rule-name http --scale-rule-http-concurrency 30
```

### 8.4 Logs & traces 🤖

```bash
# Last hour of agent traces
az monitor app-insights query \
  --apps "$(azd env get-value AZURE_APPINSIGHTS_NAME)" \
  --analytics-query "traces | where timestamp > ago(1h) | take 50"

# Container app stdout
az containerapp logs show --name <app> --resource-group rg-hack2026-dev --follow
```

---

## 9. Phase 7 — Teardown 🤖

**Automation:** `bash scripts/teardown.sh` wraps the entire ordered cleanup.

Order matters: locks first, then resources.

```bash
# 1. Drop the shared-RG delete-lock (Bicep declares it; this is the one imperative undo)
az lock delete --name nodelete-shared -g rg-hack2026-shared

# 2. AOAI custom domain reservation — release before teardown (else 24h waiting period to reuse)
az cognitiveservices account delete -g rg-hack2026-shared -n aoai-hack2026
az cognitiveservices account purge -l swedencentral -g rg-hack2026-shared -n aoai-hack2026

# 3. Full teardown
azd down --purge
# or
az group delete -n rg-hack2026-dev --yes --no-wait
az group delete -n rg-hack2026-shared --yes --no-wait
az group delete -n rg-hack2026-prod --yes --no-wait
az keyvault purge --name "$KV" --location swedencentral
```

`--purge` is critical: KV and AOAI both have soft-delete which blocks namespace reuse for 90 days otherwise.

Verify cleanup:
```bash
az group list --tag project=hack2026   # expect: []
az keyvault list-deleted --query "[?name=='$KV']"  # expect: []
```

---

## 10. Troubleshooting matrix

| Symptom | Likely cause | Fix |
|---|---|---|
| `RegistrationRequiredForResourceProvider` | RP not registered on sub | Re-run Phase 1 step 3, wait 2 min |
| `RoleAssignmentExists` on `azd provision` | Re-running over existing assignments | Safe to ignore — Bicep is idempotent on RBAC |
| `KeyVaultNameNotAvailable` | Soft-deleted KV with same name | `az keyvault purge --name <name>` then retry |
| `InvalidTemplateDeployment` referencing AOAI region | Region in params doesn't host the model | Cross-check at https://learn.microsoft.com/azure/ai-services/openai/concepts/models#standard-deployment-model-availability |
| GitHub Actions: `AADSTS70021: No matching federated identity record` | FIC subject mismatch | Match exactly: `repo:<org>/<repo>:ref:refs/heads/main` (case-sensitive) |
| GitHub Actions: `AuthorizationFailed` on `Microsoft.Authorization/roleAssignments` | SP missing `User Access Administrator` | Grant via §7.1 |
| Budget alerts not firing | Email in spam, or contact email mistyped | Check `parameters.json`, re-deploy budget module |
| AOAI returns 429 immediately | Quota = 0 in this region | Open quota request via portal; can take 24h |
| `azd provision` hangs on CAE | Region capacity issue | Try alternate region or wait; check status.azure.com |
| `aka.ms/mysecurityinfo` redirects to "personal account" error | Home-realm-discovery routed to MSA endpoint | Use tenant-pinned URL or portal avatar → View account (see §2.1.5) |
| Signup form: "We can't create a subscription with this account" | MS account already had a paid Azure sub | Use a different MS account; can't be unblocked |
| Playwright signup script: timeout on SMS step | Human didn't enter SMS code in time | Re-run; script resumes from current page state |

---

## 11. Security checklist

- [ ] No secrets in `parameters.json` (only OIDs and emails).
- [ ] No secrets in repo (`.env.example` is template only).
- [ ] KV in RBAC mode (not access policies) — confirmed in Phase 3 verification.
- [ ] Storage public blob access denied (policy module enforces).
- [ ] HTTPS-only + TLS 1.2 minimum on Storage.
- [ ] Subscription Owner count = 1 (Designated Owner only); others Contributor.
- [ ] OIDC federation scoped to specific repo + branch (not org-wide).
- [ ] App code uses Managed Identity > API keys where the service supports it (AOAI, KV, Storage all do).
- [ ] AppI has no PII in custom telemetry (review before demo).
- [ ] Pre-demo: rotate any keys that ever touched a developer laptop.
- [ ] Root-account hygiene followed: not used for daily `az login`, not shared (§2.1.1).

---

## 12. Open items (track in `dev-prep.md` / GitHub issues)

- [ ] Decision D7 (AOAI region) — blocked on task #6.
- [ ] Phase 5 GitOps cutover — schedule after first manual deploy lands cleanly.
- [ ] `infra/modules/openai.bicep` — to be authored once D7 closes.
- [ ] `infra/teardown.bicep` — currently relies on `azd down`; consider explicit teardown template for CI smoke tests.
- [ ] Quota request for AOAI — file as soon as region is confirmed (24h lead time).

---

## References

- Scaffold infra: `scaffold/infra/main.bicep` and `scaffold/infra/modules/`
- Scaffold scripts: `scaffold/scripts/` (CLI wrappers) + `scaffold/scripts/automation/` (Playwright MCP)
- Action plan: `action-plan.md`
- Tech stack rationale: `tech-stack-matrix.md`
- $200 credit source: `overview.md` §7, `action-plan.md` line 101
