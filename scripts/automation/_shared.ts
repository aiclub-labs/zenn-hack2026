// Shared helpers for the Playwright automation scripts.
// Kept tiny and self-contained — no transitive deps beyond `playwright`.

import {
  chromium,
  type Browser,
  type BrowserContext,
  type Page,
} from "playwright";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  writeFileSync,
  appendFileSync,
} from "node:fs";
import { resolve, dirname } from "node:path";

// ---------- env loading (no `dotenv` dep — keep it simple) ----------
export function loadEnv(envPath = ".env"): Record<string, string> {
  if (!existsSync(envPath)) return {};
  const out: Record<string, string> = {};
  for (const line of readFileSync(envPath, "utf8").split("\n")) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eq = trimmed.indexOf("=");
    if (eq < 0) continue;
    const k = trimmed.slice(0, eq).trim();
    const v = trimmed
      .slice(eq + 1)
      .trim()
      .replace(/^["']|["']$/g, "");
    out[k] = v;
    process.env[k] ??= v;
  }
  return out;
}

// ---------- console helpers ----------
const fg = (c: number) => (s: string) => `\x1b[${c}m${s}\x1b[0m`;
export const cyan = fg(36);
export const green = fg(32);
export const yellow = fg(33);
export const red = fg(31);
export const bold = (s: string) => `\x1b[1m${s}\x1b[0m`;

export function info(msg: string) {
  console.log(cyan(`[info] ${msg}`));
}
export function ok(msg: string) {
  console.log(green(`[ ok ] ${msg}`));
}
export function warn(msg: string) {
  console.log(yellow(`[warn] ${msg}`));
}
export function fail(msg: string): never {
  console.error(red(`[fail] ${msg}`));
  process.exit(1);
}

// ---------- await-keypress pause ----------
export async function pause(
  page: Page,
  message: string,
  opts: { screenshot?: boolean } = {},
): Promise<void> {
  const screenshotOnPause = (process.env.SCREENSHOT_ON_PAUSE ?? "1") === "1";
  if (opts.screenshot ?? screenshotOnPause) {
    try {
      const dir = "screenshots";
      if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
      const ts = new Date().toISOString().replace(/[:.]/g, "-");
      const path = `${dir}/pause-${ts}.png`;
      await page.screenshot({ path, fullPage: false });
      info(`screenshot: ${path}`);
    } catch {
      /* non-fatal */
    }
  }

  console.log(yellow(bold("\n[PAUSE] " + message)));
  console.log(
    yellow(
      "        Press Enter in this terminal when done (or Ctrl+C to abort).",
    ),
  );

  // Read one line from stdin
  await new Promise<void>((resolve) => {
    const onData = () => {
      process.stdin.removeListener("data", onData);
      process.stdin.pause();
      resolve();
    };
    process.stdin.resume();
    process.stdin.once("data", onData);
  });
}

// ---------- browser launch ----------
export async function launch(): Promise<{
  browser: Browser;
  context: BrowserContext;
  page: Page;
}> {
  const headed = (process.env.HEADED ?? "1") === "1";
  const profileDir = resolve(".playwright-profile");

  // Persistent context preserves cookies/session across runs
  const context = await chromium.launchPersistentContext(profileDir, {
    headless: !headed,
    viewport: { width: 1280, height: 800 },
    locale: "ja-JP",
    timezoneId: "Asia/Tokyo",
    args: ["--disable-blink-features=AutomationControlled"],
  });
  const browser = context.browser()!;
  const page = context.pages()[0] ?? (await context.newPage());
  return { browser, context, page };
}

// ---------- write key=value pairs to .env.azure ----------
export function writeEnvOutput(
  values: Record<string, string>,
  outPath?: string,
): void {
  const target = outPath ?? process.env.ENV_OUTPUT_PATH ?? "../../.env.azure";
  const abs = resolve(target);
  if (!existsSync(dirname(abs))) mkdirSync(dirname(abs), { recursive: true });

  // Read existing, merge, write back (preserve other keys)
  const existing: Record<string, string> = {};
  if (existsSync(abs)) {
    for (const line of readFileSync(abs, "utf8").split("\n")) {
      const t = line.trim();
      if (!t || t.startsWith("#")) continue;
      const eq = t.indexOf("=");
      if (eq < 0) continue;
      existing[t.slice(0, eq).trim()] = t.slice(eq + 1).trim();
    }
  }
  const merged = { ...existing, ...values };
  const body =
    Object.entries(merged)
      .map(([k, v]) => `${k}=${v}`)
      .join("\n") + "\n";
  writeFileSync(abs, body, "utf8");
  ok(`wrote ${abs}`);
}

// ---------- robust selector helpers ----------
// Try a list of locator strategies, return the first that resolves to a visible element.
export async function findFirstVisible(
  page: Page,
  candidates: string[],
  timeoutMs = 5000,
): Promise<string | null> {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const sel of candidates) {
      try {
        const loc = page.locator(sel).first();
        if (await loc.isVisible({ timeout: 200 }).catch(() => false))
          return sel;
      } catch {
        /* keep trying */
      }
    }
    await page.waitForTimeout(200);
  }
  return null;
}

export async function fillFirst(
  page: Page,
  candidates: string[],
  value: string,
  label: string,
): Promise<boolean> {
  const sel = await findFirstVisible(page, candidates, 8000);
  if (!sel) {
    warn(
      `could not find field for "${label}" — selectors drifted, may need manual fill`,
    );
    return false;
  }
  await page.locator(sel).first().fill(value);
  ok(`filled ${label}`);
  return true;
}

export async function clickFirst(
  page: Page,
  candidates: string[],
  label: string,
): Promise<boolean> {
  const sel = await findFirstVisible(page, candidates, 8000);
  if (!sel) {
    warn(`could not find button for "${label}"`);
    return false;
  }
  await page.locator(sel).first().click();
  ok(`clicked ${label}`);
  return true;
}
