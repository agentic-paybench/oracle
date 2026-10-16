// vendored from agentic-paybench/design-system-private@d7550af (packages/tokens, packages/family, packages/posture) by packages/family/vendor.mjs; do not edit here, re-vendor
// check.mjs: the network-log, layout and axe-core gates of the public page
// family (DES-100, founder-approved 2026-10-16). One script, the same in every
// page repository, vendored from design-system-private packages/family/gates.
//
//   node check.mjs --base http://127.0.0.1:8080 --paths / /capabilities/ ... [--out report.json]
//
// For each path, at 1280 and 390 wide, light and dark: every request the page
// makes is recorded and the gate FAILS on any request whose origin is not the
// page's own; it FAILS on any <script> element; it FAILS when the document is
// wider than the viewport at 390 (the no-sideways-scroll rule); it records the
// font families that loaded. At 1280 light, axe-core runs with the WCAG 2.0 A,
// AA and 2.1 AA tags and the gate FAILS on any violation of any impact. A path
// ending in "?" is optional: a 404 skips it (a gated surface may be absent).
// Exit 1 on any failure; the report names every one.

import { chromium } from "playwright";
import { AxeBuilder } from "@axe-core/playwright";
import { writeFileSync } from "node:fs";

const args = process.argv.slice(2);
const opt = (name, dflt) => {
  const i = args.indexOf(name);
  return i >= 0 && args[i + 1] ? args[i + 1] : dflt;
};
const base = opt("--base", "http://127.0.0.1:8080").replace(/\/$/, "");
const out = opt("--out", "");
const pathsIdx = args.indexOf("--paths");
const paths = [];
if (pathsIdx >= 0) {
  for (const p of args.slice(pathsIdx + 1)) {
    if (p.startsWith("--")) break;
    paths.push(p);
  }
}
if (!paths.length) paths.push("/");
const origin = new URL(base).origin;

const browser = await chromium.launch();
const report = [];
let failures = 0;
const fail = (entry, why) => {
  entry.failures.push(why);
  failures += 1;
};

for (const raw of paths) {
  const optional = raw.endsWith("?");
  const path = optional ? raw.slice(0, -1) : raw;
  const url = base + path;
  for (const width of [1280, 390]) {
    for (const scheme of ["light", "dark"]) {
      const ctx = await browser.newContext({ viewport: { width, height: 900 }, colorScheme: scheme });
      const page = await ctx.newPage();
      const requests = [];
      page.on("request", (r) => requests.push(r.url()));
      const entry = { path, width, scheme, failures: [] };
      const resp = await page.goto(url, { waitUntil: "load" });
      if (!resp || resp.status() >= 400) {
        if (optional && resp && resp.status() === 404) {
          entry.skipped = "optional path absent";
          report.push(entry);
          await ctx.close();
          continue;
        }
        fail(entry, `HTTP ${resp ? resp.status() : "no response"}`);
        report.push(entry);
        await ctx.close();
        continue;
      }
      await page.evaluate(() => document.fonts.ready);
      const m = await page.evaluate(() => ({
        scrollWidth: document.documentElement.scrollWidth,
        clientWidth: document.documentElement.clientWidth,
        scripts: document.querySelectorAll("script").length,
        fonts: [...new Set([...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family))],
      }));
      Object.assign(entry, m);
      const offOrigin = requests.filter((r) => new URL(r).origin !== origin);
      entry.requests = requests.length;
      entry.offOrigin = offOrigin;
      if (offOrigin.length) fail(entry, `off-origin request(s): ${offOrigin.slice(0, 3).join(", ")}`);
      if (m.scripts > 0) fail(entry, `${m.scripts} script element(s)`);
      if (m.scrollWidth > m.clientWidth) fail(entry, `document ${m.scrollWidth}px wide in a ${m.clientWidth}px viewport`);
      if (width === 1280 && scheme === "light") {
        const axe = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze();
        entry.axeViolations = axe.violations.map((v) => ({ id: v.id, impact: v.impact, nodes: v.nodes.length, help: v.help }));
        entry.axePasses = axe.passes.length;
        if (axe.violations.length) fail(entry, `axe: ${axe.violations.map((v) => `${v.id} (${v.impact}, ${v.nodes.length})`).join("; ")}`);
      }
      report.push(entry);
      await ctx.close();
    }
  }
}
await browser.close();

for (const e of report) {
  const tag = e.skipped ? "SKIP" : e.failures.length ? "FAIL" : "OK  ";
  const detail = e.skipped ? e.skipped : `scroll=${e.scrollWidth}/${e.clientWidth} requests=${e.requests} offOrigin=${(e.offOrigin || []).length} scripts=${e.scripts} fonts=${(e.fonts || []).join("|")}` + (e.axeViolations ? ` axe=${e.axeViolations.length} violation(s), ${e.axePasses} rules passed` : "");
  console.log(`${tag} ${String(e.width).padStart(4)} ${e.scheme.padEnd(5)} ${e.path}  ${detail}`);
  for (const f of e.failures) console.log(`      ${f}`);
}
if (out) writeFileSync(out, JSON.stringify(report, null, 2));
console.log(failures ? `family-gates: ${failures} failure(s)` : "family-gates: all checks passed");
process.exit(failures ? 1 : 0);
