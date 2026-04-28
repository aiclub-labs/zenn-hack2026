// playwright-mfa-enroll.ts — drives MFA enrollment at myaccount.microsoft.com/security-info.
// Wraps §2.1.5 of azure-setup.md.
//
// Auto-navigates to the tenant-pinned security-info page, opens the "+ Add sign-in method"
// dialog. Pauses for human at each enrollment step (QR scan, biometric, code entry).
// On exit, verifies enrollment via Graph API (called via az rest in a child shell).

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

// Discover tenant via az if not provided
let TENANT_ID = process.env.AZURE_TENANT_ID;
if (!TENANT_ID) {
  const out = spawnSync(
    "az",
    ["account", "show", "--query", "tenantId", "-o", "tsv"],
    { encoding: "utf8" },
  );
  if (out.status === 0) TENANT_ID = out.stdout.trim();
}
if (!TENANT_ID) {
  fail(
    "AZURE_TENANT_ID not set and `az account show` failed. Run `az login` first or set AZURE_TENANT_ID in .env.",
  );
}

(async () => {
  const { context, page } = await launch();

  // Tenant-pinned URL avoids the personal-account home-realm-discovery bounce.
  const securityInfoUrl = `https://mysignins.microsoft.com/security-info?tenantId=${TENANT_ID}`;
  info(`navigating to ${securityInfoUrl}`);
  await page.goto(securityInfoUrl, { waitUntil: "domcontentloaded" });

  // Login: usually the persistent profile already has session cookies. If not, prompt.
  const needsLogin = await findFirstVisible(
    page,
    [
      'input[name="loginfmt"]',
      'input[type="email"]',
      "role=textbox[name=/sign in|email/i]",
    ],
    3000,
  );
  if (needsLogin) {
    await pause(
      page,
      "Sign in with the AI-club account (use passkey or password). Resume after you land on the Security info page.",
    );
  }

  // Wait for the security-info page to fully render
  await page.waitForLoadState("networkidle").catch(() => {
    /* non-fatal */
  });

  // Show what's currently registered
  info("current authentication methods listed on page (read for context)");
  await pause(
    page,
    'Review the methods already registered. If you want to ADD a method, resume and the script will open the "Add sign-in method" dialog. To skip enrollment (e.g., passkey already registered), Ctrl+C now.',
  );

  // Click the "+ Add sign-in method" / "Add method" button
  const clicked = await clickFirst(
    page,
    [
      "role=button[name=/add sign-?in method/i]",
      "role=button[name=/add method/i]",
      'button:has-text("Add sign-in method")',
      'button:has-text("Add method")',
      '[data-bi-id*="addMethod" i]',
    ],
    "Add sign-in method",
  );
  if (!clicked) {
    warn("could not auto-click Add — please click it manually");
    await pause(
      page,
      'Click "+ Add sign-in method" yourself, choose the method (Authenticator recommended), then resume.',
    );
  }

  // Pause for the entire enrollment flow (QR scan / biometric / code entry).
  // Microsoft's wizard varies a lot per method; safest to let the human drive it.
  await pause(
    page,
    "Complete the enrollment wizard end-to-end (pick method, scan QR or follow prompts, verify). Resume after you see the new method appear in the methods list.",
  );

  // (Optional) repeat for a backup method
  console.log("");
  const want2nd = await new Promise<string>((r) => {
    process.stdout.write("Add a backup method now (recommended)? [y/N] ");
    process.stdin.resume();
    process.stdin.once("data", (d) => {
      process.stdin.pause();
      r(d.toString().trim().toLowerCase());
    });
  });
  if (want2nd === "y" || want2nd === "yes") {
    await clickFirst(
      page,
      [
        "role=button[name=/add sign-?in method/i]",
        "role=button[name=/add method/i]",
        'button:has-text("Add sign-in method")',
      ],
      "Add sign-in method (backup)",
    );
    await pause(
      page,
      'Pick "Phone" (or another factor) for the backup method, complete it, then resume.',
    );
  }

  // Set default sign-in method
  info("setting default sign-in method");
  const changedDefault = await clickFirst(
    page,
    [
      "role=button[name=/change|set default/i]",
      'button:has-text("Change")',
      '[aria-label*="default" i]',
    ],
    "Change default sign-in method",
  );
  if (changedDefault) {
    await pause(
      page,
      'Choose "Microsoft Authenticator – notification" (or your preferred default), confirm, then resume.',
    );
  }

  // Verify via Graph
  info("verifying enrollment via Graph API (az rest)");
  const verify = spawnSync(
    "az",
    [
      "rest",
      "--method",
      "get",
      "--url",
      "https://graph.microsoft.com/v1.0/me/authentication/methods",
      "--query",
      "value[].'@odata.type'",
      "-o",
      "tsv",
    ],
    { encoding: "utf8" },
  );

  if (verify.status === 0) {
    const types = verify.stdout.trim().split("\n").filter(Boolean);
    info(`registered method types: ${types.join(", ")}`);
    const hasMfa = types.some((t) =>
      /microsoftAuthenticator|phone|fido2|softwareOath|passwordless/i.test(t),
    );
    if (hasMfa) ok("MFA enrolled — verified via Graph");
    else
      warn(
        "Graph reports no MFA method beyond password — enrollment may not have finalized",
      );
  } else {
    warn(
      "verification call failed — run manually:\n" +
        '  az rest --method get --url "https://graph.microsoft.com/v1.0/me/authentication/methods" --query "value[].\'@odata.type\'" -o tsv',
    );
  }

  await context.close();
  process.exit(0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
