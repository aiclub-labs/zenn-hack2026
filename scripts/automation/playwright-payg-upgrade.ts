// playwright-payg-upgrade.ts — drives Free Trial → PAYG conversion at aka.ms/UpgradeNow.
// Wraps §2.6 of azure-setup.md. Run on day 28 (~2026-05-26).
//
// Pauses for human at the final confirmation click and any MFA challenge.
// Verifies the conversion via `az rest` after the form completes.

import {
  loadEnv,
  launch,
  info,
  ok,
  warn,
  fail,
  pause,
  clickFirst,
  findFirstVisible,
} from "./_shared";
import { spawnSync } from "node:child_process";

loadEnv(".env");

let SUB_ID = process.env.AZURE_SUBSCRIPTION_ID;
if (!SUB_ID) {
  const out = spawnSync(
    "az",
    ["account", "show", "--query", "id", "-o", "tsv"],
    { encoding: "utf8" },
  );
  if (out.status === 0) SUB_ID = out.stdout.trim();
}
if (!SUB_ID) {
  fail(
    "AZURE_SUBSCRIPTION_ID not set and `az account show` failed. Run `az login` first.",
  );
}

(async () => {
  const { context, page } = await launch();

  info("navigating to aka.ms/UpgradeNow");
  await page.goto("https://aka.ms/UpgradeNow", {
    waitUntil: "domcontentloaded",
  });

  // Login if needed
  const needsLogin = await findFirstVisible(
    page,
    ['input[name="loginfmt"]', 'input[type="email"]'],
    3000,
  );
  if (needsLogin) {
    await pause(
      page,
      "Sign in with the AI-club account. Resume after you land on the upgrade page.",
    );
  }

  await page.waitForLoadState("networkidle").catch(() => {
    /* non-fatal */
  });

  info('expecting "Upgrade your subscription" page');

  // Pre-flight check: confirm the sub is still on Free Trial (offer ms-azr-0044p) before clicking through
  const offerCheck = spawnSync(
    "az",
    [
      "rest",
      "--method",
      "get",
      "--url",
      `https://management.azure.com/subscriptions/${SUB_ID}?api-version=2020-01-01`,
      "--query",
      "{name:displayName,spendingLimit:subscriptionPolicies.spendingLimit,quotaId:subscriptionPolicies.quotaId}",
      "-o",
      "json",
    ],
    { encoding: "utf8" },
  );
  if (offerCheck.status === 0) {
    const parsed = JSON.parse(offerCheck.stdout || "{}");
    info(
      `current state: name=${parsed.name} spendingLimit=${parsed.spendingLimit} quotaId=${parsed.quotaId}`,
    );
    if (parsed.spendingLimit === "Off") {
      ok(
        "subscription already converted to PAYG (spendingLimit=Off) — no action needed",
      );
      await context.close();
      process.exit(0);
    }
  } else {
    warn("could not pre-check sub state via az — continuing anyway");
  }

  // Drive the upgrade form. The form is fairly stable: one "Upgrade" button per sub row.
  // If multiple subs exist, ask the human to pick the right one.
  const subRowVisible = await findFirstVisible(
    page,
    [
      `text=${SUB_ID}`,
      `text=hack2026`,
      "role=row[name=/free trial|hack2026/i]",
    ],
    8000,
  );
  if (!subRowVisible) {
    warn("could not auto-locate the hack2026 sub row");
  } else {
    info(`found sub row by selector: ${subRowVisible}`);
  }

  // Click the "Upgrade" CTA next to the sub
  const clicked = await clickFirst(
    page,
    [
      `role=button[name=/upgrade/i]`,
      `button:has-text("Upgrade")`,
      `a:has-text("Upgrade")`,
    ],
    "Upgrade",
  );
  if (!clicked) {
    warn("could not auto-click Upgrade — click it yourself, then resume");
  }

  // Plan selection — pick "Pay-As-You-Go" (typically pre-selected for Free Trial conversions)
  await pause(
    page,
    'Confirm "Pay-As-You-Go" is selected as the new offer (the default for Free Trial conversions). Card on file should already be visible. Click Upgrade / Confirm. Resume after you see the success message.',
  );

  // MFA challenge may appear before final commit
  const mfaPrompt = await findFirstVisible(
    page,
    [
      "text=/verify your identity/i",
      "text=/approve sign in/i",
      "role=heading[name=/verify/i]",
    ],
    4000,
  );
  if (mfaPrompt) {
    await pause(
      page,
      "Approve the MFA challenge (Authenticator notification, passkey biometric, or code). Resume after the upgrade success page appears.",
    );
  }

  // Verify via az rest
  info("verifying conversion via Azure Resource Manager");
  await page.waitForTimeout(5_000); // give the back-end a moment

  const verify = spawnSync(
    "az",
    [
      "rest",
      "--method",
      "get",
      "--url",
      `https://management.azure.com/subscriptions/${SUB_ID}?api-version=2020-01-01`,
      "--query",
      "{spendingLimit:subscriptionPolicies.spendingLimit,quotaId:subscriptionPolicies.quotaId,state:state}",
      "-o",
      "json",
    ],
    { encoding: "utf8" },
  );

  if (verify.status === 0) {
    const v = JSON.parse(verify.stdout || "{}");
    info(`post-upgrade state: ${JSON.stringify(v)}`);
    if (v.spendingLimit === "Off") {
      ok("PAYG conversion verified — spendingLimit flipped to Off");
    } else {
      warn(
        `spendingLimit is still "${v.spendingLimit}" — Microsoft back-end may take up to 30 min to propagate. Re-check with: az account show`,
      );
    }
  } else {
    warn(
      "verification call failed — manually run:\n" +
        `  az rest --method get --url "https://management.azure.com/subscriptions/${SUB_ID}?api-version=2020-01-01" --query "subscriptionPolicies.spendingLimit"`,
    );
  }

  await context.close();
  process.exit(0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
