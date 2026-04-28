# Browser Automation — Portal-Only Step Wrappers

Three Playwright scripts that drive the **irreducible portal-only** steps in `azure-setup.md`. They auto-fill what they can and **pause with explicit prompts** for human actions (SMS / card / biometric / CAPTCHA).

| Script | Wraps `azure-setup.md` § | Use when |
|---|---|---|
| `playwright-signup.ts` | §2.1 — `azure.microsoft.com/free` signup form | First-time creating the AI-club Azure account ($200 credit moment) |
| `playwright-mfa-enroll.ts` | §2.1.5 — Authenticator / phone enrollment via `myaccount.microsoft.com/security-info` | Adding MFA factors when not relying solely on passkey |
| `playwright-payg-upgrade.ts` | §2.6 — Free Trial → PAYG conversion at `aka.ms/UpgradeNow` | 2026-05-26 (D9 day-28) |

## Setup (one-time)

```bash
cd scaffold/scripts/automation
bun install                   # installs Playwright + types
bun run install-browsers      # downloads chromium (~150MB)
cp .env.example .env
# edit .env — fill in profile fields, phone, address. NO secrets.
```

## Running

```bash
bun run signup    # runs playwright-signup.ts
bun run mfa       # runs playwright-mfa-enroll.ts
bun run payg      # runs playwright-payg-upgrade.ts
```

By default the browser is **headed** (you can see what's happening) and pauses await keypress at each human break-point. Set `HEADED=0` in `.env` for CI smoke tests.

## How human break-points work

When the script needs you to do something (enter SMS code, scan QR, click confirm, etc.), it:

1. Takes a screenshot to `screenshots/` (if `SCREENSHOT_ON_PAUSE=1`).
2. Prints what to do, e.g. `[PAUSE] Enter the SMS code in the form, then press Enter here.`
3. Waits for `Enter` in the terminal.
4. Resumes from the current page state.

**Never put credentials, SMS codes, or card details in `.env`** — the scripts only auto-fill non-sensitive fields. Sensitive entry happens in the browser, by you, while the script is paused.

## Resumability

Each script:
- Detects "already done" states (e.g., signup script sees an existing sub → exits with the captured IDs instead of trying to resign-up).
- Preserves browser session state in `.playwright-profile/` between runs (auto-cleaned on success). Re-running after a mid-flow crash usually resumes from where you stopped.

## Troubleshooting

| Issue | Fix |
|---|---|
| "Selected user account does not exist in tenant 'Microsoft Services'" | Sign out of all MS accounts first; use a private window. See `azure-setup.md` §10. |
| CAPTCHA appears | Solve it in the browser; script auto-detects it's gone and continues. |
| Browser closes unexpectedly | Re-run; session persists. If it loops, delete `.playwright-profile/` and restart. |
| `bun: command not found` | Install Bun: `winget install Oven-sh.Bun` (Windows) or `curl -fsSL https://bun.sh/install \| bash` (WSL/macOS). |
| Script hangs at "ready to fill" with empty form | Selectors may have drifted (Microsoft updates the form occasionally). Run with `HEADED=1`, watch which step fails, file a quick fix to the script. |

## What gets written to disk

- `.env.azure` (path configurable) — captured `TENANT_ID` and `SUB_ID` after signup. Consumed by `bootstrap-phase0.{sh,ps1}`.
- `screenshots/` — debug screenshots at break-points. Safe to delete; gitignored.
- `.playwright-profile/` — Chromium user data dir for session persistence. Gitignored.

## Trust model

These scripts:
- Run **locally on your machine**. No data sent anywhere except to `microsoft.com` / `azure.com`.
- Do not collect, log, or transmit any field you type into the browser.
- Do not store passwords or sensitive credentials anywhere on disk.
- Source code is in this directory — read before running if you don't trust it.
