// playwright-signup.ts — drives the Azure free trial signup form.
// Wraps §2.1 of azure-setup.md.
//
// Auto-fills profile fields from .env. Pauses for human at:
//   - SMS verification
//   - Credit card details
//   - MFA QR scan / passkey biometric
//   - any CAPTCHA Microsoft drops in
//
// On success, writes TENANT_ID + SUB_ID to ../../.env.azure (configurable via ENV_OUTPUT_PATH).

import {
  loadEnv,
  launch,
  info,
  ok,
  warn,
  fail,
  pause,
  fillFirst,
  clickFirst,
  findFirstVisible,
  writeEnvOutput,
} from "./_shared";

loadEnv(".env");

const REQUIRED_ENV = [
  "PROFILE_FIRST_NAME",
  "PROFILE_LAST_NAME",
  "PROFILE_EMAIL",
  "PROFILE_PHONE_E164",
];
for (const k of REQUIRED_ENV) {
  if (!process.env[k])
    fail(`missing required env var: ${k}. Edit .env (copy from .env.example).`);
}

(async () => {
  const { context, page } = await launch();

  info("navigating to azure.microsoft.com/free");
  await page.goto("https://azure.microsoft.com/free", {
    waitUntil: "domcontentloaded",
  });

  // Step 1: hit the "Start free" / "Try Azure for free" CTA
  await clickFirst(
    page,
    [
      "role=link[name=/start free/i]",
      "role=link[name=/try azure for free/i]",
      "role=button[name=/start free/i]",
      'a:has-text("Start free")',
      'a:has-text("無料アカウント")',
    ],
    "Start free CTA",
  );

  // Step 2: sign-in flow lands at login.microsoftonline.com or login.live.com
  info("waiting for login form");
  await page.waitForLoadState("domcontentloaded");

  // If a chooser appears ("Use another account" / account tiles), prefer typing fresh
  const chooserVisible = await findFirstVisible(
    page,
    ["role=link[name=/use another account/i]", "text=/use another account/i"],
    2000,
  );
  if (chooserVisible) {
    await page.locator(chooserVisible).first().click();
  }

  // Email field
  const emailFilled = await fillFirst(
    page,
    [
      'input[name="loginfmt"]',
      'input[type="email"]',
      "role=textbox[name=/email|sign in/i]",
    ],
    process.env.AICLUB_MS_ACCOUNT ?? process.env.PROFILE_EMAIL!,
    "MS account email",
  );

  if (emailFilled) {
    await clickFirst(
      page,
      [
        'input[type="submit"]',
        "role=button[name=/next/i]",
        "role=button[name=/sign in/i]",
      ],
      "Next (email)",
    );
  }

  // Password / passkey: human break-point
  await pause(
    page,
    "Complete authentication (password / passkey / MFA challenge). The script will resume after you reach the signup profile form.",
  );

  // Step 3: profile form on signup.azure.com
  info("expecting profile form (signup.azure.com)");
  await page.waitForLoadState("networkidle").catch(() => {
    /* non-fatal */
  });

  // Country / region selector
  await fillFirst(
    page,
    [
      "role=combobox[name=/country|region|国/i]",
      'select[name*="country" i]',
      'input[name*="country" i]',
    ],
    process.env.PROFILE_COUNTRY ?? "Japan",
    "Country/Region",
  );

  await fillFirst(
    page,
    [
      'input[name*="firstName" i]',
      'input[name*="given" i]',
      "role=textbox[name=/first name|名/i]",
    ],
    process.env.PROFILE_FIRST_NAME!,
    "First name",
  );

  await fillFirst(
    page,
    [
      'input[name*="lastName" i]',
      'input[name*="surname" i]',
      'input[name*="family" i]',
      "role=textbox[name=/last name|姓/i]",
    ],
    process.env.PROFILE_LAST_NAME!,
    "Last name",
  );

  if (process.env.PROFILE_FIRST_NAME_FURIGANA) {
    await fillFirst(
      page,
      [
        'input[name*="firstNameFurigana" i]',
        'input[name*="firstNameKana" i]',
        'input[placeholder*="フリガナ"]',
      ],
      process.env.PROFILE_FIRST_NAME_FURIGANA,
      "First name furigana",
    );
  }

  if (process.env.PROFILE_LAST_NAME_FURIGANA) {
    await fillFirst(
      page,
      ['input[name*="lastNameFurigana" i]', 'input[name*="lastNameKana" i]'],
      process.env.PROFILE_LAST_NAME_FURIGANA,
      "Last name furigana",
    );
  }

  await fillFirst(
    page,
    ['input[name*="email" i]', 'input[type="email"]'],
    process.env.PROFILE_EMAIL!,
    "Email",
  );

  await fillFirst(
    page,
    ['input[name*="phone" i]', 'input[type="tel"]'],
    process.env.PROFILE_PHONE_E164!,
    "Phone",
  );

  if (process.env.PROFILE_POSTAL_CODE) {
    await fillFirst(
      page,
      ['input[name*="postal" i]', 'input[name*="zip" i]'],
      process.env.PROFILE_POSTAL_CODE,
      "Postal code",
    );
  }
  if (process.env.PROFILE_PREFECTURE) {
    await fillFirst(
      page,
      ['input[name*="state" i]', 'input[name*="prefecture" i]'],
      process.env.PROFILE_PREFECTURE,
      "Prefecture/State",
    );
  }
  if (process.env.PROFILE_CITY) {
    await fillFirst(
      page,
      ['input[name*="city" i]'],
      process.env.PROFILE_CITY,
      "City",
    );
  }
  if (process.env.PROFILE_ADDRESS_LINE1) {
    await fillFirst(
      page,
      ['input[name*="addressLine1" i]', 'input[name*="address1" i]'],
      process.env.PROFILE_ADDRESS_LINE1,
      "Address line 1",
    );
  }
  if (process.env.PROFILE_ADDRESS_LINE2) {
    await fillFirst(
      page,
      ['input[name*="addressLine2" i]', 'input[name*="address2" i]'],
      process.env.PROFILE_ADDRESS_LINE2,
      "Address line 2",
    );
  }
  if (process.env.PROFILE_COMPANY_OPTIONAL) {
    await fillFirst(
      page,
      ['input[name*="company" i]'],
      process.env.PROFILE_COMPANY_OPTIONAL,
      "Company (optional)",
    );
  }

  ok("profile form prefilled — review and click Next manually");

  // Step 4: human break-point — review profile, click Next, do SMS verification
  await pause(
    page,
    "Review the profile fields (especially address — must match your card billing address). Click Next, then complete the SMS verification step. Resume after you land on the credit-card form.",
  );

  // Step 5: human break-point — credit card details
  await pause(
    page,
    'Enter your credit card details (card #, expiry, CVV, name on card). $1 will be authorized and refunded; nothing will be charged. Click Next to submit. Resume when the form completes and you see the green "$200 credit ready" banner.',
  );

  // Step 6: detect successful signup — wait for portal redirect
  info("waiting for portal redirect (up to 90s)");
  try {
    await page.waitForURL(/portal\.azure\.com/i, { timeout: 90_000 });
    ok("reached portal.azure.com");
  } catch {
    warn(
      "did not auto-redirect to portal — proceeding to capture state from current page",
    );
  }

  // Step 7: try to capture tenant + sub from page state
  // The portal exposes these in window state, but it's flaky to extract pre-auth.
  // Easiest: open a new tab to portal and read from URL / local storage hooks.
  await page
    .goto(
      "https://portal.azure.com/#blade/Microsoft_Azure_Resources/SubscriptionMenuBlade/Subscriptions",
      { waitUntil: "domcontentloaded" },
    )
    .catch(() => {
      /* non-fatal */
    });

  await pause(
    page,
    'Confirm in the portal that you see a subscription named "Azure subscription 1" or "Free Trial". Then return here so the script can finish.',
  );

  // We extract IDs from cookies/local state if available; otherwise tell the user to capture via az cli.
  try {
    const cookies = await context.cookies("https://portal.azure.com");
    const hint = cookies.find((c) => /tenant/i.test(c.name));
    if (hint) info(`cookie hint: ${hint.name}=${hint.value.slice(0, 8)}...`);
  } catch {
    /* ignore */
  }

  // The reliable path: shell out to `az account show` after the user runs `az login`.
  // We cannot run az from here without Bun child_process, but we can prompt.
  console.log("");
  console.log("Final step — open a NEW terminal (WezTerm) and run:");
  console.log("  az login");
  console.log(
    '  az account show --query "{name:name,id:id,tenant:tenantId}" -o table',
  );
  console.log("Copy the values, then come back here.");
  await pause(
    page,
    "After running az login + az account show in a separate terminal, paste TENANT_ID and SUB_ID below.",
  );

  // Capture from stdin
  const promptInput = async (q: string): Promise<string> => {
    process.stdout.write(q);
    return await new Promise<string>((r) => {
      process.stdin.resume();
      process.stdin.once("data", (d) => {
        process.stdin.pause();
        r(d.toString().trim());
      });
    });
  };
  const TENANT_ID = await promptInput("TENANT_ID: ");
  const SUB_ID = await promptInput("SUB_ID:    ");

  if (TENANT_ID && SUB_ID) {
    writeEnvOutput({
      AZURE_TENANT_ID: TENANT_ID,
      AZURE_SUBSCRIPTION_ID: SUB_ID,
      AICLUB_MS_ACCOUNT:
        process.env.AICLUB_MS_ACCOUNT ?? process.env.PROFILE_EMAIL!,
    });
    ok(`signup complete. TENANT_ID=${TENANT_ID} SUB_ID=${SUB_ID}`);
  } else {
    warn("TENANT_ID / SUB_ID not captured — write them down manually");
  }

  await context.close();
  process.exit(0);
})().catch((e) => {
  console.error(e);
  process.exit(1);
});
