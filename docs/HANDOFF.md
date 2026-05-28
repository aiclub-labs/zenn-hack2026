# Hand-off — what's left for you (browser / iPad / phone)

> 📌 **進行中タスクは GitHub Issues 管理**: https://github.com/aiclub-labs/zenn-hack2026/issues — このファイルは背景情報・ランブック用。新規タスクは Issue を切ること。

> **Project status & timeline canonical sources:** [STATUS.md](./STATUS.md) (current state) · [ROADMAP.md](./ROADMAP.md) (timeline) · [INDEX.md](./INDEX.md) (navigation)
>
> このドキュメントは **operator が手動で実行する必要があるブラウザ/ポータル作業** のチェックリスト。critical-path 日付は ROADMAP.md にある。

Updated: 2026-04-28. Companion to `dev-prep.md` and `azure-setup.md`.

Everything below requires your auth or is browser/portal-only — it can't be automated locally. iPad-friendly where noted.

## A. Hackathon entry (no compute needed)

- [ ] **A1 — Zenn entry form** (KPMG名義・法人部門) — [ipad-ok]
  - One person submits as team rep
  - Confirms 5/14 entry-session invite + receives the "成果物提出フォーム" URL by email
  - File the confirmation email somewhere shared
- [ ] **A2 — Reserve `ai-club` Zenn org handle** — [ipad-ok]
  - Check availability first; fall back to e.g. `kpmg-ai-club` or `aiclub-jp`
  - Hold off on full org creation until social check #2 confirms KPMG branding is OK
- [ ] **A3 — Internal-confirmation follow-ups** (4 still open: 表記 / 登壇 / IP / 利益相反) — [ipad-ok]
  - Owner: marketing-channel contact
  - Block none of A1/B/C — none of those publish anything externally yet

## B. Azure account creation (browser-only) — ✅ DONE 2026-04-29

- [x] **B1** Sub `hack2026` (`2c29a97c-08b6-4bc3-88ea-266eb1cfd730`), Free Trial, region `swedencentral`, backed by operator's personal-Gmail MSA per project memory
- [x] **B2** $200 credit confirmed in Cost Management → Credits (verified 2026-04-28)
- [x] **B3** All 3 members in tenant: operator (member, Owner) + sotaroo.ai@outlook.com (guest, PendingAcceptance) + arumakan.34@gmail.com (guest, PendingAcceptance). Both guests' invitations dispatched 2026-04-29 11:04 UTC. ⚠️ **2026-05-05 訂正**: Sotaro の正しいアドレスは `outlook.com`（旧 `outlook.jp` で発送した招待は無効 — 旧ゲストオブジェクト削除 + 新アドレスで再招待が必要、OID も変わるため `infra/main.parameters.json` の更新が follow-up で要る）
- [x] **B4** Designated Owner = operator (sole). Teammates = RG-scope Contributor via Bicep (NOT sub-scope, per operator's "only I have admin auth" preference)

**Phase 1 + Phase 2 completed 2026-04-29.** Full deployed-resource manifest, RBAC matrix, and platform-fix postmortem in [STATUS.md](./STATUS.md).

## C. GitHub repo — ✅ MOSTLY DONE 2026-04-29

- [x] **C1** `aiclub-labs/zenn-hack2026` (private). Owner: aiclub-labs org (Google-SSO-backed AI-club Gmail; per project memory). Personal handle `maumao76` is `push` collaborator.
- [x] **C2** All 3 teammate handles (operator + Suzuki-Sotaro + member 3) have `push` collaborator access
- [ ] **C3** Branch protection deliberately skipped — free-tier private repo blocks classic + rulesets API. Social norm + advisory CI substitutes. Revisit post-demo if repo goes public. See [STATUS.md "Recent decisions"](./STATUS.md).
- [ ] **C4** OIDC App Registration + GitHub vars/secrets — deferred. Optional until M5+; current Bicep was deployed by operator's local `az` session, not CI.
- [x] **C5** Scaffold pushed to `main` (58 files, 77 objects, ~59 KiB)

## D. Discord — already designed, execution open

**Scope is settled** (per `discord-bot/docs/server-structure-plan.md` v3): hackathon comms live inside the AI Club server (guild `1478407098521092198`), not a separate server. Existing self-built bot is reused.

The hackathon footprint inside the server:

- Category `🏆 Hackathon: MS Agent 2026` — `@everyone` denied, `Hackathon Team` role allowed
- Channels: `#hack-chat` (text — discussion + weekly standup thread), `#hack-dev-log` (forum, tags: `wip` / `resolved` / `infra` / `agent` / `azure` / `prompt` / `blog`), `#hack-submission` (text — Zenn draft + demo + checklist), `#github-feed` (text — webhook), `#hack-meetings` (text — meeting notes/transcripts), `#hack-voice` (voice — 同期 + デモ練習。当初の `Demo Rehearsal` を兼ねる), `#hack-pm` (text — PM agent 化に向けた project mgmt 用)
- Archive plan: 2026-06-18 後にカテゴリ名を `📦 Archive: MS Agent 2026` にリネーム → 📦 Archive 配下へ移動 → read-only sync

Execution runbook is in `discord-bot/docs/server-setup-execution-guide.md` (~7 phases, iPad-friendly, 2.5–3h split across sessions).

**What's actually open** (verified against live server via `npm run inspect` 2026-05-12):

- [x] **D1 — Hackathon Team role assignment** — 3 メンバー + bot = 4 members 付与済、🏆 カテゴリ閲覧可
- [x] **D2 — `#welcome` pinned text** — Community + Onboarding 有効、welcome 運用中
- [x] **D3 — Community-mode 2-moderator requirement** — Admin 3 名（sotaro / mao / daichi）で要件クリア
- [ ] **D4 — Decide post-hackathon Alumni / public-invite policy** — 残課題（Alumni role = 0 members）
- [x] **D5 — `#github-feed` webhook target repo** — `aiclub-labs/zenn-hack2026` で配線済

Phases that need a real keyboard: Phase 5 (GitHub webhook ↔ Discord URL roundtrip) and Phase 6 (member ID collection). Everything else (0–4, 7) is iPad-doable.

## E. Locally automated already (done while you were at the gym)

See `git log` on this branch — commits prefixed `ai-club:` for hackathon-2026.

- `scaffold/scripts/bootstrap-phase1.sh` — collapses Phase 1's 5 commands into one runnable script (login, sub-select, RP register, objectId resolve, parameters.json patch, what-if preview)
- `scaffold/.github/CODEOWNERS` + PR template + bug/feature issue templates
- `scaffold/tests/fixtures/demo-style-guide.yaml` — synthetic mock style guide for the PPT-Polish demo (per dev-prep §10)
- `scaffold/docs/branch-protection.md` — exact GitHub Settings → Branches checklist + OIDC steps
- `dev-prep.md` / `action-plan.md` — status updated to 2026-04-27

## F. Critical-path watch

→ **See [ROADMAP.md](./ROADMAP.md)** for the canonical milestone list (M0–M15) with dates and owners.

Nothing in section A blocks development. B + C unblock real Azure work — start them when you have a quiet hour at a real keyboard.
